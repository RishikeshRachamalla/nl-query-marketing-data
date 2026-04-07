import requests
import pandas as pd

from utils.config import DATABRICKS_HOST, DATABRICKS_TOKEN, WAREHOUSE_ID


def run_query(sql_query: str) -> pd.DataFrame:
    """
    Executes a SQL query against Databricks SQL Warehouse.
    Returns a DataFrame on success, raises Exception on failure.
    """
    url     = f"https://{DATABRICKS_HOST}/api/2.0/sql/statements"
    headers = {
        "Authorization": f"Bearer {DATABRICKS_TOKEN}",
        "Content-Type":  "application/json",
    }
    payload = {
        "warehouse_id": WAREHOUSE_ID,
        "statement":    sql_query,
        "wait_timeout": "50s",
    }

    response = requests.post(url, headers=headers, json=payload)
    data     = response.json()
    state    = data.get("status", {}).get("state", "UNKNOWN")

    if state == "FAILED":
        error_msg = data.get("status", {}).get("error", {}).get("message", "Query failed with an unknown error.")
        raise Exception(error_msg)

    if state != "SUCCEEDED":
        raise Exception(f"Unexpected query state: {state}. Please try again.")

    columns = [col["name"] for col in data["manifest"]["schema"]["columns"]]
    rows    = data.get("result", {}).get("data_array", [])
    df      = pd.DataFrame(rows, columns=columns)

    # Coerce numeric columns
    for col in df.columns:
        try:
            df[col] = pd.to_numeric(df[col])
        except (ValueError, TypeError):
            pass

    return df
