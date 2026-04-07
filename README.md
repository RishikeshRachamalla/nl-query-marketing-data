# 🎯 Data Play — Ask Your Marketing Data Anything

<p align="center">
  <img src="https://img.shields.io/badge/Databricks-FF3621?style=for-the-badge&logo=databricks&logoColor=white"/>
  <img src="https://img.shields.io/badge/Delta_Lake-003366?style=for-the-badge&logo=apachespark&logoColor=white"/>
  <img src="https://img.shields.io/badge/Claude_API-8A2BE2?style=for-the-badge&logo=anthropic&logoColor=white"/>
  <img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>
  <img src="https://img.shields.io/badge/Python_3.11-3776AB?style=for-the-badge&logo=python&logoColor=white"/>
</p>

<p align="center">
  <strong>Type a question. Get SQL. See results. Understand the story.</strong><br/>
  A natural-language analytics interface built on a full Medallion pipeline — 525K retail rows, Gold tables, and Claude AI.
</p>

---

## ✨ What It Does

**Data Play** turns plain English questions into live Databricks SQL queries — no SQL knowledge needed.

```
You type:   "Which signup channel drives the most revenue?"
Claude:      SELECT signup_channel, SUM(total_revenue) ...
Databricks:  Executes against 525K row Gold table
You see:     Table + chart + AI business insight + follow-up ideas
```

Built end-to-end: raw CSV → Medallion architecture (Bronze → Silver → Gold) → served via Databricks SQL Warehouse → queried through a Streamlit app powered by Claude API.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DATA PIPELINE (Databricks)                  │
│                                                                 │
│  UCI Online Retail II   →   Bronze Layer   →   Silver Layer    │
│     525K transactions        (raw Delta)      (cleaned, RFM,   │
│     + Faker enrichment                         loyalty scores)  │
│                                                                 │
│                         Silver Layer   →   Gold Layer          │
│                                           customer_360          │
│                                           daily_kpis            │
│                                           segment_summary       │
│                                           campaign_metrics      │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    Databricks SQL Warehouse
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                     AI QUERY LAYER (Streamlit)                  │
│                                                                 │
│   User question  →  Claude API (NL → SQL)  →  Databricks SQL  │
│                  ←  Results + KPIs + Chart                      │
│                  ←  AI Insight + 3 Follow-up Questions          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🗂️ Gold Tables

| Table | Rows | What's Inside |
|---|---|---|
| `customer_360` | ~4,372 | Full customer profile — RFM scores, loyalty tier, demographics, churn risk, basket size |
| `daily_kpis` | ~750 | Daily revenue, transaction count, active customers (Dec 2009 – Dec 2011) |
| `segment_summary` | 4 | Revenue, AOV, frequency aggregated by loyalty tier (Bronze / Silver / Gold / Platinum) |
| `campaign_metrics` | ~6 | Acquisition channel performance — email opt-in rates, revenue per channel |

---

## 🎨 App Features

### 🤖 AI Query Layer
- **Natural language → SQL** — Schema-aware Claude prompt generates precise, safe SQL
- **AI Insight card** — Every result gets a 2-3 sentence analyst-style business interpretation
- **Smart follow-ups** — 3 context-aware follow-up questions generated per query, one-click to run

### 🛡️ 6-Layer Guardrail System

| Layer | Guard | Protects Against |
|---|---|---|
| 1 | Query cooldown (3s) | Warehouse hammering |
| 2 | Input validation | Too short / too long / gibberish inputs |
| 3 | Prompt injection detection | AI jailbreak / manipulation attempts |
| 4 | Out-of-scope detection | Weather, sports, unrelated questions |
| 5 | Destructive SQL blocking | `DROP`, `DELETE`, `ALTER`, `TRUNCATE` |
| 6 | `SELECT *` guard + auto-`LIMIT` | Full table scans on 500K+ row tables |

### 📊 Data Presentation
- Formatted columns — currency (`$1,234`), percentages (`87.3%`), integers
- Auto-sized bar/line charts per result shape
- KPI summary row (smart avg vs. sum based on column type)
- One-click CSV download

### 🧭 UX
- Dark animated gradient UI
- Schema explorer sidebar — all 4 tables with column types
- Query history (last 10 queries, no duplicates)
- Compact hero mode once a query is active
- `.env` health check on startup with actionable error messages

