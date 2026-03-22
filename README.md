# AI-Powered NL Query Layer for Marketing Analytics

**Author:** Rishikesh Rachamalla
**Stack:** Databricks · Delta Lake · PySpark · Claude API · Streamlit

---

## What This Is

An end-to-end pipeline that takes raw retail transaction data (UCI Online Retail II, 525K rows) through a medallion architecture on Databricks, then exposes the Gold layer through a natural-language query interface powered by Claude API.

**Ask in plain English → get SQL → get results + chart.**

---

## Project Structure

```
nl-query-marketing-data/
├── data/sample/                  # Small sample CSVs for reference (git-tracked)
├── notebooks/
│   ├── 01_bronze_ingestion.py    # Databricks verification queries
│   ├── 02_silver_transformation.py
│   ├── 03_gold_aggregation.py
│   └── 04_data_quality_checks.py
├── enrichment/
│   ├── enrich_retail_data.py     # Phase 1 enrichment script
│   └── output/                   # Generated CSVs (gitignored)
├── streamlit_app/
│   └── app.py                    # Phase 5 NL query app
├── docs/
│   ├── data_dictionary.md        # All column definitions
│   └── architecture.md           # System design
└── .gitignore
```

---

## Phases

| Phase | Description | Status |
|-------|-------------|--------|
| 1 | Data ingestion — enrich UCI dataset, upload to Databricks | ✅ Complete |
| 2 | Silver layer — clean, join, RFM scores | 🔜 |
| 3 | Gold layer — customer_360, daily_kpis, segments | 🔜 |
| 4 | Serving layer — Databricks SQL Warehouse | 🔜 |
| 5 | AI query layer — Claude API + Streamlit app | 🔜 |

---

## Phase 1 Quick Start

```bash
# 1. Install dependencies
pip install pandas faker openpyxl

# 2. Download UCI Online Retail II from Kaggle and place in enrichment/
#    https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci

# 3. Run enrichment script
cd enrichment/
python enrich_retail_data.py

# 4. Upload output CSVs to Databricks via UI:
#    enrichment/output/bronze_raw_transactions.csv  → default.bronze_raw_transactions
#    enrichment/output/silver_enriched_customers.csv → default.silver_enriched_customers
```

---

## Gold Tables (Phase 3)

| Table | Description |
|-------|-------------|
| `customer_360` | Full customer profile with RFM + loyalty attributes |
| `daily_kpis` | Revenue, volume, active customers per day |
| `segment_summary` | Metrics by loyalty tier and signup channel |
| `campaign_metrics` | Campaign response rates and revenue impact |

---

## NL Query Examples (Phase 5)

- *"Show me top 10 segments by revenue this quarter"*
- *"Which signup channel has the highest churn risk?"*
- *"Compare email opt-in rate across loyalty tiers"*
- *"What's the average order value for Platinum customers?"*
