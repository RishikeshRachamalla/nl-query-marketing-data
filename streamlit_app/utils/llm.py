import json
import pandas as pd
import anthropic

from utils.config import ANTHROPIC_API_KEY, SCHEMA_CONTEXT, RESULT_LIMIT


def generate_sql(question: str) -> tuple[str | None, dict | None, str | None]:
    """
    Sends the user's question to Claude and returns (sql, formats, oos_reason).

    - If the question is out of scope:  (None, None, reason_string)
    - If the question is valid:         (sql_string, formats_dict, None)
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=600,
        system=f"""You are a SQL expert specialising in Databricks SQL for a marketing analytics platform.

First, decide if the question is relevant to the available marketing data.
If the question is NOT related to customers, transactions, revenue, loyalty, segments, campaigns,
or marketing KPIs — return:
{{"relevant": false, "reason": "one sentence explaining what this app covers"}}

If the question IS relevant, return:
{{"relevant": true, "sql": "<query>", "formats": {{...}}}}

Note: This dataset contains HISTORICAL transaction data from Dec 2009 to Dec 2011.
Avoid relative date filters like 'last 5 weeks' or 'past month'.
Use absolute date ranges or non-date filters instead.

{SCHEMA_CONTEXT}

SQL rules (only when relevant=true):
- "sql": SQL query using full table path (marketing.gold.table_name).
         LIMIT to {RESULT_LIMIT} rows unless the user specifies otherwise.
- "formats": dict mapping each selected column name to one of:
             "currency", "integer", "percent", "id", "text".
  • "id"       → identifier columns (customer_id)
  • "currency" → monetary columns (spend, revenue, value)
  • "integer"  → count columns (transactions, items, customers)
  • "percent"  → ratio/rate/pct columns
- No explanation, no markdown, no backticks. Pure JSON only.""",
        messages=[{"role": "user", "content": question}],
    )

    raw = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)

    if not parsed.get("relevant", True):
        return None, None, parsed.get("reason", "This question is outside the scope of the marketing dataset.")

    return parsed["sql"], parsed["formats"], None


def generate_insight(question: str, sql: str, df: pd.DataFrame) -> tuple[str, list[str]]:
    """
    Given the original question, SQL, and result DataFrame, returns:
      - insight  : 2-3 sentence analyst-style business insight
      - followups: list of 3 smart follow-up questions
    """
    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    # Build a concise data summary to pass to Claude
    sample_csv  = df.head(10).to_csv(index=False)
    row_count   = len(df)
    col_summary = ", ".join(
        f"{c} ({df[c].dtype})" for c in df.columns
    )

    # Numeric summary for context
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    stats_lines  = []
    for col in numeric_cols[:6]:                    # cap at 6 cols
        stats_lines.append(
            f"  {col}: min={df[col].min():,.2f}, "
            f"max={df[col].max():,.2f}, "
            f"avg={df[col].mean():,.2f}"
        )
    stats_text = "\n".join(stats_lines) if stats_lines else "No numeric columns."

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=500,
        system="""You are a senior marketing analyst reviewing query results from a retail loyalty dataset.

Given a question, SQL query, and data sample, return a JSON object with:
{
  "insight": "2-3 sentence business insight. Be specific — use actual numbers from the data. End with one actionable recommendation.",
  "followups": ["follow-up question 1", "follow-up question 2", "follow-up question 3"]
}

Rules:
- Insight must reference specific values from the data (e.g. "$1.2M", "34%", "Platinum tier")
- Tone: direct, confident, like a real analyst presenting to a CMO
- Follow-up questions must be different angles on the same data — dig deeper or pivot to related metrics
- No markdown, no backticks. Pure JSON only.""",
        messages=[{
            "role": "user",
            "content": (
                f"Question: {question}\n\n"
                f"SQL:\n{sql}\n\n"
                f"Result: {row_count} rows, columns: {col_summary}\n\n"
                f"Data sample (first 10 rows):\n{sample_csv}\n\n"
                f"Numeric stats:\n{stats_text}"
            ),
        }],
    )

    raw    = message.content[0].text.strip().replace("```json", "").replace("```", "").strip()
    parsed = json.loads(raw)

    insight   = parsed.get("insight", "")
    followups = parsed.get("followups", [])[:3]
    return insight, followups
