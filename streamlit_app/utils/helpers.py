import time
import pandas as pd
import streamlit as st

from utils.config import FORMAT_MAP


def format_dataframe(df: pd.DataFrame, formats: dict):
    """Applies number formatting to a DataFrame for display."""
    format_dict = {}
    for col, fmt_type in formats.items():
        if col in df.columns and df[col].dtype in ["int64", "float64"]:
            fmt = FORMAT_MAP.get(fmt_type)
            if fmt:
                format_dict[col] = fmt
    return df.style.format(format_dict) if format_dict else df


def add_to_history(question: str, row_count: int) -> None:
    """Prepends a query to session history (max 10 entries, no consecutive duplicates)."""
    if "query_history" not in st.session_state:
        st.session_state["query_history"] = []

    history = st.session_state["query_history"]
    if history and history[0]["question"] == question:
        return

    history.insert(0, {
        "question": question,
        "rows":     row_count,
        "time":     time.strftime("%H:%M:%S"),
    })
    st.session_state["query_history"] = history[:10]


def guardrail_card(card_type: str, icon: str, title: str, body: str, hint: str = "") -> None:
    """Renders a styled error/warning card using st.markdown."""
    css_class = "oos-card" if card_type == "oos" else "warn-card"
    hint_html = f'<div class="guardrail-hint">{hint}</div>' if hint else ""
    st.markdown(f"""
    <div class="{css_class}">
        <div class="guardrail-icon">{icon}</div>
        <div class="guardrail-title">{title}</div>
        <div class="guardrail-body">{body}</div>
        {hint_html}
    </div>
    """, unsafe_allow_html=True)
