import pytest
from src.processor import DataProcessor

@pytest.mark.parametrize("price_raw,expected", [
    ("£51.77", 51.77),
    ("Â£10.50", 10.5),
    ("invalid", 0.0),
])
def test_clean_price(price_raw, expected):
    assert DataProcessor._clean_price(price_raw) == pytest.approx(expected)

@pytest.mark.parametrize("rating_raw,expected", [
    ("One", 1),
    ("Two", 2),
    ("Five", 5),
    ("Zero", 0),
    ("", 0),
])
def test_rating_mapping(rating_raw, expected):
    assert DataProcessor._map_rating(rating_raw) == expected

def test_book_id_deterministic():
    title = "Some Book"
    url = "http://example.com/book/1"
    id1 = DataProcessor._generate_book_id(title, url)
    id2 = DataProcessor._generate_book_id(title, url)
    assert id1 == id2
    assert len(id1) == 64

def test_duplicate_dropping():
    raw = [
        {
            "title": "Book A",
            "detail_url": "http://example.com/a",
            "price_raw": "£10.00",
            "stock_raw": "In stock",
            "rating_raw": "Three",
        },
        {
            "title": "Book A",
            "detail_url": "http://example.com/a",
            "price_raw": "£10.00",
            "stock_raw": "In stock",
            "rating_raw": "Three",
        },
    ]
    df = DataProcessor().process(raw)
    assert len(df) == 1
    assert "book_id" in df.columns
