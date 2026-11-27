import pytest
import pandas as pd
from sqlalchemy import text
from src.processor import DataProcessor
from src.db import DatabaseManager

@pytest.fixture(scope="function")
def db_manager():
    # In‑memory SQLite DB for isolated testing
    manager = DatabaseManager(database_url="sqlite:///:memory:")
    manager.init_db()
    return manager

def _make_df():
    raw = [
        {
            "title": "Book A",
            "detail_url": "http://example.com/a",
            "price_raw": "£10.00",
            "stock_raw": "In stock",
            "rating_raw": "Three",
        },
        {
            "title": "Book B",
            "detail_url": "http://example.com/b",
            "price_raw": "£20.50",
            "stock_raw": "Out of stock",
            "rating_raw": "Four",
        },
    ]
    return DataProcessor().process(raw)

def test_table_initialization(db_manager):
    # Table should exist without errors after init_db()
    # Attempt a simple query
    with db_manager.SessionLocal() as session:
        result = session.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name='books';"))
        tables = result.fetchall()
        assert tables, "Table 'books' was not created"

def test_idempotent_upsert(db_manager):
    df_initial = _make_df()
    count1 = db_manager.upsert_books(df_initial)
    assert count1 == 2, "First upsert should affect two rows"

    # Modify price for one record (same book_id)
    df_modified = df_initial.copy()
    df_modified.loc[df_modified["title"] == "Book A", "price"] = 99.99
    count2 = db_manager.upsert_books(df_modified)
    # Upsert should still report 2 rows (update counts as affected)
    assert count2 == 2, "Second upsert should affect two rows (updates)"

    # Verify that the price was updated in the DB
    with db_manager.SessionLocal() as session:
        result = session.execute(text("SELECT price FROM books WHERE title='Book A';"))
        price = result.scalar_one()
        assert price == pytest.approx(99.99)
