"""EDA script (clean copy).

Loads CSV, computes canonical sales_value, aggregates monthly sales,
computes MoM growth, basic customer/product summaries, saves plots to ./plots.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Tuple

import matplotlib.pyplot as plt
import pandas as pd

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except Exception:
    ExponentialSmoothing = None


def load_and_prepare(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    df.columns = [c.strip() for c in df.columns]
    col_map = {c.lower(): c for c in df.columns}

    def find(*cands):
        for c in cands:
            if c in col_map:
                return col_map[c]
        return None

    product_col = find("product category", "product", "item")
    qty_col = find("quantity", "qty")
    price_col = find("price per unit", "price", "unit_price")
    total_col = find("total amount", "total", "amount")
    customer_col = find("customer id", "customer", "customer_id")
    cost_col = find("cost", "cost per unit", "unit_cost")
    date_col = find("date", "transaction date", "order date", "date")

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

    df.attrs.update({
        "product_col": product_col,
        "qty_col": qty_col,
        "price_col": price_col,
        "date_col": date_col,
        "customer_col": customer_col,
        "cost_col": cost_col,
    })

    return df


def ensure_plots_dir() -> Path:
    p = Path("plots")
    p.mkdir(exist_ok=True)
    return p


def clean_monthly_series(df: pd.DataFrame, min_days_in_month: int = 8) -> pd.Series:
    if "month" not in df.columns:
        return pd.Series(dtype=float)
    monthly = df.groupby("month")["sales_value"].sum().sort_index()
    counts = df.groupby("month")["date_parsed"].nunique()
    if counts.empty:
        return monthly
    median_count = counts.median()
    keep = counts >= max(min_days_in_month, 0.5 * median_count)
    return monthly[keep]


def compute_mom(series: pd.Series) -> pd.DataFrame:
    if series.empty:
        return pd.DataFrame()
    out = series.rename("sales").reset_index()
    out["mom"] = out["sales"].pct_change().fillna(0)
    return out


def plot_monthly(series: pd.Series, out_dir: Path) -> Optional[Path]:
    if series.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 4))
    series.plot(ax=ax, marker="o")
    ax.set_ylabel("Sales Value")
    ax.set_title("Monthly Sales")
    out = out_dir / "monthly_sales.png"
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    return out


def plot_quantity_hist(df: pd.DataFrame, out_dir: Path) -> Optional[Path]:
    qty = df.attrs.get("qty_col")
    if not qty or qty not in df.columns:
        return None
    fig, ax = plt.subplots(figsize=(6, 4))
    df[qty].dropna().astype(float).plot(kind="hist", bins=30, ax=ax)
    ax.set_title("Quantity Distribution")
    out = out_dir / "quantity_hist.png"
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    return out


def forecast_and_plot(series: pd.Series, out_dir: Path, periods: int = 3) -> Optional[Path]:
    if series.empty:
        return None
    fig, ax = plt.subplots(figsize=(10, 5))
    series.plot(ax=ax, marker="o", label="Observed")
    series.rolling(3, min_periods=1).mean().plot(ax=ax, linestyle="--", label="3-mo rolling")
    if ExponentialSmoothing is not None and len(series) >= 6:
        try:
            model = ExponentialSmoothing(series, trend="add", seasonal=None)
            fit = model.fit(optimized=True)
            fcast = fit.forecast(periods)
            ax.plot(fcast.index, fcast.values, marker="x", label="Forecast")
        except Exception:
            pass
    ax.set_ylabel("Sales Value")
    ax.set_title("Monthly Sales with Forecast")
    ax.legend()
    out = out_dir / "monthly_sales_forecast.png"
    fig.tight_layout(); fig.savefig(out); plt.close(fig)
    return out


def customer_metrics(df: pd.DataFrame) -> pd.DataFrame:
    cust = df.attrs.get("customer_col")
    if not cust or cust not in df.columns:
        return pd.DataFrame()
    by = df.groupby(cust).agg(orders=("sales_value", "count"), total=("sales_value", "sum"))
    by["aov"] = by["total"] / by["orders"].replace(0, pd.NA)
    return by.sort_values("total", ascending=False)


def top_products(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    prod = df.attrs.get("product_col")
    if not prod or prod not in df.columns:
        return pd.DataFrame()
    grp = df.groupby(prod).agg(total_sales=("sales_value", "sum"))
    return grp.sort_values("total_sales", ascending=False).head(n).reset_index()


def run_eda(path: str) -> Tuple[pd.DataFrame, List[Path]]:
    df = load_and_prepare(path)
    out = ensure_plots_dir()
    generated: List[Path] = []

    monthly_raw = df.groupby("month")["sales_value"].sum().sort_index() if "month" in df.columns else pd.Series(dtype=float)
    monthly = clean_monthly_series(df)
    mom = compute_mom(monthly)

    p = plot_monthly(monthly if not monthly.empty else monthly_raw, out)
    if p:
        generated.append(p)
    p = plot_quantity_hist(df, out)
    if p:
        generated.append(p)
    p = forecast_and_plot(monthly, out, periods=3)
    if p:
        generated.append(p)

    cust = customer_metrics(df)
    prod = top_products(df, n=20)

    print("Dataset shape:", df.shape)
    print("Columns:", list(df.columns))
    total_sales = df["sales_value"].sum()
    print("Total sales:", total_sales)

    if not prod.empty:
        print("Top products:")
        print(prod.to_string(index=False))

    if not cust.empty:
        total_customers = len(cust)
        repeat_rate = (cust["orders"] > 1).sum() / max(total_customers, 1)
        overall_aov = total_sales / max(df.shape[0], 1)
        print(f"Customers: {total_customers}, Repeat rate: {repeat_rate:.1%}, AOV: {overall_aov:.2f}")

    if not mom.empty:
        print("Month-over-month (recent):")
        print(mom.tail(6).to_string(index=False))

    insights: List[str] = []
    if total_sales > 0 and not prod.empty:
        top_share = prod.iloc[0]["total_sales"] / total_sales
        insights.append(f"Top product contributes approx {top_share:.1%} of total sales.")
    if not monthly.empty and len(monthly) >= 2:
        trend = (monthly.iloc[-1] - monthly.iloc[0]) / max(monthly.iloc[0], 1)
        insights.append(f"Sales trend from first to last cleaned month: {trend:.1%} change.")

    print("\nBusiness insights:")
    for s in insights:
        print("-", s)

    return df, generated


if __name__ == "__main__":
    data_path = "retail_sales_dataset.csv"
    df, plots = run_eda(data_path)
    if plots:
        print("Saved plots:")
        for p in plots:
            print("-", p)
