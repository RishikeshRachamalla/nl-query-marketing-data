import re
import time
import streamlit as st

from utils.config import (
    MIN_INPUT_LEN, MAX_INPUT_LEN, RESULT_LIMIT,
    COOLDOWN_SECS, BLOCKED_SQL_KEYWORDS,
    LARGE_TABLE_NAMES, PROMPT_INJECTION_PATTERNS,
)


def check_input(text: str) -> tuple[bool, str | None, str | None]:
    """
    Validates the user's raw input.
    Returns (ok, error_type, error_message).
    """
    stripped = text.strip()

    if len(stripped) < MIN_INPUT_LEN:
        return False, "too_short", "Your question is too short. Please be more specific."

    if len(stripped) > MAX_INPUT_LEN:
        return False, "too_long", f"Your question exceeds {MAX_INPUT_LEN} characters. Please shorten it."

    # Gibberish check — long words with no vowels
    long_words = [w for w in stripped.split() if len(w) > 5]
    if long_words:
        no_vowel = sum(1 for w in long_words if not re.search(r'[aeiouAEIOU]', w))
        if no_vowel / len(long_words) > 0.6:
            return False, "gibberish", "That doesn't look like a valid question. Try asking something about your marketing data."

    # Prompt injection check
    lower = stripped.lower()
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, lower):
            return False, "injection", "That input looks like an attempt to manipulate the AI. Please ask a genuine marketing data question."

    return True, None, None


def validate_sql(sql: str) -> None:
    """
    Raises ValueError if the SQL contains blocked keywords or SELECT * on large tables.
    """
    sql_upper = sql.upper()

    for kw in BLOCKED_SQL_KEYWORDS:
        if kw in sql_upper:
            raise ValueError(f"Query contains forbidden keyword: `{kw}`. Only SELECT queries are allowed.")

    if re.search(r"SELECT\s+\*", sql_upper):
        for table in LARGE_TABLE_NAMES:
            if table.upper() in sql_upper:
                raise ValueError(
                    f"`SELECT *` on `{table}` is not allowed — it has 500K+ rows. "
                    "Please select specific columns instead."
                )


def enforce_limit(sql: str) -> str:
    """Injects LIMIT clause if missing."""
    if "LIMIT" not in sql.upper():
        sql = sql.rstrip(";").rstrip() + f"\nLIMIT {RESULT_LIMIT}"
    return sql


def is_on_cooldown() -> bool:
    """Returns True if the user submitted a query too recently."""
    return (time.time() - st.session_state.get("last_query_time", 0)) < COOLDOWN_SECS


def missing_env_keys(required: dict) -> list[str]:
    """Returns list of env variable names that are missing or empty."""
    return [k for k, v in required.items() if not v]