---

## 🚀 Quick Start

### 1. Clone & install

```bash
git clone https://github.com/RishikeshRachamalla/nl-query-marketing-data.git
cd nl-query-marketing-data

python3 -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
```

Fill in `.env`:

```env
ANTHROPIC_API_KEY=sk-ant-...
DATABRICKS_HOST=your-workspace.azuredatabricks.net
DATABRICKS_HTTP_PATH=/sql/1.0/warehouses/your_warehouse_id
DATABRICKS_TOKEN=dapiXXXXXXXXXXXXXXXX
```

### 3. Build the data pipeline (Databricks)

```bash
# 1. Download UCI Online Retail II from Kaggle:
#    https://www.kaggle.com/datasets/mashlyn/online-retail-ii-uci
#    Place the .xlsx file in enrichment/

# 2. Enrich the dataset locally
cd enrichment/
python enrich_retail_data.py

# 3. Upload output CSVs to Databricks DBFS via the UI
#    enrichment/output/bronze_raw_transactions.csv   → default.bronze_raw_transactions
#    enrichment/output/silver_enriched_customers.csv → default.silver_enriched_customers

# 4. Run notebooks in order (Databricks workspace):
#    notebooks/01_bronze_ingestion.py
#    notebooks/02_silver_transformation.py
#    notebooks/03_gold_aggregation.py
#    notebooks/04_data_quality_checks.py
```

### 4. Run the app

```bash
cd streamlit_app/
streamlit run app.py
```

Open `http://localhost:8501` — start asking questions.

---

## 💬 Example Questions to Try

```
Top 10 customers by total spend
Which signup channel drives the most revenue?
Platinum customers with high churn risk
Email opt-in rate by age group
Compare avg basket size across loyalty tiers
Show daily revenue trend for 2011
```

---

## 📁 Project Structure

```
nl-query-marketing-data/
├── enrichment/
│   ├── enrich_retail_data.py        # Phase 1: UCI dataset enrichment + Faker fields
│   └── output/                      # Generated CSVs (gitignored)
│
├── notebooks/
│   ├── 01_bronze_ingestion.py       # Databricks: Bronze Delta table
│   ├── 02_silver_transformation.py  # Databricks: Clean, join, RFM scores
│   ├── 03_gold_aggregation.py       # Databricks: Build 4 Gold tables
│   └── 04_data_quality_checks.py   # Databricks: Row counts, null checks
│
├── streamlit_app/
│   ├── app.py                       # UI layout, page rendering, query orchestration
│   └── utils/
│       ├── config.py                # Constants, schema, format maps, guardrail patterns
│       ├── llm.py                   # Claude API — SQL generation + AI insights
│       ├── database.py              # Databricks SQL Warehouse query execution
│       ├── guardrails.py            # Input validation, SQL safety, rate limiting
│       └── helpers.py              # Formatting, query history, UI components
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔧 Environment Variables

| Variable | Where to get it |
|---|---|
| `ANTHROPIC_API_KEY` | [console.anthropic.com](https://console.anthropic.com) |
| `DATABRICKS_HOST` | Databricks workspace URL (no `https://`) |
| `DATABRICKS_HTTP_PATH` | SQL Warehouse → Connection Details → HTTP Path |
| `DATABRICKS_TOKEN` | Databricks → User Settings → Access Tokens |

---

## ✅ Build Status

| Phase | What Was Built | Status |
|---|---|---|
| 1 | UCI data ingestion, Faker enrichment, DBFS upload | ✅ Done |
| 2 | Silver layer — dedup, joins, RFM computation | ✅ Done |
| 3 | Gold layer — 4 aggregated Delta tables | ✅ Done |
| 4 | Databricks SQL Warehouse (serverless) | ✅ Done |
| 5 | Streamlit AI query layer with Claude API | ✅ Done |

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Raw storage | Databricks DBFS |
| Data format | Delta Lake (ACID transactions, time travel) |
| Processing | PySpark (Medallion architecture) |
| Serving | Databricks SQL Warehouse — Serverless |
| LLM | Anthropic Claude API (`claude-haiku-4-5`) |
| Frontend | Streamlit |
| Language | Python 3.11+ |

---

<p align="center">Built by <strong>Rishikesh Rachamalla</strong></p>
