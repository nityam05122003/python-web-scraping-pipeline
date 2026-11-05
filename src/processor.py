# Processor module

"""
Data processing and normalization for scraped book data.
Transforms raw dictionaries from BookScraper into a clean pandas DataFrame.
"""

import logging
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Any

import pandas as pd

# Module‑level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DataProcessor:
    """Normalize raw book data into a tidy pandas DataFrame.

    Steps performed:
    * Clean and convert ``price_raw`` → ``price`` (float).
    * Clean ``stock_raw`` → ``stock_status`` (text) and ``is_in_stock`` (bool).
    * Map ``rating_raw`` (text) → ``rating`` (int 0‑5).
    * Add ``scraped_at`` (UTC timestamp).
    * Create deterministic ``book_id`` using SHA‑256 of ``title`` + ``detail_url``.
    * Drop duplicate records based on ``book_id``.
    * Validate critical columns (``book_id``, ``title``, ``price``).
    """

    RATING_MAP = {
        "One": 1,
        "Two": 2,
        "Three": 3,
        "Four": 4,
        "Five": 5,
    }

    def __init__(self):
        pass

    @staticmethod
    def _clean_price(price_raw: str) -> float:
        """Strip everything except digits and a decimal point, then convert to float.
        Returns 0.0 on failure.
        """
        try:
            import re
            cleaned = re.sub(r"[^\d.]", "", price_raw)
            return float(cleaned) if cleaned else 0.0
        except Exception as exc:
            logger.warning("Failed to parse price %s: %s", price_raw, exc)
            return 0.0

    @staticmethod
    def _parse_stock(stock_raw: str) -> (str, bool):
        status = stock_raw.strip()
        is_stock = "in stock" in status.lower()
        return status, is_stock

    @staticmethod
    def _map_rating(rating_raw: str) -> int:
        return DataProcessor.RATING_MAP.get(rating_raw, 0)

    @staticmethod
    def _generate_book_id(title: str, detail_url: str) -> str:
        source = f"{title}{detail_url}".encode("utf-8")
        return hashlib.sha256(source).hexdigest()

    def process(self, raw_data: List[Dict[str, Any]]) -> pd.DataFrame:
        if not raw_data:
            logger.info("No raw data supplied to DataProcessor.process")
            return pd.DataFrame()
        df = pd.DataFrame(raw_data)
        df["price"] = df["price_raw"].apply(self._clean_price)
        df[["stock_status", "is_in_stock"]] = df["stock_raw"].apply(
            lambda x: pd.Series(self._parse_stock(x))
        )
        df["rating"] = df["rating_raw"].apply(self._map_rating)
        df["scraped_at"] = datetime.now(timezone.utc)
        df["book_id"] = df.apply(
            lambda row: self._generate_book_id(row.get("title", ""), row.get("detail_url", "")),
            axis=1,
        )
        df = df.drop_duplicates(subset=["book_id"]).reset_index(drop=True)
        required = ["book_id", "title", "price"]
        for col in required:
            if df[col].isnull().any() or (df[col] == "").any():
                raise ValueError(f"Critical column '{col}' contains null or empty values after processing")
        column_order = [
            "book_id",
            "title",
            "detail_url",
            "price",
            "stock_status",
            "is_in_stock",
            "rating",
            "scraped_at",
        ]
        extra = [c for c in df.columns if c not in column_order]
        df = df[column_order + extra]
        return df
