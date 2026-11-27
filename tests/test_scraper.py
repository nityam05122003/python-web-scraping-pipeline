import requests
from src.scraper import BookScraper

SAMPLE_HTML = """
<html>
  <body>
    <article class="product_pod">
      <p class="star-rating Three"></p>
      <h3><a href="catalogue/a-light-in-the-attic_1000/index.html" title="A Light in the Attic">A Light in the Attic</a></h3>
      <div class="product_price">
        <p class="price_color">£51.77</p>
        <p class="instock availability">In stock</p>
      </div>
    </article>
    <article class="product_pod">
      <p class="star-rating Two"></p>
      <div class="product_price">
        <p class="price_color">£19.99</p>
        <p class="instock availability">In stock</p>
      </div>
    </article>
  </body>
</html>
"""


def test_scrape_parses_valid_and_skips_malformed(mocker):
    scraper = BookScraper()
    mocker.patch.object(scraper, "fetch_page", return_value=SAMPLE_HTML)

    books = list(scraper.scrape(max_pages=1))

    assert len(books) == 1
    book = books[0]
    assert book["title"] == "A Light in the Attic"
    assert book["detail_url"] == "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html"
    assert book["price_raw"] == "£51.77"
    assert book["stock_raw"] == "In stock"
    assert book["rating_raw"] == "Three"


def test_fetch_page_handles_request_exception(mocker):
    scraper = BookScraper()
    mocker.patch.object(
        scraper.session,
        "get",
        side_effect=requests.RequestException("Connection timed out"),
    )

    result = scraper.fetch_page("https://books.toscrape.com/")
    assert result is None
