# MiniProject — Retail Sales EDA

This workspace contains a small retail sales dataset (`retail_sales_dataset.csv`) and scripts for exploratory data analysis.

Files of interest:
- `analysis_clean.py` — lightweight defensive analyzer that prints a small product-level summary.
- `eda_clean.py` — a more complete EDA script: canonicalizes sales values, aggregates monthly sales, computes MoM, customer and product summaries, and saves plots under `plots/`.

Optional features
- Forecasting (simple Holt-Winters) and an interactive Streamlit dashboard are implemented in a guarded way in the EDA code — they require extra packages.

Install dependencies (PowerShell):

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Run the scripts (PowerShell):

```powershell
# Quick check (sample)
python analysis_clean.py --sample 100

# Full EDA (writes images to ./plots)
python eda_clean.py
```

If you want me to replace the corrupted `analysis.py` and `eda.py` files with the cleaned versions, say "Yes, overwrite originals" and I'll do that and re-run validations.
