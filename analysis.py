"""Small retail sales analysis script (clean copy).

Safe, minimal diagnostics for retail_sales_dataset.csv.
"""

from __future__ import annotations

import argparse
import os
from typing import Optional

import pandas as pd


def load_data(path: str, nrows: Optional[int] = None) -> pd.DataFrame:
    if not os.path.isfile(path):
        raise FileNotFoundError(f"Data file not found: {path}")
    try:
        return pd.read_csv(path, nrows=nrows)
    except pd.errors.EmptyDataError as exc:
        raise ValueError(f"CSV file is empty: {path}") from exc
    except Exception as exc:
        raise ValueError(f"Failed to read CSV file {path}: {exc}") from exc


def summarize_sales(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    possible_qty = [c for c in ("quantity", "Quantity", "qty") if c in df.columns]
    possible_price = [c for c in ("price", "Price", "unit_price") if c in df.columns]
    product_cols = [c for c in ("product", "Product", "item", "Product Category") if c in df.columns]
    possible_total = [c for c in ("total", "Total", "total_amount", "Total Amount") if c in df.columns]

    if not product_cols or (not possible_qty and not possible_total):
        return pd.DataFrame()

    product_col = product_cols[0]

    if possible_total:
        total_col = possible_total[0]
        df_local = df[[product_col, total_col]].copy()
        df_local[total_col] = pd.to_numeric(df_local[total_col], errors="coerce").fillna(0)
        return df_local.groupby(product_col)[total_col].sum().reset_index().rename(columns={total_col: "sales_value"})

    qty_col = possible_qty[0]
    price_col = possible_price[0] if possible_price else None
    cols = [product_col, qty_col] + ([price_col] if price_col else [])
    df_local = df[cols].copy()
    df_local[qty_col] = pd.to_numeric(df_local[qty_col], errors="coerce").fillna(0)

    if price_col:
        df_local[price_col] = pd.to_numeric(df_local[price_col], errors="coerce").fillna(0)
        df_local["sales_value"] = df_local[qty_col] * df_local[price_col]
        return df_local.groupby(product_col)["sales_value"].sum().reset_index()

    return df_local.groupby(product_col)[qty_col].sum().reset_index().rename(columns={qty_col: "quantity"})


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a minimal retail sales analysis")
    parser.add_argument("--data", "-d", default="retail_sales_dataset.csv", help="Path to CSV data file")
    parser.add_argument("--sample", "-s", type=int, default=None, help="Read only the first N rows for quick testing")
    args = parser.parse_args()

    try:
        df = load_data(args.data, nrows=args.sample)
    except Exception as exc:
        print(f"Error loading data: {exc}")
        return 2

    summary = summarize_sales(df)
    if summary.empty:
        print("No summary could be produced (missing expected columns or empty data)")
        print("\nDiagnostics:")
        print(f"- rows: {len(df)}; columns: {len(df.columns)}")
        if len(df.columns) > 0:
            print(f"- column names: {', '.join(df.columns.tolist()[:20])}")
        try:
            print("\nSample rows:")
            print(df.head(5).to_string(index=False))
        except Exception:
            pass
        return 0

    print("Summary: (top 10)")
    print(summary.head(10).to_string(index=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())