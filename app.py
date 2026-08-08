
import streamlit as st
import pandas as pd

from mdcomputers_scraper import MDComputersScraper

st.set_page_config(
    page_title="MDComputers Product Scraper",
    page_icon="🖥️",
    layout="wide",
)
st.markdown(
    """
    <link rel="manifest" href="./app/static/manifest.json">
    <meta name="theme-color" content="#1F2937">
    <link rel="apple-touch-icon" href="./app/static/icon-192.png">
    <script>
      if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('./app/static/service-worker.js')
          .catch(function(err) { console.log('SW registration failed:', err); });
      }
    </script>
    """,
    unsafe_allow_html=True,
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
            st.download_button(
                "⬇️ Download results as CSV",
                data=csv_data,
                file_name=f"{keyword.replace(' ', '_')}_results.csv",
                mime="text/csv",
            )

st.divider()
st.caption(
    "Built with Python, BeautifulSoup, and Streamlit. "
    "Not affiliated with MDComputers.in — for educational/portfolio use."
)
