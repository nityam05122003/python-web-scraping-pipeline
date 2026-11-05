# Scraper module

"""
Scraper logic: fetch HTML pages and return raw content.
Replace with actual implementation.
"""

import requests

def fetch(url: str) -> str:
    response = requests.get(url)
    response.raise_for_status()
    return response.text
