"""
Phase 1: Data Enrichment Script
Project: AI-Powered NL Query Layer for Marketing Analytics
Author: Rishikesh Rachamalla

Loads the UCI Online Retail II dataset, saves a raw Bronze CSV,
and builds a Silver customer enrichment table with 26 synthetic
loyalty/marketing fields using Faker.
"""

import pandas as pd
import numpy as np
from faker import Faker
import random
import os
from datetime import datetime, timedelta

# ── Config ────────────────────────────────────────────────────────────────────
INPUT_FILE = "./online_retail_II.csv"   # or .xlsx — script auto-detects
OUTPUT_DIR = "./output"
RANDOM_SEED = 42

random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)
fake = Faker()
Faker.seed(RANDOM_SEED)

os.makedirs(OUTPUT_DIR, exist_ok=True)

# ── Column name mapping ───────────────────────────────────────────────────────
COLUMN_MAP = {
    "Invoice":     "invoice_no",
    "StockCode":   "stock_code",
    "Description": "description",
    "Quantity":    "quantity",
    "InvoiceDate": "invoice_date",
    "Price":       "unit_price",
    "Customer ID": "customer_id",
    "Country":     "country",
    # already-lowercase variants (some Kaggle versions)
    "invoice":      "invoice_no",
    "stockcode":    "stock_code",
    "description":  "description",
    "quantity":     "quantity",
    "invoicedate":  "invoice_date",
    "price":        "unit_price",
    "customer id":  "customer_id",
    "customerid":   "customer_id",
    "country":      "country",
}

# ── Step 1: Load dataset ──────────────────────────────────────────────────────
print("Step 1: Loading dataset...")

if not os.path.exists(INPUT_FILE):
    # Try xlsx variant
    xlsx_path = INPUT_FILE.replace(".csv", ".xlsx")
    if os.path.exists(xlsx_path):
        INPUT_FILE = xlsx_path
    else:
        raise FileNotFoundError(
            f"Dataset not found. Place 'online_retail_II.csv' (or .xlsx) "
            f"in the enrichment/ folder.\nExpected path: {os.path.abspath(INPUT_FILE)}"
        )

if INPUT_FILE.endswith(".xlsx"):
    # UCI file has two sheets; concatenate both years
    xl = pd.ExcelFile(INPUT_FILE)
    sheets = [pd.read_excel(INPUT_FILE, sheet_name=s) for s in xl.sheet_names]
    df = pd.concat(sheets, ignore_index=True)
else:
    df = pd.read_csv(INPUT_FILE, encoding="utf-8", low_memory=False)

print(f"  Loaded {len(df):,} rows, {df.shape[1]} columns")

# ── Step 2: Standardize column names ─────────────────────────────────────────
print("Step 2: Standardizing column names...")
df.columns = [COLUMN_MAP.get(c, COLUMN_MAP.get(c.strip(), c.strip().lower().replace(" ", "_")))
              for c in df.columns]

# Ensure expected columns exist
expected = ["invoice_no", "stock_code", "description", "quantity",
            "invoice_date", "unit_price", "customer_id", "country"]
missing = [c for c in expected if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns after rename: {missing}. "
                     f"Found: {list(df.columns)}")

# Cast customer_id to nullable Int64 (keeps NaN, avoids float formatting)
df["customer_id"] = pd.to_numeric(df["customer_id"], errors="coerce")
df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce")

# ── Step 3: Save Bronze CSV ───────────────────────────────────────────────────
print("Step 3: Saving Bronze layer (raw)...")
bronze_path = os.path.join(OUTPUT_DIR, "bronze_raw_transactions.csv")
df.to_csv(bronze_path, index=False)
print(f"  Saved: {bronze_path} ({len(df):,} rows, {df.shape[1]} columns)")

# ── Step 4: Build customer-level table ───────────────────────────────────────
print("Step 4: Building customer enrichment table...")
customers_df = df.dropna(subset=["customer_id"]).copy()
customers_df["customer_id"] = customers_df["customer_id"].astype(int)

# Aggregate real transaction stats per customer
agg = (
    customers_df.groupby("customer_id")
    .agg(
        total_transactions=("invoice_no", "nunique"),
        total_quantity=("quantity", "sum"),
        total_revenue=("unit_price", lambda x: (x * customers_df.loc[x.index, "quantity"]).sum()),
        first_purchase_date=("invoice_date", "min"),
        last_purchase_date=("invoice_date", "max"),
        country=("country", lambda x: x.mode()[0] if not x.mode().empty else "Unknown"),
    )
    .reset_index()
)
print(f"  Unique customers with IDs: {len(agg):,}")

# ── Step 5: Generate synthetic loyalty fields ─────────────────────────────────
print("Step 5: Generating synthetic loyalty fields...")

n = len(agg)

# Signup channel (POS-heavy, mirrors C-store reality)
signup_channels = random.choices(
    ["POS", "Mobile App", "Web", "Email Campaign", "Referral"],
    weights=[45, 25, 15, 10, 5],
    k=n,
)

