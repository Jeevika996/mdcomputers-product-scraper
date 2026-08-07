
from __future__ import annotations

import logging
import re
from typing import Iterable, Optional

from bs4 import BeautifulSoup, Tag

from .models import Product

logger = logging.getLogger(__name__)

_PRODUCT_URL_RE = re.compile(r"/product/[^/?#]+", re.IGNORECASE)
_NUMBER_RE = re.compile(r"[\d,]+(?:\.\d+)?")
_DISCOUNT_RE = re.compile(r"-?\s*(\d+(?:\.\d+)?)\s*%")

_PRODUCT_CONTAINER_SELECTORS = [
    "div.product-layout",
    "div.product-thumb",
    "div.product-grid .product-item",
    "li.product-item",
    "div.product-item",
]

_NAME_LINK_SELECTORS = [
    "h4 a",
    "h3 a",
    ".caption a",
    ".product-name a",
    "a.product-title",
]

_PRICE_CONTAINER_SELECTORS = [
    ".price",
    ".product-price",
    ".price-box",
]

_IMAGE_SELECTORS = ["img"]

_AVAILABILITY_SELECTORS = [
    ".stock",
    ".availability",
    ".product-stock",
]

_RATING_SELECTORS = [
    ".rating",
    ".product-rating",
]


def _first_match(tag: Tag, selectors: Iterable[str]) -> Optional[Tag]:
    for sel in selectors:
        found = tag.select_one(sel)
        if found is not None:
            return found
    return None


def _clean_text(tag: Optional[Tag]) -> Optional[str]:
    if tag is None:
        return None
    text = tag.get_text(" ", strip=True)
    return text or None


def _parse_price_value(text: str) -> Optional[float]:
    match = _NUMBER_RE.search(text)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def _parse_prices(container: Optional[Tag], fallback_scope: Tag):
    scope = container or fallback_scope

    old_price = None
    new_price = None

    old_tag = scope.select_one(".price-old, .old-price, del, s, strike")
    new_tag = scope.select_one(".price-new, .new-price, .special-price, ins")

    if new_tag is not None:
        new_price = _parse_price_value(new_tag.get_text(" ", strip=True))
    if old_tag is not None:
        old_price = _parse_price_value(old_tag.get_text(" ", strip=True))

    if new_price is None and old_price is None:
        text = _clean_text(scope) or ""
        amounts = [
            _parse_price_value(m) for m in re.findall(r"₹\s*[\d,]+(?:\.\d+)?", text)
        ]
        amounts = [a for a in amounts if a is not None]
        if len(amounts) == 1:
            new_price = amounts[0]
        elif len(amounts) >= 2:
            old_price, new_price = max(amounts), min(amounts)

    discount_percent = None
    discount_tag = scope.select_one(".discount, .special-tag, .product-badge, .badge")
    search_root = scope if discount_tag is None else discount_tag
    dmatch = _DISCOUNT_RE.search(search_root.get_text(" ", strip=True))
    if dmatch:
        discount_percent = float(dmatch.group(1))
    elif old_price and new_price and old_price > 0:
        discount_percent = round((1 - (new_price / old_price)) * 100, 2)

    return new_price, old_price, discount_percent


def _extract_image_url(container: Tag) -> Optional[str]:
    img = _first_match(container, _IMAGE_SELECTORS)
    if img is None:
        return None
    for attr in ("data-src", "data-original", "src"):
        val = img.get(attr)
        if val:
            return val
    return None


def _extract_name_and_url(container: Tag, base_url: str):
    link = _first_match(container, _NAME_LINK_SELECTORS)
    if link is None:
        candidates = container.find_all("a", href=_PRODUCT_URL_RE)
        best_link, best_text = None, ""
        for candidate in candidates:
            text = _clean_text(candidate) or ""
            if len(text) > len(best_text):
                best_link, best_text = candidate, text
        link = best_link or (candidates[0] if candidates else None)
    if link is None:
        return None

    name = _clean_text(link) or link.get("title")
    href = link.get("href")
    if not name or not href:
        return None

    if href.startswith("//"):
        href = "https:" + href
    elif href.startswith("/"):
        href = base_url.rstrip("/") + href

    return name, href


def _extract_sku(container: Tag) -> Optional[str]:
    return _clean_text(container.select_one(".model, .sku, .product-model"))


def parse_search_page(
    html: str,
    base_url: str,
    search_keyword: str,
    page_number: int,
    source_url: str,
) -> list[Product]:
    soup = BeautifulSoup(html, "lxml")

    containers = []
    for sel in _PRODUCT_CONTAINER_SELECTORS:
        containers = soup.select(sel)
        if containers:
            logger.debug("Matched %d product containers with selector %r", len(containers), sel)
            break

    if not containers:
        containers = _generic_container_fallback(soup)
        if containers:
            logger.debug(
                "Used generic /product/ link fallback, found %d containers", len(containers)
            )

    products: list[Product] = []
    seen_urls: set[str] = set()

    for container in containers:
        name_url = _extract_name_and_url(container, base_url)
        if name_url is None:
            continue
        name, url = name_url
        if url in seen_urls:
            continue
        seen_urls.add(url)

        price_container = _first_match(container, _PRICE_CONTAINER_SELECTORS)
        price, old_price, discount = _parse_prices(price_container, container)

        product = Product(
            name=name,
            url=url,
            price=price,
            old_price=old_price,
            discount_percent=discount,
            image_url=_extract_image_url(container),
            availability=_clean_text(_first_match(container, _AVAILABILITY_SELECTORS)),
            rating=_extract_rating(container),
            sku_or_model=_extract_sku(container),
            search_keyword=search_keyword,
            page_number=page_number,
            source_url=source_url,
        )
        products.append(product)

    return products


