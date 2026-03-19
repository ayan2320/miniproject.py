"""Small Streamlit dashboard for the retail sales EDA.

Usage:
  streamlit run app.py

The app will try to load `retail_sales_dataset.csv` from the project root.
If `streamlit` (or other packages) aren't installed, run the commands in README.md to install them.
"""

from pathlib import Path
from typing import Optional

import pandas as pd

try:
    import streamlit as st
except Exception:  # pragma: no cover - runtime dependency
    st = None


def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]

    # simple canonical sales value detection
    cols = {c.lower(): c for c in df.columns}
    def find(*cands):
        for c in cands:
            if c in cols:
                return cols[c]
        return None

    qty_col = find("quantity", "qty")
    price_col = find("price", "unit price", "price per unit", "price_per_unit")
    total_col = find("total", "total amount", "amount", "sales_value")
    date_col = find("date", "transaction date", "order date")
    product_col = find("product", "product category", "item")
    customer_col = find("customer", "customer id", "customer_id")
    category_col = find("category", "product category")

    if total_col and total_col in df.columns:
        df["sales_value"] = pd.to_numeric(df[total_col], errors="coerce").fillna(0)
    elif qty_col and price_col and qty_col in df.columns and price_col in df.columns:
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
        df[price_col] = pd.to_numeric(df[price_col], errors="coerce").fillna(0)
        df["sales_value"] = df[qty_col] * df[price_col]
    elif qty_col and qty_col in df.columns:
        df[qty_col] = pd.to_numeric(df[qty_col], errors="coerce").fillna(0)
        df["sales_value"] = df[qty_col]
    else:
        df["sales_value"] = 0

    if date_col and date_col in df.columns:
        df["date_parsed"] = pd.to_datetime(df[date_col], errors="coerce")
        df["month"] = df["date_parsed"].dt.to_period("M").dt.to_timestamp()
    else:
        df["date_parsed"] = pd.NaT
        df["month"] = pd.NaT

    df.attrs.update({
        "product_col": product_col,
        "customer_col": customer_col,
        "category_col": category_col,
    })

    return df


def build_app(df: pd.DataFrame) -> None:
    st.title("Retail Sales — Quick Dashboard")

    # Sidebar filters
    st.sidebar.subheader("Filters")
    prod_col = df.attrs.get("product_col")
    cat_col = df.attrs.get("category_col")
    cust_col = df.attrs.get("customer_col")

    selected_products = None
    selected_categories = None

    if prod_col and prod_col in df.columns:
        products = sorted([p for p in df[prod_col].dropna().unique()])
        selected_products = st.sidebar.multiselect("Products", products, default=products if len(products) <= 10 else products[:10])

    if cat_col and cat_col in df.columns:
        categories = sorted([c for c in df[cat_col].dropna().unique()])
        selected_categories = st.sidebar.multiselect("Categories", categories, default=categories if len(categories) <= 10 else categories[:10])

    has_dates = df["date_parsed"].notna().any()
    start_date = end_date = None
    if has_dates:
        min_dt = df["date_parsed"].min().date()
        max_dt = df["date_parsed"].max().date()
        # date_input returns a single date or a tuple (start,end)
        dr = st.sidebar.date_input("Date range", value=(min_dt, max_dt), min_value=min_dt, max_value=max_dt)
        if isinstance(dr, (list, tuple)) and len(dr) == 2:
            start_date, end_date = dr
        else:
            start_date = dr
            end_date = dr

    # Apply filters to create a filtered dataframe used for charts and metrics
    df_filtered = df
    if selected_products:
        df_filtered = df_filtered[df_filtered[prod_col].isin(selected_products)]
    if selected_categories:
        df_filtered = df_filtered[df_filtered[cat_col].isin(selected_categories)]
    if has_dates and start_date is not None and end_date is not None:
        start_ts = pd.to_datetime(start_date)
        # include entire end day
        end_ts = pd.to_datetime(end_date) + pd.Timedelta(days=1) - pd.Timedelta(seconds=1)
        df_filtered = df_filtered[(df_filtered["date_parsed"] >= start_ts) & (df_filtered["date_parsed"] <= end_ts)]

    # top-level metrics (based on filtered data)
    total_sales = float(df_filtered["sales_value"].sum())
    n_orders = int(len(df_filtered))
    if cust_col and cust_col in df_filtered.columns:
        total_customers = df_filtered[cust_col].nunique()
    else:
        total_customers = None

    col1, col2, col3 = st.columns(3)
    col1.metric("Total sales", f"{total_sales:,.2f}")
    col2.metric("Orders", f"{n_orders}")
    col3.metric("Customers", f"{total_customers if total_customers is not None else 'N/A'}")

    # monthly series
    if "month" in df_filtered.columns:
        monthly = df_filtered.groupby("month")["sales_value"].sum().sort_index()
        st.subheader("Monthly sales")
        st.line_chart(monthly)

        st.subheader("Recent month-over-month growth")
        mom = monthly.pct_change().dropna()
        if not mom.empty:
            st.line_chart(mom.fillna(0))
        else:
            st.write("Not enough monthly data to compute MoM.")

    # top products (based on filtered data)
    if prod_col and prod_col in df_filtered.columns:
        st.subheader("Top products")
        top = df_filtered.groupby(prod_col).agg(total_sales=("sales_value", "sum"), orders=("sales_value", "count"))
        top = top.sort_values("total_sales", ascending=False).head(20)
        st.dataframe(top)

    # category breakdown (if available)
    if cat_col and cat_col in df_filtered.columns:
        st.subheader("Sales by category")
        bycat = df_filtered.groupby(cat_col)["sales_value"].sum().sort_values(ascending=False)
        st.bar_chart(bycat)

    # customer-level metrics (based on filtered data)
    if cust_col and cust_col in df_filtered.columns:
        st.subheader("Customer summary")
        bycust = df_filtered.groupby(cust_col).agg(orders=("sales_value", "count"), total=("sales_value", "sum"))
        bycust["aov"] = bycust["total"] / bycust["orders"].replace(0, pd.NA)
        st.write(f"Total customers: {len(bycust)}")
        st.dataframe(bycust.sort_values("total", ascending=False).head(50))

    # show static plot images if they exist
    plots_dir = Path("plots")
    if plots_dir.exists():
        st.subheader("Saved plots")
        for p in sorted(plots_dir.iterdir()):
            if p.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                st.image(str(p), caption=p.name)


def main():
    if st is None:
        print("streamlit is not installed. Install it with: python -m pip install streamlit")
        return

    data_path = Path("retail_sales_dataset.csv")
    if not data_path.exists():
        st.error(f"Data file not found: {data_path}. Place `retail_sales_dataset.csv` in the project root.")
        return

    df = load_data(data_path)

    st.sidebar.title("Controls")
    st.sidebar.write("Dataset rows:", len(df))

    build_app(df)


if __name__ == "__main__":
    # Allow running `python app.py` as a lightweight check
    if st is None:
        print("streamlit not installed — run `streamlit run app.py` after installing requirements.")
    else:
        main()
