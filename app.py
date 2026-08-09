
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd

from mdcomputers_scraper import MDComputersScraper

st.set_page_config(
    page_title="MDComputers Product Scraper",
    page_icon="🖥️",
    layout="wide",
)
components.html(
    """
    <script>
      (function () {
        const head = window.parent.document.head;

        const manifestLink = document.createElement('link');
        manifestLink.rel = 'manifest';
        manifestLink.href = './app/static/manifest.json';
        head.appendChild(manifestLink);

        const themeMeta = document.createElement('meta');
        themeMeta.name = 'theme-color';
        themeMeta.content = '#1F2937';
        head.appendChild(themeMeta);

        const appleIcon = document.createElement('link');
        appleIcon.rel = 'apple-touch-icon';
        appleIcon.href = './app/static/icon-192.png';
        head.appendChild(appleIcon);

        const appleCapable = document.createElement('meta');
        appleCapable.name = 'apple-mobile-web-app-capable';
        appleCapable.content = 'yes';
        head.appendChild(appleCapable);

        const appleTitle = document.createElement('meta');
        appleTitle.name = 'apple-mobile-web-app-title';
        appleTitle.content = 'MD Scraper';
        head.appendChild(appleTitle);

        if ('serviceWorker' in navigator) {
          navigator.serviceWorker
            .register('./app/static/service-worker.js')
            .catch(function (err) {
              console.log('SW registration failed:', err);
            });
        }
      })();
    </script>
    """,
    height=0,
)

st.title("🖥️ MDComputers Product Scraper")
st.caption(
    "Search live product listings from MDComputers.in — pulls real name, "
    "price, discount, and stock data directly from the site."
)

with st.form("search_form"):
    col1, col2 = st.columns([3, 1])
    with col1:
        keyword = st.text_input(
            "Search keyword", placeholder="e.g. rtx 4060, ryzen 5, keyboard"
        )
    with col2:
        max_pages = st.number_input(
            "Pages to search", min_value=1, max_value=10, value=2
        )
    submitted = st.form_submit_button("Search", type="primary", width="stretch")

if submitted:
    if not keyword.strip():
        st.warning("Please enter a search keyword.")
    else:
        with st.spinner(f"Searching MDComputers for '{keyword}'..."):
            try:
                with MDComputersScraper(request_delay=1.0) as scraper:
                    products = scraper.search(keyword=keyword, max_pages=int(max_pages))
            except Exception as exc:
                st.error(f"Something went wrong while scraping: {exc}")
                products = []

        if not products:
            st.info(f"No products found for '{keyword}'. Try a shorter or different keyword.")
        else:
            st.success(f"Found {len(products)} product(s) for '{keyword}'.")

            rows = [
                {
                    "Name": p.name,
                    "Price (₹)": p.price,
                    "Old Price (₹)": p.old_price,
                    "Discount": f"{p.discount_percent}%" if p.discount_percent else "",
                    "Availability": p.availability or "",
                    "URL": p.url,
                }
                for p in products
            ]
            df = pd.DataFrame(rows)

            st.dataframe(
                df,
                width="stretch",
                hide_index=True,
                column_config={
                    "URL": st.column_config.LinkColumn("Product Link"),
                    "Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                    "Old Price (₹)": st.column_config.NumberColumn(format="₹%.2f"),
                },
            )

            csv_data = df.to_csv(index=False).encode("utf-8")
