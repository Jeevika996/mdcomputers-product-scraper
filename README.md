# MDComputers Product Scraper

A Python web scraper that extracts product details from [MDComputers.in](https://www.mdcomputers.in)
search results using BeautifulSoup. Supports keyword-based search, structured
data extraction, and includes a live Streamlit web demo.

MDComputers runs on **OpenCart**, and search results are served at:
https://www.mdcomputers.in/?route=product/search&search=<keyword>
## 🔗 Live Demo

Try it here: ## 🔗 Live Demo

Try it here: **[https://mdcomputers-scraper.streamlit.app/](https://mdcomputers-scraper.streamlit.app/)**

## Features

- Keyword search with pagination (walks multiple result pages automatically)
- Structured extraction per product: name, URL, current price, old/MRP price,
  discount %, image URL, stock status, rating, SKU/model
- Deduplicates products across pages
- Resilient parsing: each field is extracted via an ordered list of
  candidate CSS selectors, with a generic link-based fallback if the
  site's theme changes and none of the known selectors match
- Handles storefronts that render each product as **two separate links**
  (image + title) sharing the same URL — a common OpenCart theme pattern
  that naive scrapers get wrong
- Polite by default: rate-limited requests, retry with exponential backoff
  on transient errors (429/500/502/503/504)
- Simple Streamlit web interface for live browser-based searching

## Install

```bash
git clone https://github.com/Jeevika996/mdcomputers-product-scraper.git
cd mdcomputers-product-scraper
pip install -r requirements.txt
```

## Run the web app

```bash
pip install streamlit pandas
streamlit run app.py
```
Then open `http://localhost:8501` in your browser.

## Use as a Python library

```python
from mdcomputers_scraper import MDComputersScraper

with MDComputersScraper(request_delay=1.5) as scraper:
    products = scraper.search(keyword="rtx 4060", max_pages=3)

for p in products:
    print(p.name, p.price)
```

Each result is a `Product` dataclass with fields:
## Project layout
mdcomputers_scraper/
config.py # base URL, headers, timeouts, retry/rate-limit policy
models.py # Product dataclass
http_client.py # requests.Session wrapper: retries + throttling
parser.py # BeautifulSoup extraction (selector fallback chains)
scraper.py # orchestrates search + pagination + dedup
app.py # Streamlit web interface
## Notes on responsible use

- Requests are rate-limited by default.
- This project only reads publicly accessible search result pages; it does
  not log in, bypass access controls, or hit non-public endpoints.
- Built for educational/portfolio purposes. Not affiliated with MDComputers.in.
Step 3: Save (Ctrl+S), then push it to GitHub:
git add README.md
git commit -m "Add README"
git push
