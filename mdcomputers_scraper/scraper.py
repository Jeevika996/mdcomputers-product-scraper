
from __future__ import annotations

import logging
from typing import Optional

from . import config
from .http_client import HttpClient
from .models import Product
from .parser import has_next_page, parse_search_page

logger = logging.getLogger(__name__)


class MDComputersScraper:
    def __init__(
        self,
        base_url: str = config.BASE_URL,
        request_delay: float = config.DEFAULT_REQUEST_DELAY,
        timeout: int = config.REQUEST_TIMEOUT,
        max_retries: int = config.MAX_RETRIES,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = HttpClient(
            timeout=timeout, max_retries=max_retries, request_delay=request_delay
        )

    def search(
        self,
        keyword: str,
        max_pages: int = 5,
        match_description: bool = False,
        category_id: Optional[int] = None,
    ) -> list[Product]:
        """
        Search MDComputers for `keyword` and return every product found,
        walking up to `max_pages` of results (deduplicated by product URL).
        """
        if not keyword or not keyword.strip():
            raise ValueError("keyword must be a non-empty string")

        max_pages = max(1, min(max_pages, config.MAX_PAGES_HARD_LIMIT))

        all_products: list[Product] = []
        seen_urls: set[str] = set()

        for page in range(1, max_pages + 1):
            params = dict(config.DEFAULT_SEARCH_PARAMS)
            params["search"] = keyword
            params["description"] = "1" if match_description else "0"
            params["page"] = str(page)
            if category_id is not None:
                params["category_id"] = str(category_id)

            logger.info("Fetching page %d for keyword=%r", page, keyword)
            response = self.client.get(self.base_url + "/", params=params)

            page_products = parse_search_page(
                html=response.text,
                base_url=self.base_url,
                search_keyword=keyword,
                page_number=page,
                source_url=response.url,
            )

            if not page_products:
                logger.info("No products found on page %d, stopping.", page)
                break

            new_count = 0
            for product in page_products:
                if product.url not in seen_urls:
                    seen_urls.add(product.url)
                    all_products.append(product)
                    new_count += 1

            logger.info(
                "Page %d: %d products found (%d new, %d duplicates)",
                page,
                len(page_products),
                new_count,
                len(page_products) - new_count,
            )

            if new_count == 0:
                # Same results as before (likely stuck on last page) -> stop.
                break

            if not has_next_page(response.text, current_page=page):
                logger.info("No further pages detected after page %d.", page)
                break

        return all_products

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "MDComputersScraper":
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()