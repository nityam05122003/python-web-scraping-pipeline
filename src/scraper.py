# Scraper module

"""
Web scraper for Books to Scrape (https://books.toscrape.com/).
Provides a BookScraper class that yields raw book data.
"""

import logging
from typing import Iterator, Dict, Any, Optional
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

# Module‑level logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BookScraper:
    """
    Scrapes book information from https://books.toscrape.com/.

    The scraper yields dictionaries with the following raw fields:
        - title:        book title
        - detail_url:   absolute URL to the book detail page
        - price_raw:    price string (e.g. "£51.77")
        - stock_raw:    raw stock/availability text
        - rating_raw:   rating class name (e.g. "Three")
    """

    BASE_URL = "https://books.toscrape.com/"

    def __init__(self, timeout: int = 10):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0.0.0 Safari/537.36"
            )
        })
        self.timeout = timeout

    def fetch_page(self, url: str) -> Optional[str]:
        """Download a page and return its HTML text, or None on request failure."""
        try:
            response = self.session.get(url, timeout=self.timeout)
            response.raise_for_status()
            return response.text
        except requests.RequestException as exc:
            logger.error("Failed to fetch %s: %s", url, exc)
            return None

    def _get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Download a page and parse it with BeautifulSoup."""
        html = self.fetch_page(url)
        if html is None:
            return None
        return BeautifulSoup(html, "html.parser")

    def _parse_book_card(self, card) -> Dict[str, Any]:
        """Extract raw fields from a single product card."""
        try:
            title = card.h3.a["title"].strip()
            rel_url = card.h3.a["href"]
            detail_url = urljoin(self.BASE_URL, rel_url)
            price_raw = card.select_one("p.price_color").get_text(strip=True)
            stock_raw = card.select_one("p.instock.availability").get_text(strip=True)
            rating_tag = card.select_one("p.star-rating")
            rating_raw = rating_tag["class"][1] if rating_tag and len(rating_tag["class"]) > 1 else ""
            return {
                "title": title,
                "detail_url": detail_url,
                "price_raw": price_raw,
                "stock_raw": stock_raw,
                "rating_raw": rating_raw,
            }
        except Exception as exc:
            logger.warning("Failed to parse a book card: %s", exc)
            return {}

    def scrape(self, max_pages: int = 2) -> Iterator[Dict[str, Any]]:
        """Iterate over raw book dictionaries across pages.

        Parameters
        ----------
        max_pages : int, optional
            Upper limit of pages visited (default = 2).
        """
        page_url = self.BASE_URL
        for page_num in range(1, max_pages + 1):
            logger.info("Scraping page %d: %s", page_num, page_url)
            html = self.fetch_page(page_url)
            if not html:
                logger.warning("Stopping pagination: failed to fetch %s", page_url)
                break
            soup = BeautifulSoup(html, "html.parser")
            for card in soup.select("article.product_pod"):
                data = self._parse_book_card(card)
                if data:
                    yield data
            next_el = soup.select_one("li.next a")
            if not next_el:
                break
            page_url = urljoin(page_url, next_el["href"])