# Loyalty tier based on total_transactions quartiles
txn = agg["total_transactions"]
tier_bins = [0, txn.quantile(0.40), txn.quantile(0.70), txn.quantile(0.90), txn.max() + 1]
tier_labels = ["Bronze", "Silver", "Gold", "Platinum"]
loyalty_tier = pd.cut(txn, bins=tier_bins, labels=tier_labels, include_lowest=True).astype(str)

# Churn risk score (inverse of recency — higher days since last purchase = higher risk)
max_date = agg["last_purchase_date"].max()
days_since = (max_date - agg["last_purchase_date"]).dt.days
churn_risk = (days_since / days_since.max()).round(4)

# Visit frequency (monthly) based on tenure and transaction count
tenure_months = ((agg["last_purchase_date"] - agg["first_purchase_date"]).dt.days / 30).clip(lower=1)
visit_freq = (agg["total_transactions"] / tenure_months).round(2)

# Binary / categorical synthetic fields
email_opt_in       = [random.random() < 0.68 for _ in range(n)]
sms_opt_in         = [random.random() < 0.42 for _ in range(n)]
push_opt_in        = [random.random() < 0.31 for _ in range(n)]
campaign_responder = [random.random() < 0.55 for _ in range(n)]
subscription_active = [random.random() < 0.22 for _ in range(n)]
discount_sensitivity = random.choices(["Low", "Medium", "High"], weights=[30, 45, 25], k=n)
preferred_category   = random.choices(
    ["Home & Garden", "Gifts", "Seasonal", "Office", "Clothing", "Food"],
    weights=[25, 22, 20, 15, 10, 8], k=n,
)
preferred_day_of_week = random.choices(
    ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"],
    weights=[12, 13, 15, 16, 20, 14, 10], k=n,
)
preferred_time_of_day = random.choices(["Morning", "Afternoon", "Evening"], weights=[35, 45, 20], k=n)

# Loyalty points: proportional to revenue with some noise
loyalty_points = (agg["total_revenue"].clip(lower=0) * 10 * np.random.uniform(0.8, 1.2, n)).astype(int)

# Redemption rate
redemption_rate = np.random.uniform(0.0, 0.6, n).round(4)

# Referral count
referral_count = np.random.choice([0, 1, 2, 3, 4, 5], p=[0.60, 0.20, 0.10, 0.05, 0.03, 0.02], size=n)

# Signup date: random date before first purchase
signup_dates = [
    (row.first_purchase_date - timedelta(days=random.randint(0, 365))).date()
    for _, row in agg.iterrows()
]

# Satisfaction score (1–5, skewed positive)
satisfaction_score = np.random.choice([1, 2, 3, 4, 5], p=[0.03, 0.07, 0.15, 0.40, 0.35], size=n)

# NPS category
nps_map = {1: "Detractor", 2: "Detractor", 3: "Passive", 4: "Passive", 5: "Promoter"}
nps_category = [nps_map[s] for s in satisfaction_score]

# Last campaign clicked
last_campaign = random.choices(
    ["Summer Sale", "Holiday Bundle", "Loyalty Bonus", "Re-engagement", "None"],
    weights=[20, 25, 30, 15, 10], k=n,
)

# ── Step 6: Assemble and save Silver enrichment table ────────────────────────
print("Step 6: Saving enrichment table...")

silver = agg.copy()
silver["loyalty_tier"]          = loyalty_tier.values
silver["signup_channel"]        = signup_channels
silver["signup_date"]           = signup_dates
silver["email_opt_in"]          = email_opt_in
silver["sms_opt_in"]            = sms_opt_in
silver["push_opt_in"]           = push_opt_in
silver["campaign_responder"]    = campaign_responder
silver["subscription_active"]   = subscription_active
silver["discount_sensitivity"]  = discount_sensitivity
silver["preferred_category"]    = preferred_category
silver["preferred_day_of_week"] = preferred_day_of_week
silver["preferred_time_of_day"] = preferred_time_of_day
silver["loyalty_points"]        = loyalty_points.values
silver["redemption_rate"]       = redemption_rate
silver["referral_count"]        = referral_count
silver["churn_risk_score"]      = churn_risk.values
silver["visit_frequency_monthly"] = visit_freq.values
silver["satisfaction_score"]    = satisfaction_score
silver["nps_category"]          = nps_category
silver["last_campaign_clicked"] = last_campaign

silver_path = os.path.join(OUTPUT_DIR, "silver_enriched_customers.csv")
silver.to_csv(silver_path, index=False)
print(f"  Saved: {silver_path} ({len(silver):,} rows, {silver.shape[1]} columns)")

# ── Step 7: Generate data dictionary ─────────────────────────────────────────
print("Step 7: Generating data dictionary...")

