# DB module

"""
Database connection handling and ORM definitions for the scraped books.
Uses SQLAlchemy 2.0 Declarative style and supports upserts on both PostgreSQL and SQLite.
"""

import os
import logging
from datetime import datetime, timezone
from typing import List

import pandas as pd
from sqlalchemy import create_engine, select, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, Session, sessionmaker
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from dotenv import load_dotenv

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Load .env variables if present
load_dotenv()


class Base(DeclarativeBase):
    pass


class Book(Base):
    """SQLAlchemy model representing a scraped book record."""

    __tablename__ = "books"

    # Primary key – deterministic SHA‑256 hash (64 hex chars)
    book_id: Mapped[str] = mapped_column(String(64), primary_key=True, nullable=False)
    title: Mapped[str] = mapped_column(nullable=False)
    detail_url: Mapped[str] = mapped_column(nullable=False)
    price: Mapped[float] = mapped_column(nullable=False)
    stock_status: Mapped[str] = mapped_column(nullable=False)
    is_in_stock: Mapped[bool] = mapped_column(nullable=False)
    rating: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        nullable=False, default=lambda: datetime.now(timezone.utc)
    )
    updated_at: Mapped[datetime] = mapped_column(
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DatabaseManager:
    """High‑level helper for DB interactions.

    - Reads DATABASE_URL from the environment (via ``python‑dotenv``).
    - Falls back to a local SQLite file under ``data/books.db``.
    - Provides ``init_db`` to create tables and ``upsert_books`` for bulk upserts.
    """

    def __init__(self, database_url: str | None = None):
        # Resolve database URL
        self.database_url = (
            database_url
            or os.getenv("DATABASE_URL")
            or "sqlite:///data/books.db"
        )
        logger.info("Connecting to database: %s", self.database_url)
        self.engine = create_engine(self.database_url, future=True, echo=False)
        self.SessionLocal = sessionmaker(bind=self.engine, class_=Session, future=True)

    def init_db(self) -> None:
        """Create tables if they do not exist."""
        Base.metadata.create_all(self.engine)
        logger.info("Database tables ensured.")

    def upsert_books(self, df: pd.DataFrame) -> int:
        """Bulk upsert a DataFrame of book records.

        Returns the total number of rows inserted or updated.
        """
        if df.empty:
            logger.info("Empty DataFrame supplied to upsert_books – nothing to do.")
            return 0

        # Ensure only columns that exist in the Book model are used for upsert
        required_cols = ["book_id", "title", "detail_url", "price", "stock_status", "is_in_stock", "rating"]
        # Filter the DataFrame to these columns (ignore missing ones gracefully)
        df_filtered = df[required_cols]

        # Convert filtered DataFrame to list of dicts matching the Book model columns
        records: List[dict] = df_filtered.to_dict(orient="records")

        # Choose dialect‑specific insert statement
        dialect = self.engine.dialect.name
        if dialect == "postgresql":
            stmt = pg_insert(Book).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Book.book_id],
                set_={
                    "title": stmt.excluded.title,
                    "detail_url": stmt.excluded.detail_url,
                    "price": stmt.excluded.price,
                    "stock_status": stmt.excluded.stock_status,
                    "is_in_stock": stmt.excluded.is_in_stock,
                    "rating": stmt.excluded.rating,
                    "updated_at": datetime.now(timezone.utc),
                },
            )
        else:  # SQLite (or any other) – uses the same syntax
            stmt = sqlite_insert(Book).values(records)
            stmt = stmt.on_conflict_do_update(
                index_elements=[Book.book_id],
                set_={
                    "title": stmt.excluded.title,
                    "detail_url": stmt.excluded.detail_url,
                    "price": stmt.excluded.price,
                    "stock_status": stmt.excluded.stock_status,
                    "is_in_stock": stmt.excluded.is_in_stock,
                    "rating": stmt.excluded.rating,
                    "updated_at": datetime.now(timezone.utc),
                },
            )

        with self.SessionLocal() as session:
            result = session.execute(stmt)
            session.commit()
            # ``rowcount`` reflects total rows affected for most dialects
            affected = result.rowcount if hasattr(result, "rowcount") else len(records)
            logger.info("Upserted %d book records (dialect=%s).", affected, dialect)
            return affected
