# Data Play — AI-Powered NL Query Layer for Marketing Analytics

**Author:** Rishikesh Rachamalla
**Stack:** Databricks · Delta Lake · PySpark · Claude API · Streamlit · Python

---

## What This Is

An end-to-end data pipeline and AI application that takes raw retail transaction data (UCI Online Retail II, 525K rows) through a Medallion architecture on Databricks, then exposes the Gold layer through a **natural-language query interface** powered by the Claude API.

**Ask in plain English → Claude generates SQL → Databricks runs it → Results + AI Insight.**

---

## Live Demo

> Ask: *"Platinum customers with high churn risk"*
> Ask: *"Which signup channel drives the most revenue?"*
> Ask: *"Compare avg basket size across loyalty tiers"*

---

## Project Structure

```
nl-query-marketing-data/
├── enrichment/
│   ├── enrich_retail_data.py        # Phase 1: UCI dataset enrichment script
│   └── output/                      # Generated CSVs (gitignored)
│
├── notebooks/
│   ├── 01_bronze_ingestion.py       # Databricks: Bronze table verification
│   ├── 02_silver_transformation.py  # Databricks: Silver layer queries
│   ├── 03_gold_aggregation.py       # Databricks: Gold layer aggregations
│   └── 04_data_quality_checks.py   # Databricks: DQ checks
│
├── streamlit_app/
│   ├── app.py                       # Main UI — page layout, rendering, query flow
│   └── utils/
│       ├── config.py                # Constants, schema definitions, format maps
│       ├── llm.py                   # Claude API — SQL generation + AI insights
│       ├── database.py              # Databricks SQL Warehouse query execution
│       ├── guardrails.py            # Input validation, SQL safety, cooldown
│       └── helpers.py              # Formatting, history, UI components
│
├── docs/
│   ├── architecture.md              # System design — 5-phase architecture
│   └── data_dictionary.md          # All column definitions
│
├── requirements.txt
├── .gitignore
└── README.md
```

---

## Architecture — 5 Phases

```
Phase 1: Data Ingestion
  UCI Online Retail II (525K rows CSV)
  → Databricks DBFS (raw file storage)
  → Python + Faker (enrich loyalty fields)

Phase 2: Medallion Architecture (PySpark + Delta Lake)
  Bronze → Silver → Gold
  Raw transactions → Deduped + enriched → Aggregated tables

Phase 3: Gold Tables (Delta Lake)
  customer_360 · daily_kpis · segment_summary · campaign_metrics

Phase 4: Serving Layer
  Databricks SQL Warehouse (Serverless)

Phase 5: AI Query Layer (Streamlit App)
  User NL question → Claude API (Schema + NL → SQL)
  → Databricks SQL → Results + Chart + AI Insight
```

---

## Gold Tables

| Table | Rows | Description |
|---|---|---|
| `customer_360` | ~4,372 | Full customer profile — RFM, loyalty tier, demographics, churn risk |
| `daily_kpis` | ~750 | Daily revenue, transactions, active customers |
| `segment_summary` | 4 | Aggregated metrics by loyalty tier |
| `campaign_metrics` | ~6 | Performance by signup channel |

**Dataset range:** December 2009 – December 2011

---

## Streamlit App Features

### Core
- Natural language → SQL via Claude API (schema-aware prompting)
- Databricks SQL Warehouse execution
- Results table with formatted columns (currency, %, integers)
- Auto-fit bar/line charts
- CSV download

### AI Layer
- **AI Insight** — Claude generates a 2-3 sentence analyst-style business insight from every result
- **Follow-up questions** — 3 smart follow-up questions generated per query, clickable to re-run

### Guardrails (6 layers)
| # | Guardrail | What it prevents |
|---|---|---|
| 1 | Query cooldown (3s) | Warehouse overload |
| 2 | Input validation | Too short, too long, gibberish |
| 3 | Prompt injection detection | AI manipulation attempts |
| 4 | Out-of-scope detection | Weather, sports, unrelated questions |
| 5 | Destructive SQL blocking | DROP, DELETE, ALTER, TRUNCATE |
| 6 | SELECT * guard + LIMIT enforcement | Full table scans on 500K+ row tables |

### UX
- Dark animated gradient UI
- Schema explorer sidebar with column type badges
- Query history (last 10 queries)
- Compact hero when query is active
- `.env` validation on startup with clear error messaging

---

## Quick Start

### 1. Clone & install

```bash
git clone https://github.com/RishikeshRachamalla/nl-query-marketing-data.git
cd nl-query-marketing-data

python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Set up environment variables

```bash
cp .env.example .env
```

Edit `.env`:
```
ANTHROPIC_API_KEY=your_claude_api_key
DATABRICKS_HOST=your-workspace.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse_id
DATABRICKS_TOKEN=your_databricks_token
```

### 3. Phase 1 — Data ingestion

```bash
# Download UCI Online Retail II from Kaggle:
# https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci
# Place the file in enrichment/

cd enrichment/
python enrich_retail_data.py

# Upload output CSVs to Databricks via UI:
# enrichment/output/bronze_raw_transactions.csv   → default.bronze_raw_transactions
# enrichment/output/silver_enriched_customers.csv → default.silver_enriched_customers
```

### 4. Run the app

```bash
cd streamlit_app/
streamlit run app.py
```

---

## Environment Variables

| Variable | Description |
|---|---|
| `ANTHROPIC_API_KEY` | Claude API key from console.anthropic.com |
| `DATABRICKS_HOST` | Databricks workspace hostname (no https://) |
| `DATABRICKS_HTTP_PATH` | SQL Warehouse HTTP path |
| `DATABRICKS_TOKEN` | Databricks personal access token |

---

## Code Structure

| File | Responsibility |
|---|---|
| `app.py` | UI layout, page rendering, query orchestration |
| `utils/config.py` | All constants, schema definitions, format maps, guardrail patterns |
| `utils/llm.py` | `generate_sql()` and `generate_insight()` — Claude API calls |
| `utils/database.py` | `run_query()` — Databricks REST API execution |
| `utils/guardrails.py` | `check_input()`, `validate_sql()`, `enforce_limit()`, `is_on_cooldown()` |
| `utils/helpers.py` | `format_dataframe()`, `add_to_history()`, `guardrail_card()` |

---

## Phase Status

| Phase | Description | Status |
|---|---|---|
| 1 | Data ingestion — enrich UCI dataset, upload to Databricks | ✅ Complete |
| 2 | Silver layer — clean, join, compute RFM scores | ✅ Complete |
| 3 | Gold layer — customer_360, daily_kpis, segments, campaigns | ✅ Complete |
| 4 | Serving layer — Databricks SQL Warehouse | ✅ Complete |
| 5 | AI query layer — Claude API + Streamlit app | ✅ Complete |

---

## Tech Stack

| Layer | Technology |
|---|---|
| Data storage | Databricks DBFS + Delta Lake |
| Data processing | PySpark (Medallion architecture) |
| Serving | Databricks SQL Warehouse (Serverless) |
| AI / LLM | Anthropic Claude API (claude-haiku-4-5) |
| Frontend | Streamlit |
| Language | Python 3.11+ |

---

*Built by Rishikesh Rachamalla*