def _extract_rating(container: Tag) -> Optional[float]:
    rating_tag = _first_match(container, _RATING_SELECTORS)
    if rating_tag is None:
        return None
    style = rating_tag.get("style", "")
    width_match = re.search(r"width\s*:\s*(\d+(?:\.\d+)?)\s*%", style)
    if width_match:
        return round(float(width_match.group(1)) / 100 * 5, 2)
    text = rating_tag.get_text(" ", strip=True)
    frac_match = re.search(r"(\d+(?:\.\d+)?)\s*/\s*5", text)
    if frac_match:
        return float(frac_match.group(1))
    return None


def _lowest_common_ancestor(tags):
    chains = []
    for t in tags:
        chain = []
        node = t
        while node is not None:
            chain.append(node)
            node = node.parent
        chains.append(list(reversed(chain)))

    lca = None
    for level_nodes in zip(*chains):
        first = level_nodes[0]
        if all(n is first for n in level_nodes):
            lca = first
        else:
            break
    return lca


def _generic_container_fallback(soup: BeautifulSoup) -> list:
    product_links = soup.find_all("a", href=_PRODUCT_URL_RE)

    groups = {}
    for link in product_links:
        href = link.get("href")
        if not href:
            continue
        key = href.split("?")[0].rstrip("/")
        groups.setdefault(key, []).append(link)

    containers = []
    seen_ids = set()

    for key, links in groups.items():
        if len(links) == 1:
            node = links[0]
            for _ in range(4):
                if node.parent is None:
                    break
                node = node.parent
            candidate = node
        else:
            candidate = _lowest_common_ancestor(links)
            if candidate is not None:
                distinct_hrefs = {
                    a.get("href", "").split("?")[0].rstrip("/")
                    for a in candidate.find_all("a", href=_PRODUCT_URL_RE)
                }
                if len(distinct_hrefs) > 1:
                    node = links[0]
                    for _ in range(4):
                        if node.parent is None:
                            break
                        node = node.parent
                    candidate = node

        if candidate is not None and id(candidate) not in seen_ids:
            seen_ids.add(id(candidate))
            containers.append(candidate)

    return containers


def has_next_page(html: str, current_page: int) -> bool:
    soup = BeautifulSoup(html, "lxml")

    pagination = soup.select_one("ul.pagination, div.pagination, nav.pagination")
    if pagination is not None:
        for link in pagination.find_all("a", href=True):
            text = link.get_text(strip=True).lower()
            if text in ("»", "next", ">"):
                return True
            if text.isdigit() and int(text) > current_page:
                return True

    results_text = soup.find(string=re.compile(r"Showing\s+\d+\s+to\s+\d+\s+of\s+\d+", re.I))
    if results_text:
        match = re.search(r"\((\d+)\s+Pages?\)", results_text, re.I)
        if match:
            total_pages = int(match.group(1))
            return current_page < total_pages

    return False


# --- Example usage (not required — just to show the parser actually working) ---
if __name__ == "__main__":
    example_html = """
    <html><body>
    <div class="product-layout">
      <div class="product-thumb">
        <div class="image">
          <a href="/product/msi-rtx-5060-ventus-2x-oc-graphics-card-g5060-8v2c">
            <img src="https://mdcomputers.in/image/catalog/gpu1.webp" alt="MSI RTX 5060">
          </a>
        </div>
        <div class="caption">
          <h4><a href="/product/msi-rtx-5060-ventus-2x-oc-graphics-card-g5060-8v2c">MSI RTX 5060 Ventus 2X OC 8GB GDDR7 Graphics Card</a></h4>
          <p class="price">
            <span class="price-old">₹60,999</span>
            <span class="price-new">₹46,999</span>
          </p>
          <span class="stock">In Stock</span>
          <span class="model">G5060-8V2C</span>
        </div>
      </div>
    </div>
    </body></html>
    """

    results = parse_search_page(
        html=example_html,
        base_url="https://www.mdcomputers.in",
        search_keyword="rtx 5060",
        page_number=1,
        source_url="https://www.mdcomputers.in/?route=product/search&search=rtx+5060",
    )

    for product in results:
        print(f"Name: {product.name}")
        print(f"Price: ₹{product.price}")
        print(f"Old Price: ₹{product.old_price}")
        print(f"Discount: {product.discount_percent}%")
        print(f"Availability: {product.availability}")
        print(f"URL: {product.url}")