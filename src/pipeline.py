# src/pipeline.py
"""
Pipeline entry point for the web-scraping project.

This script ties together the three core components:
1. :class:`src.scraper.BookScraper` – extracts raw book data from
   ``https://books.toscrape.com/``.
2. :class:`src.processor.DataProcessor` – normalises the raw dictionaries
   into a clean :class:`pandas.DataFrame`.
3. :class:`src.db.DatabaseManager` – persists the processed records into a
   database (SQLite by default, PostgreSQL if ``DATABASE_URL`` is provided).

Running the module directly will perform a single scrape (by default up to
two pages) and upsert the results.  The ``--max-pages`` argument can be used to
control the pagination depth.
"""

import argparse
import logging
import os
import sys

from src.scraper import BookScraper
from src.processor import DataProcessor
from src.db import DatabaseManager


def configure_logging(log_dir: str = "logs", log_file: str = "pipeline.log") -> logging.Logger:
    """Configure root logging to output to both stdout and a log file."""
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_path, encoding="utf-8"),
        ],
        force=True,
    )
    return logging.getLogger(__name__)


logger = configure_logging()


def run_pipeline(max_pages: int = 2) -> None:
    """Execute the end-to-end scraping -> processing -> storage flow.

    Parameters
    ----------
    max_pages: int, optional
        Maximum number of pagination pages to traverse. Defaults to ``2``.
    """
    logger.info("Starting scraping with max_pages=%s", max_pages)
    raw_records = list(BookScraper().scrape(max_pages=max_pages))
    logger.info("Scraped %d raw book records", len(raw_records))

    logger.info("Processing raw records into a DataFrame")
    df = DataProcessor().process(raw_records)
    logger.info("Processed DataFrame with %d rows", len(df))

    db_manager = DatabaseManager()
    db_manager.init_db()
    upserted = db_manager.upsert_books(df)
    logger.info("Upserted %d records into the database", upserted)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the book-scraping pipeline.")
    parser.add_argument(
        "--max-pages",
        type=int,
        default=2,
        help="Maximum number of pagination pages to scrape (default: 2)",
    )
    args = parser.parse_args()

    try:
        run_pipeline(max_pages=args.max_pages)
        logger.info("Pipeline status: SUCCESS")
        sys.exit(0)
    except Exception as exc:
        logger.exception("Pipeline status: FAILURE - %s", exc)
        sys.exit(1)
