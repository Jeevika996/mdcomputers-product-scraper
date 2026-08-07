from __future__ import annotations

BASE_URL = "https://www.mdcomputers.in"
SEARCH_ROUTE = "product/search"

DEFAULT_SEARCH_PARAMS = {
    "route": SEARCH_ROUTE,
    "description": "0",
    "limit": "100",
}

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Connection": "keep-alive",
}

REQUEST_TIMEOUT = 15
MAX_RETRIES = 3
BACKOFF_FACTOR = 1.5
RETRY_STATUS_CODES = (429, 500, 502, 503, 504)
DEFAULT_REQUEST_DELAY = 1.5
MAX_PAGES_HARD_LIMIT = 50