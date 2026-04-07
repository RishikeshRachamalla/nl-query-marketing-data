import os
from dotenv import load_dotenv

load_dotenv()

# ── API credentials ───────────────────────────────────────────────────────────
ANTHROPIC_API_KEY    = os.getenv("ANTHROPIC_API_KEY")
DATABRICKS_HOST      = os.getenv("DATABRICKS_HOST")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN     = os.getenv("DATABRICKS_TOKEN")
WAREHOUSE_ID         = DATABRICKS_HTTP_PATH.split("/")[-1] if DATABRICKS_HTTP_PATH else ""

# ── App limits ────────────────────────────────────────────────────────────────
MIN_INPUT_LEN = 5
MAX_INPUT_LEN = 400
RESULT_LIMIT  = 50
COOLDOWN_SECS = 3

# ── Required env keys ─────────────────────────────────────────────────────────
REQUIRED_ENV = {
    "ANTHROPIC_API_KEY":    ANTHROPIC_API_KEY,
    "DATABRICKS_HOST":      DATABRICKS_HOST,
    "DATABRICKS_HTTP_PATH": DATABRICKS_HTTP_PATH,
    "DATABRICKS_TOKEN":     DATABRICKS_TOKEN,
}

# ── Example prompts ───────────────────────────────────────────────────────────
EXAMPLES = [
    "Top 10 customers by total spend",
    "Which signup channel drives the most revenue?",
    "Platinum customers with high churn risk",
    "Email opt-in rate by age group",
    "Compare avg basket size across loyalty tiers",
]

# ── Number format map ─────────────────────────────────────────────────────────
FORMAT_MAP = {
    "currency": "${:,.2f}",
    "integer":  "{:,}",
    "decimal":  "{:,.2f}",
    "percent":  "{:,.1f}%",
    "id":       "{}",
    "text":     None,
}

# ── Column type → badge colour ────────────────────────────────────────────────
TYPE_BADGE = {
    "int":       "#3b82f6",
    "double":    "#10b981",
    "string":    "#a78bfa",
    "boolean":   "#f59e0b",
    "date":      "#ec4899",
    "timestamp": "#ec4899",
}

# ── Schema for LLM system prompt ─────────────────────────────────────────────
SCHEMA_CONTEXT = """
You have access to these tables in a Databricks SQL warehouse:

1. marketing.gold.customer_360
   Columns: customer_id (int), first_purchase_date (timestamp), last_purchase_date (timestamp),
   total_transactions (int), total_items_purchased (int), total_spend (double), country (string),
   avg_basket_size (double), visit_frequency_monthly (double), loyalty_points (int),
   churn_risk_score (int), redemption_count (int), loyalty_tier (string), signup_channel (string),
   age_group (string), gender (string), email_opt_in (boolean), sms_opt_in (boolean),
   push_opt_in (boolean), preferred_payment (string), preferred_category (string),
   campaign_responder (boolean), subscription_active (boolean), promo_codes_used (int),
   discount_sensitivity (string), referral_count (int), signup_date (date),
   avg_transaction_value (double), unique_products_purchased (int),
   countries_purchased_from (int), spend_stddev (double)

2. marketing.gold.daily_kpis
   Columns: transaction_date (date), total_revenue (double), total_transactions (int),
   active_customers (int), total_items_sold (int), unique_products_sold (int),
   avg_basket_size (double), avg_revenue_per_customer (double)

3. marketing.gold.segment_summary
   Columns: loyalty_tier (string), customer_count (int), avg_total_spend (double),
   avg_basket_size (double), avg_visit_frequency (double), avg_churn_risk (double),
   avg_loyalty_points (int), avg_redemptions (double), email_optin_pct (double),
   campaign_response_pct (double), subscription_pct (double), total_segment_revenue (double)

4. marketing.gold.campaign_metrics
   Columns: signup_channel (string), customer_count (int), avg_lifetime_spend (double),
   avg_transactions (double), avg_basket_size (double), avg_churn_risk (double),
   email_optin_pct (double), sms_optin_pct (double), campaign_response_pct (double),
   total_channel_revenue (double)
"""

# ── Table icons for sidebar ───────────────────────────────────────────────────
TABLE_ICONS = {
    "customer_360":     "👥",
    "daily_kpis":       "📈",
    "segment_summary":  "🎯",
    "campaign_metrics": "📣",
}

# ── Schema for sidebar explorer ───────────────────────────────────────────────
SCHEMA_SIDEBAR = {
    "customer_360": {
        "desc": "One row per customer — RFM, loyalty, demographics",
        "cols": [
            ("customer_id",            "int",       "id"),
            ("total_spend",            "double",    "currency"),
            ("total_transactions",     "int",       "integer"),
            ("loyalty_tier",           "string",    "text"),
            ("churn_risk_score",       "int",       "integer"),
            ("signup_channel",         "string",    "text"),
            ("age_group",              "string",    "text"),
            ("gender",                 "string",    "text"),
            ("loyalty_points",         "int",       "integer"),
            ("email_opt_in",           "boolean",   "text"),
            ("campaign_responder",     "boolean",   "text"),
            ("avg_basket_size",        "double",    "currency"),
            ("visit_frequency_monthly","double",    "decimal"),
            ("first_purchase_date",    "timestamp", "text"),
            ("last_purchase_date",     "timestamp", "text"),
        ],
    },
    "daily_kpis": {
        "desc": "Aggregated daily revenue & transaction KPIs",
        "cols": [
            ("transaction_date",          "date",   "text"),
            ("total_revenue",             "double", "currency"),
            ("total_transactions",        "int",    "integer"),
            ("active_customers",          "int",    "integer"),
            ("avg_basket_size",           "double", "currency"),
            ("avg_revenue_per_customer",  "double", "currency"),
        ],
    },
    "segment_summary": {
        "desc": "Per loyalty tier segment aggregates",
        "cols": [
            ("loyalty_tier",          "string", "text"),
            ("customer_count",        "int",    "integer"),
            ("avg_total_spend",       "double", "currency"),
            ("avg_churn_risk",        "double", "decimal"),
            ("email_optin_pct",       "double", "percent"),
            ("campaign_response_pct", "double", "percent"),
            ("total_segment_revenue", "double", "currency"),
        ],
    },
    "campaign_metrics": {
        "desc": "Per signup channel marketing performance",
        "cols": [
            ("signup_channel",        "string", "text"),
            ("customer_count",        "int",    "integer"),
            ("avg_lifetime_spend",    "double", "currency"),
            ("email_optin_pct",       "double", "percent"),
            ("campaign_response_pct", "double", "percent"),
            ("total_channel_revenue", "double", "currency"),
        ],
    },
}

# ── Blocked SQL keywords ──────────────────────────────────────────────────────
BLOCKED_SQL_KEYWORDS = [
    "DROP", "DELETE", "ALTER", "TRUNCATE",
    "INSERT", "UPDATE", "CREATE", "REPLACE",
]

LARGE_TABLE_NAMES = ["customer_360"]

# ── Prompt injection patterns ─────────────────────────────────────────────────
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(previous|prior|above|all)\s+instructions",
    r"forget\s+(everything|all|previous)",
    r"you\s+are\s+now\s+a",
    r"act\s+as\s+(if\s+you\s+are|a\s+different)",
    r"new\s+system\s+prompt",
    r"jailbreak",
    r"do\s+anything\s+now",
    r"override\s+(your\s+)?(instructions|rules|prompt)",
    r"reveal\s+(your\s+)?(system\s+)?prompt",
    r"disregard\s+(your\s+)?(previous\s+)?instructions",
]
