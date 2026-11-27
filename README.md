# Python Web Scraping ETL Pipeline

[![Web Scraping Data Pipeline](https://github.com/nityam05122003/python-web-scraping-pipeline/actions/workflows/pipeline.yml/badge.svg)](https://github.com/nityam05122003/python-web-scraping-pipeline/actions/workflows/pipeline.yml)

Automated end-to-end ETL pipeline scraping book catalog data, normalizing records with Pandas, performing idempotent SQLAlchemy 2.0 upserts into PostgreSQL (Neon) or SQLite, and running every 6 hours via GitHub Actions.

## Stack & Architecture

- **Extract (`src/scraper.py`):** Paginated HTML scraping (`requests` + `BeautifulSoup4`) with URL normalization.
- **Transform (`src/processor.py`):** Pandas price cleaning, star-rating mapping (`1-5`), stock count extraction, and deduplication on `product_url`.
- **Load (`src/db.py`):** Dialect-aware `ON CONFLICT (product_url) DO UPDATE` upserts for PostgreSQL and SQLite.
- **Orchestrate (`src/pipeline.py` & `.github/workflows/pipeline.yml`):** Dual console/file logging (`logs/pipeline.log`), exit codes (`0`/`1`), `pytest` gate, and 6-hour cron schedule (`0 */6 * * *`).

## Quickstart

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -v
python -m src.pipeline --max-pages 3
```

## Docker

```bash
docker build -t web-scraping-pipeline .
docker run --rm --env-file .env web-scraping-pipeline --max-pages 3
```
