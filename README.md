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
python analysis.py --sample 100

# Full EDA (writes images to ./plots)
python eda.py
```
project topic: Data exploration and visualization
Title: Explore Customer Purchase Behavior for Marketing Decisions
A marketing team wants insights into customer buying patterns.
Key Tasks:
• Load dataset using pandas.
• Perform exploratory data analysis.
• Visualize trends using charts.
• Identify high-value customers.
• Interpret insights for business.
Data Source:
https://www.kaggle.com/datasets/mohammadtalib786/retail-sales-dataset
to run app.py type in terminal: streamlit run app.py
