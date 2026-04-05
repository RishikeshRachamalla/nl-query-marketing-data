import os
import requests
import pandas as pd
import streamlit as st
import anthropic
import json
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
DATABRICKS_HOST = os.getenv("DATABRICKS_HOST")
DATABRICKS_HTTP_PATH = os.getenv("DATABRICKS_HTTP_PATH")
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN")

# Extract warehouse ID from HTTP path
WAREHOUSE_ID = DATABRICKS_HTTP_PATH.split("/")[-1]

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

# def generate_sql(question):
#     client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
#     message = client.messages.create(
#         model="claude-haiku-4-5-20251001",
#         max_tokens=500,
#         system=f"""You are a SQL expert. Given a natural language question, generate a Databricks SQL query.
# {SCHEMA_CONTEXT}
# Rules:
# - Return ONLY the SQL query, no explanation, no markdown, no backticks.
# - Use the full table path (marketing.gold.table_name).
# - Keep queries simple and readable.
# - Always LIMIT results to 50 rows unless the user specifies otherwise.""",
#         messages=[{"role": "user", "content": question}]
#     )
#     return message.content[0].text.strip()

def generate_sql(question):
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system=f"""You are a SQL expert specializing in Databricks SQL. Given a natural language question, generate a Databricks SQL query.
            Note: This dataset contains historical transaction data from Dec 2009 to Dec 2011. 
            Avoid relative date filters like 'last 5 weeks' or 'past month'. 
            Use absolute date ranges or non-date filters instead.
            {SCHEMA_CONTEXT}
            Rules:
            - Data date range: This dataset contains historical transaction data from December 2009 to December 2011.
            - Return ONLY valid JSON with two keys: "sql" and "formats".
            - Only use Databricks SQL compatible functions.
            - "sql": the Databricks SQL query using full table path (marketing.gold.table_name). Always LIMIT to 50 rows unless user specifies otherwise.
            - "formats": a dict mapping each selected column name to one of: "currency", "integer", "percent", "id", "text".
            - Use "id" for identifier columns like customer_id.
            - Use "currency" for monetary columns like spend, revenue, value.
            - Use "integer" for counts like transactions, items, customers.
            - Use "percent" for ratio/rate/pct columns.
            - No explanation, no markdown, no backticks. Pure JSON only.""",
        messages=[{"role": "user", "content": question}]
    )
    raw = message.content[0].text.strip()
    # st.write(f"DEBUG raw response: `{raw}`")  # temporary debug
    raw = raw.replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)
    # st.write(f"DEBUG parsed response: `{parsed}`")  # temporary debug
    return parsed["sql"], parsed["formats"]

def run_query(sql_query):
    url = f"https://{DATABRICKS_HOST}/api/2.0/sql/statements"
    headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}", "Content-Type": "application/json"}
    # payload = {
    #     "warehouse_id": WAREHOUSE_ID,
    #     "statement": sql_query,
    #     "wait_timeout": "50s",
    #     "disposition": "INLINE",
    #     "format": "JSON_ARRAY"
    # }
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "statement": sql_query,
        "wait_timeout": "50s"
}
    
    response = requests.post(url, headers=headers, json=payload)
    data = response.json()
    
    state = data.get("status", {}).get("state", "UNKNOWN")
    if state != "SUCCEEDED":
        st.write("DEBUG RESPONSE:", data)
    
    if state == "SUCCEEDED":
        columns = [col["name"] for col in data["manifest"]["schema"]["columns"]]
        # df = pd.DataFrame(data["result"]["data_array"], columns=columns)
        rows = data.get("result", {}).get("data_array", [])
        df = pd.DataFrame(rows, columns=columns)
        return df.apply(pd.to_numeric, errors='ignore')
    else:
        # raise Exception(f"State: {state} | Full response: {data}")
        # raise Exception(f"State: {state} | Error code: {data.get('status', {}).get('error', {}).get('error_code')} | Message: {data.get('status', {}).get('error', {}).get('message')}")
        raise Exception(f"Full response: {json.dumps(data, indent=2)}")

def validate_sql(sql):
    blocked = ['DROP', 'DELETE', 'ALTER', 'TRUNCATE', 'INSERT', 'UPDATE', 'CREATE', 'REPLACE']
    sql_upper = sql.upper()
    for keyword in blocked:
        if keyword in sql_upper:
            raise Exception(f"Query contains forbidden keyword: {keyword}. Only SELECT queries are allowed.")

st.title("Marketing Data Query Assistant")
st.caption("Ask questions about customers, revenue, segments, and campaigns in plain English.")

question = st.text_input("Ask a question:", placeholder="e.g. Show me top 10 customers by total spend")
st.markdown("**Try these:**")
examples = [
    "Top 10 customers by total spend",
    "Average basket size by loyalty tier",
    "Revenue by signup channel",
    "Churn risk score by age group",
    "Daily revenue from available data last 2 weeks",
]

cols = st.columns(len(examples))
for i, example in enumerate(examples):
    if cols[i].button(example, use_container_width=True):
        question = example

FORMAT_MAP = {
    "currency": "${:,.2f}",
    "integer": "{:,}",
    "decimal": "{:,.2f}",
    "percent": "{:,.1f}%",
    # "id": "{:,}",
    "text": None
}

if question:
    # Debug: test Databricks connection
    try:
        test_url = f"https://{DATABRICKS_HOST}/api/2.0/sql/statements"
        test_headers = {"Authorization": f"Bearer {DATABRICKS_TOKEN}", "Content-Type": "application/json"}
        test_payload = {"warehouse_id": WAREHOUSE_ID, "statement": "SELECT 1", "wait_timeout": "30s"}
        test_response = requests.post(test_url, headers=test_headers, json=test_payload)
        st.write("Connection test status code:", test_response.status_code)
        st.write("Connection test response:", test_response.json())
    except Exception as e:
        st.write("Connection test failed:", str(e))

    with st.spinner("Generating SQL..."):
        sql_query, formats = generate_sql(question)

    # Guardrail check
    try:
        validate_sql(sql_query)
    except Exception as e:
        st.error(str(e))
        st.stop()

    st.subheader("Generated SQL")
    # st.code(sql_query, language="sql")
    st.code(sql_query, language="sql", wrap_lines=True)

    try:
        with st.spinner("Running query..."):
            df = run_query(sql_query)

        if not df.empty:
            st.subheader("Results")
            try:
                format_dict = {}
                for col, fmt_type in formats.items():
                    if col in df.columns:
                        fmt = FORMAT_MAP.get(fmt_type)
                        if fmt:
                            format_dict[col] = fmt
                st.dataframe(df.style.format(format_dict), use_container_width=True)
            except Exception:
                st.dataframe(df, use_container_width=True)

            # Auto chart
            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            categorical_cols = df.select_dtypes(exclude='number').columns.tolist()

            if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
                st.subheader("Chart")
                chart_col = st.selectbox("Select metric to chart:", numeric_cols)
                st.bar_chart(df.set_index(categorical_cols[0])[chart_col])
            elif len(numeric_cols) >= 2:
                st.subheader("Chart")
                st.line_chart(df.set_index(df.columns[0])[numeric_cols[1:]])
        else:
            st.info("Query returned no results.")

    except Exception as e:
        st.error(f"Query failed: {str(e)}")