bronze_dict = [
    ("invoice_no",    "string",  "Unique invoice identifier; prefix 'C' = cancellation"),
    ("stock_code",    "string",  "Product/item code"),
    ("description",   "string",  "Product description (may be null)"),
    ("quantity",      "integer", "Units purchased; negative = return/cancellation"),
    ("invoice_date",  "datetime","Transaction timestamp"),
    ("unit_price",    "float",   "Price per unit in GBP; 0.0 = free/error"),
    ("customer_id",   "integer", "Customer identifier; ~135K rows are null (guest checkouts)"),
    ("country",       "string",  "Country of customer"),
]

silver_dict = [
    ("customer_id",           "integer", "Unique customer identifier (FK to bronze)"),
    ("total_transactions",    "integer", "Count of distinct invoices per customer"),
    ("total_quantity",        "integer", "Lifetime units purchased"),
    ("total_revenue",         "float",   "Lifetime revenue in GBP (quantity × unit_price)"),
    ("first_purchase_date",   "datetime","Date of first transaction"),
    ("last_purchase_date",    "datetime","Date of most recent transaction"),
    ("country",               "string",  "Most frequent country for this customer"),
    ("loyalty_tier",          "string",  "Bronze / Silver / Gold / Platinum (txn-count quartiles)"),
    ("signup_channel",        "string",  "Synthetic: enrollment channel (POS, Mobile App, Web, …)"),
    ("signup_date",           "date",    "Synthetic: loyalty program enrollment date"),
    ("email_opt_in",          "boolean", "Synthetic: email marketing consent (68% rate)"),
    ("sms_opt_in",            "boolean", "Synthetic: SMS marketing consent (42% rate)"),
    ("push_opt_in",           "boolean", "Synthetic: push notification consent (31% rate)"),
    ("campaign_responder",    "boolean", "Synthetic: responded to ≥1 marketing campaign (55%)"),
    ("subscription_active",   "boolean", "Synthetic: active paid loyalty subscription (22%)"),
    ("discount_sensitivity",  "string",  "Synthetic: price sensitivity — Low / Medium / High"),
    ("preferred_category",    "string",  "Synthetic: most purchased product category"),
    ("preferred_day_of_week", "string",  "Synthetic: day of week with highest visit rate"),
    ("preferred_time_of_day", "string",  "Synthetic: Morning / Afternoon / Evening"),
    ("loyalty_points",        "integer", "Synthetic: accumulated points (revenue × 10 ± noise)"),
    ("redemption_rate",       "float",   "Synthetic: fraction of points redeemed (0.0–0.6)"),
    ("referral_count",        "integer", "Synthetic: number of friends referred"),
    ("churn_risk_score",      "float",   "Synthetic: 0–1 score; higher = more days since last visit"),
    ("visit_frequency_monthly","float",  "Synthetic: avg transactions per month over tenure"),
    ("satisfaction_score",    "integer", "Synthetic: 1–5 CSAT score (skewed positive)"),
    ("nps_category",          "string",  "Synthetic: Detractor / Passive / Promoter (from CSAT)"),
    ("last_campaign_clicked", "string",  "Synthetic: most recent campaign the customer engaged with"),
]

dd_lines = [
    "# Data Dictionary — NL Query Layer for Marketing Analytics",
    f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
    "",
    "---",
    "",
    "## Bronze Table: `bronze_raw_transactions`",
    f"**Rows:** ~{len(df):,} &nbsp;|&nbsp; **Source:** UCI Online Retail II (Kaggle)",
    "",
    "| Column | Type | Description |",
    "|--------|------|-------------|",
]
for col, dtype, desc in bronze_dict:
    dd_lines.append(f"| `{col}` | {dtype} | {desc} |")

dd_lines += [
    "",
    "---",
    "",
    "## Silver Table: `silver_enriched_customers`",
    f"**Rows:** ~{len(silver):,} &nbsp;|&nbsp; **Grain:** one row per unique customer_id",
    "",
    "> Fields marked **Synthetic** are generated with Faker/numpy for demo purposes.",
    "> Real fields are derived from the UCI transaction data.",
    "",
    "| Column | Type | Description |",
    "|--------|------|-------------|",
]
for col, dtype, desc in silver_dict:
    dd_lines.append(f"| `{col}` | {dtype} | {desc} |")

dd_path = os.path.join(OUTPUT_DIR, "data_dictionary.md")
with open(dd_path, "w") as f:
    f.write("\n".join(dd_lines) + "\n")
print(f"  Saved: {dd_path}")

# ── Summary ───────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("DONE! Files ready for upload to Databricks.")
print("=" * 60)
print(f"\n  Bronze CSV : {bronze_path}")
print(f"  Silver CSV : {silver_path}")
print(f"  Dictionary : {dd_path}")
print(f"\nBronze stats:")
print(f"  Rows            : {len(df):,}")
print(f"  Null customer_id: {df['customer_id'].isna().sum():,}")
print(f"  Cancellations   : {df['invoice_no'].astype(str).str.startswith('C').sum():,}")
print(f"\nSilver stats:")
print(f"  Unique customers: {len(silver):,}")
print(f"  Loyalty tiers:\n{silver['loyalty_tier'].value_counts().to_string()}")
print(f"\n  Signup channels:\n{silver['signup_channel'].value_counts().to_string()}")
