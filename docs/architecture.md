# Architecture — AI-Powered NL Query Layer for Marketing Analytics

## Overview

End-to-end pipeline from raw retail transactions to a natural language query interface powered by Claude API.

## Phases

### Phase 1: Data Ingestion
- **Source:** UCI Online Retail II (525K rows, CSV/XLSX)
- **Enrichment:** Python + Faker — 26 synthetic loyalty/marketing fields
- **Storage:** Databricks DBFS → Delta Lake tables

### Phase 2: Medallion Architecture (PySpark + Delta Lake)
| Layer | Table | Description |
|-------|-------|-------------|
| Bronze | `bronze_raw_transactions` | Raw transactions, schema-on-read |
| Silver | `silver_enriched_customers` | Dedupe, enrich, join; RFM + loyalty fields |
| Gold | `customer_360`, `daily_kpis`, `segment_summary`, `campaign_metrics` | Business-ready aggregations |

### Phase 3: Gold Tables (Delta Lake)
- `customer_360` — full customer profile
- `daily_kpis` — revenue, volume, active customers per day
- `segment_summary` — metrics by loyalty tier / channel
- `campaign_metrics` — campaign response and ROI

### Phase 4: Serving Layer
- Databricks SQL Warehouse (Serverless, Free Edition)
- Exposes Gold tables via SQL connector

### Phase 5: AI Query Layer (local Streamlit app)
```
User NL question
      ↓  (prompt + schema)
  Claude API  →  generates SQL
      ↓
  Databricks SQL Warehouse  →  executes query
      ↓
  Results + chart displayed in Streamlit
```

## Tech Stack
| Component | Technology |
|-----------|-----------|
| Data storage | Databricks Delta Lake (Free Edition) |
| Transformation | PySpark |
| Enrichment | Python, Faker, pandas |
| AI layer | Claude API (Anthropic) |
| App framework | Streamlit |
| SQL connector | `databricks-sql-connector` |
| Version control | GitHub |
