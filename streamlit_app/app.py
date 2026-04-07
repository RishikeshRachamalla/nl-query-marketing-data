import time
import streamlit as st
import streamlit.components.v1 as components

from utils.config    import (
    EXAMPLES, FORMAT_MAP, TYPE_BADGE, TABLE_ICONS,
    SCHEMA_SIDEBAR, REQUIRED_ENV, RESULT_LIMIT, MAX_INPUT_LEN,
)
from utils.guardrails import check_input, validate_sql, enforce_limit, is_on_cooldown, missing_env_keys
from utils.llm        import generate_sql, generate_insight
from utils.database   import run_query
from utils.helpers    import format_dataframe, add_to_history, guardrail_card

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Data Play",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ── Animated background ── */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #1a1a2e, #16213e);
    background-size: 400% 400%;
    animation: gradientShift 12s ease infinite;
}
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.97) !important;
    border-right: 1px solid rgba(167, 139, 250, 0.2) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small {
    color: #94a3b8 !important;
}
[data-testid="stSidebar"] .stMarkdown strong {
    color: #c4b5fd !important;
}
/* Section headers */
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p strong {
    color: #c4b5fd !important;
    font-size: 0.78rem !important;
    letter-spacing: 0.05em !important;
    text-transform: uppercase !important;
}
/* Expander headers */
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #60a5fa !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    background: rgba(255,255,255,0.03) !important;
    border-radius: 8px !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    background: rgba(96,165,250,0.08) !important;
    border-color: rgba(96,165,250,0.2) !important;
}
/* Caption / small text */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #64748b !important;
    font-size: 0.75rem !important;
}
/* Divider */
[data-testid="stSidebar"] hr {
    border-color: rgba(167,139,250,0.15) !important;
}
/* Dataset badge in sidebar */
[data-testid="stSidebar"] .stMarkdown div {
    color: #c4b5fd !important;
}

/* ── Sidebar toggle — always visible ── */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    background: rgba(167, 139, 250, 0.15) !important;
    border-radius: 0 8px 8px 0 !important;
    border: 1px solid rgba(167, 139, 250, 0.3) !important;
    border-left: none !important;
    color: #a78bfa !important;
}
[data-testid="collapsedControl"]:hover {
    background: rgba(167, 139, 250, 0.25) !important;
}

/* ── Animations ── */
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

/* ── Hero ── */
.hero-header {
    text-align: center;
    padding: 2rem 1rem 1.2rem;
    animation: fadeInDown 0.8s ease;
}
.hero-title {
    font-size: 2.8rem;
    font-weight: 700;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.4rem;
}
.hero-subtitle { font-size: 1rem; color: #94a3b8; font-weight: 300; }
.data-badge {
    display: inline-block;
    background: rgba(167,139,250,0.12);
    border: 1px solid rgba(167,139,250,0.25);
    border-radius: 20px;
    padding: 0.25rem 0.8rem;
    font-size: 0.75rem;
    color: #c4b5fd;
    margin-top: 0.6rem;
}

/* ── Input ── */
.stTextInput > div > div > input {
    background: #1e1e2e !important;
    border: 1.5px solid rgba(167, 139, 250, 0.4) !important;
    border-radius: 12px !important;
    color: #f1f5f9 !important;
    caret-color: #a78bfa !important;
    font-size: 1rem !important;
    padding: 0.75rem 1rem !important;
    transition: border-color 0.3s ease, box-shadow 0.3s ease !important;
}
.stTextInput > div > div > input:focus {
    border-color: #a78bfa !important;
    box-shadow: 0 0 0 3px rgba(167, 139, 250, 0.2) !important;
    background: #1e1e2e !important;
}
.stTextInput > div > div > input::placeholder { color: #475569 !important; }

/* ── Buttons ── */
.stButton > button {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(96, 165, 250, 0.3) !important;
    border-radius: 8px !important;
    color: #93c5fd !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    padding: 0.45rem 0.6rem !important;
    transition: all 0.25s ease !important;
    white-space: normal !important;
    text-align: center !important;
    line-height: 1.3 !important;
}
.stButton > button:hover {
    background: rgba(96, 165, 250, 0.15) !important;
    border-color: #60a5fa !important;
    color: #eff6ff !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 16px rgba(96, 165, 250, 0.2) !important;
}

/* ── Result cards — use st.container(border=True) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.04) !important;
    border: 1px solid rgba(255,255,255,0.09) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(10px) !important;
    animation: fadeInUp 0.5s ease !important;
}
.section-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 0.6rem;
}

/* ── Download button — dark themed ── */
[data-testid="stDownloadButton"] button {
    background: rgba(52, 211, 153, 0.08) !important;
    border: 1px solid rgba(52, 211, 153, 0.3) !important;
    color: #34d399 !important;
    border-radius: 8px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(52, 211, 153, 0.18) !important;
    border-color: #34d399 !important;
}

/* ── KPI cards ── */
.kpi-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 12px;
    padding: 1rem 1.2rem;
    text-align: center;
    animation: fadeInUp 0.5s ease;
}
.kpi-value { font-size: 1.6rem; font-weight: 700; color: #f1f5f9; }
.kpi-label { font-size: 0.75rem; color: #94a3b8; margin-top: 0.2rem; }

/* ── Guardrail cards ── */
.oos-card {
    background: rgba(239, 68, 68, 0.07);
    border: 1px solid rgba(239, 68, 68, 0.25);
    border-radius: 14px;
    padding: 2rem;
    text-align: center;
    animation: fadeInUp 0.5s ease;
}
.warn-card {
    background: rgba(245, 158, 11, 0.07);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 14px;
    padding: 2rem;
    text-align: center;
    animation: fadeInUp 0.5s ease;
}
.guardrail-icon { font-size: 2.5rem; margin-bottom: 0.8rem; }
.guardrail-title { font-size: 1.15rem; font-weight: 600; margin-bottom: 0.5rem; }
.oos-card  .guardrail-title { color: #fca5a5; }
.warn-card .guardrail-title { color: #fcd34d; }
.guardrail-body { font-size: 0.9rem; color: #94a3b8; margin-bottom: 1rem; line-height: 1.6; }
.guardrail-hint { font-size: 0.78rem; color: #475569; font-style: italic; }

/* ── Banners ── */
.truncation-banner {
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.3);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    font-size: 0.82rem;
    color: #fcd34d;
    margin-bottom: 0.8rem;
    animation: fadeIn 0.4s ease;
}
.config-error {
    background: rgba(239, 68, 68, 0.1);
    border: 1px solid rgba(239, 68, 68, 0.3);
    border-radius: 12px;
    padding: 1.5rem;
    animation: fadeIn 0.4s ease;
}
.config-error-title { font-size: 1rem; font-weight: 600; color: #fca5a5; margin-bottom: 0.5rem; }
.config-error-body  { font-size: 0.85rem; color: #94a3b8; font-family: monospace; }

/* ── Char counter ── */
.char-counter { font-size: 0.72rem; color: #475569; text-align: right; margin-top: 0.2rem; }
.char-counter.warn { color: #fcd34d; }

/* ── Try label ── */
.try-label {
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748b;
    margin-bottom: 0.5rem;
}

/* ── Misc ── */
.stCode, pre {
    border-radius: 10px !important;
    background: rgba(0,0,0,0.35) !important;
    border: 1px solid rgba(167,139,250,0.15) !important;
}
.stDataFrame { border-radius: 10px !important; overflow: hidden !important; animation: fadeIn 0.6s ease; }
.stSpinner > div { border-color: #a78bfa transparent transparent transparent !important; }
.stAlert { border-radius: 10px !important; animation: fadeIn 0.4s ease; }
.stSelectbox > div > div {
    background: rgba(255,255,255,0.05) !important;
    border: 1px solid rgba(167,139,250,0.3) !important;
    border-radius: 8px !important;
    color: #f1f5f9 !important;
}
hr { border-color: rgba(255,255,255,0.08) !important; margin: 1.5rem 0 !important; }

/* ── Header — fully transparent, no visible bar ── */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
}

/* Hide hamburger menu, deploy button, toolbar — keep sidebar toggle */
#MainMenu { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }

/* Style the sidebar toggle buttons (both collapse and expand) */
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button {
    background: rgba(167, 139, 250, 0.15) !important;
    border: 1px solid rgba(167, 139, 250, 0.35) !important;
    border-radius: 8px !important;
    color: #a78bfa !important;
    transition: background 0.2s ease !important;
}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="collapsedControl"] button:hover {
    background: rgba(167, 139, 250, 0.3) !important;
}

/* Force collapsed control to always be visible */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}

/* ── AI Insight card ── */
.insight-card {
    background: linear-gradient(135deg, rgba(167,139,250,0.08), rgba(96,165,250,0.06));
    border: 1px solid rgba(167,139,250,0.3);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    margin-bottom: 1.2rem;
    animation: fadeInUp 0.6s ease;
    backdrop-filter: blur(10px);
    position: relative;
    overflow: hidden;
}
.insight-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #a78bfa, #60a5fa, #34d399);
}
.insight-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #a78bfa;
    margin-bottom: 0.7rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}
.insight-text {
    font-size: 0.95rem;
    color: #e2e8f0;
    line-height: 1.75;
    font-weight: 400;
}

/* ── Typewriter animation ── */
@keyframes typewriter {
    from { width: 0; }
    to   { width: 100%; }
}
@keyframes blink { 50% { border-color: transparent; } }

/* ── Follow-up question buttons ── */
.followup-label {
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #64748b;
    margin: 0.8rem 0 0.5rem;
}
.stButton.followup-btn > button {
    background: rgba(96,165,250,0.06) !important;
    border: 1px solid rgba(96,165,250,0.25) !important;
    border-radius: 20px !important;
    color: #93c5fd !important;
    font-size: 0.78rem !important;
    padding: 0.35rem 0.9rem !important;
    white-space: normal !important;
    text-align: left !important;
    transition: all 0.2s ease !important;
}
.stButton.followup-btn > button:hover {
    background: rgba(96,165,250,0.15) !important;
    border-color: #60a5fa !important;
    color: #eff6ff !important;
    transform: translateX(4px) !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.2); }
::-webkit-scrollbar-thumb { background: rgba(167,139,250,0.4); border-radius: 3px; }
</style>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Data Play")
    st.caption("AI-powered NL query layer over Databricks Gold tables.")
    st.markdown(
        '<div style="background:rgba(167,139,250,0.1);border:1px solid rgba(167,139,250,0.25);'
        'border-radius:8px;padding:0.4rem 0.8rem;font-size:0.75rem;color:#c4b5fd;margin-bottom:0.5rem;">'
        'Dataset: Dec 2009 – Dec 2011</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("**Schema Explorer**")
    for table, meta in SCHEMA_SIDEBAR.items():
        icon = TABLE_ICONS.get(table, "📋")
        with st.expander(f"{icon} gold.{table}", expanded=False):
            st.caption(meta["desc"])
            for col_name, col_type, _ in meta["cols"]:
                badge_color = TYPE_BADGE.get(col_type, "#64748b")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(
                        f'<span style="background:{badge_color}22;color:{badge_color};'
                        f'font-size:0.6rem;font-weight:600;padding:0.1rem 0.35rem;'
                        f'border-radius:4px;">{col_type}</span>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f'<span style="font-size:0.75rem;color:#94a3b8;">{col_name}</span>',
                        unsafe_allow_html=True,
                    )

    st.divider()
    st.markdown("**Query History**")
    history = st.session_state.get("query_history", [])
    if not history:
        st.markdown(
            '<div style="text-align:center;padding:1rem 0.5rem;">'
            '<div style="font-size:1.5rem;margin-bottom:0.4rem;">🔍</div>'
            '<div style="font-size:0.75rem;color:#475569;">Run a query to see history</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for item in history:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.07);'
                f'border-radius:8px;padding:0.5rem 0.7rem;margin-bottom:0.4rem;">'
                f'<div style="font-size:0.75rem;color:#cbd5e1;">{item["question"]}</div>'
                f'<div style="font-size:0.65rem;color:#475569;margin-top:0.15rem;">'
                f'{item["time"]} · {item["rows"]} rows</div></div>',
                unsafe_allow_html=True,
            )


# ── .env validation ───────────────────────────────────────────────────────────
missing = missing_env_keys(REQUIRED_ENV)
if missing:
    st.markdown(f"""
    <div class="config-error">
        <div class="config-error-title">Configuration Error — App cannot start</div>
        <div class="config-error-body">
            Missing environment variables:<br><br>
            {"<br>".join(f"&nbsp;&nbsp;• {k}" for k in missing)}
            <br><br>Add them to <code>.env</code> and restart the app.
        </div>
    </div>
    """, unsafe_allow_html=True)
    st.stop()


# ── Sidebar toggle — injected via iframe so JS actually executes ──────────────
components.html("""
<script>
(function() {
    var doc = window.parent.document;

    // Remove any previous instance
    var old = doc.getElementById('dp-sidebar-btn');
    if (old) old.remove();

    // Create button directly in parent DOM
    var btn = doc.createElement('button');
    btn.id = 'dp-sidebar-btn';
    btn.title = 'Toggle sidebar';
    btn.innerHTML = '&#9776;';
    btn.style.cssText = [
        'position:fixed', 'top:0.6rem', 'left:0.7rem',
        'z-index:999999', 'width:2.2rem', 'height:2.2rem',
        'background:rgba(167,139,250,0.18)',
        'border:1px solid rgba(167,139,250,0.4)',
        'border-radius:8px', 'color:#a78bfa',
        'font-size:1.1rem', 'cursor:pointer',
        'display:flex', 'align-items:center', 'justify-content:center',
        'transition:background 0.2s ease', 'line-height:1'
    ].join(';');

    btn.onmouseenter = function() { this.style.background = 'rgba(167,139,250,0.35)'; };
    btn.onmouseleave = function() { this.style.background = 'rgba(167,139,250,0.18)'; };

    btn.onclick = function() {
        var selectors = [
            '[data-testid="collapsedControl"] button',
            '[data-testid="stSidebarCollapseButton"] button',
            'button[aria-label="Close sidebar"]',
            'button[aria-label="Open sidebar"]'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var b = doc.querySelector(selectors[i]);
            if (b) { b.click(); return; }
        }
        // Final fallback — directly toggle sidebar CSS
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (sb) {
            sb.style.display = (sb.style.display === 'none') ? 'flex' : 'none';
        }
    };

    doc.body.appendChild(btn);
})();
</script>
""", height=0)

# ── Hero — compact when a question is active, full when idle ──────────────────
active_question = st.session_state.get("last_question", "")

if not active_question:
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">Data Play</div>
        <div class="hero-subtitle">Ask questions about customers, revenue, segments & campaigns.</div>
        <div class="data-badge">Dataset: Dec 2009 – Dec 2011 &nbsp;·&nbsp; 4 Gold tables &nbsp;·&nbsp; ~525K transactions</div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div style="text-align:center;padding:0.6rem 0 0.2rem;">
        <span style="font-size:1.4rem;font-weight:700;background:linear-gradient(90deg,#a78bfa,#60a5fa,#34d399);
        -webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;">Data Play</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown("---")

# ── Input — transfer pending question BEFORE widget renders ───────────────────
# Both follow-up buttons and example buttons write to "pending_question"
# We move it to "question_input" here, before the widget is instantiated
if st.session_state.get("pending_question"):
    st.session_state["question_input"] = st.session_state.pop("pending_question")

question = st.text_input(
    label="question",
    placeholder="e.g. Show me top 10 customers by total spend",
    label_visibility="collapsed",
    max_chars=MAX_INPUT_LEN,
    key="question_input",
)

if question:
    warn_class = "warn" if (MAX_INPUT_LEN - len(question)) < 50 else ""
    st.markdown(
        f'<div class="char-counter {warn_class}">{len(question)}/{MAX_INPUT_LEN}</div>',
        unsafe_allow_html=True,
    )

st.markdown('<div class="try-label">✦ Try these examples</div>', unsafe_allow_html=True)
ex_cols = st.columns(len(EXAMPLES))
for i, example in enumerate(EXAMPLES):
    if ex_cols[i].button(example, use_container_width=True, key=f"ex_{i}"):
        st.session_state["pending_question"] = example
        st.rerun()

st.markdown("---")

# ── Query flow ────────────────────────────────────────────────────────────────
if not question:
    st.stop()

# G1 — Cooldown
if is_on_cooldown():
    wait = round(3 - (time.time() - st.session_state.get("last_query_time", 0)), 1)
    guardrail_card("warn", "⏳", "Slow down!", f"Please wait {wait}s before submitting another query.", "This prevents overloading the warehouse.")
    st.stop()

# G2 — Input validation
ok, error_type, error_msg = check_input(question)
if not ok:
    icon_map  = {"too_short": "✏️", "too_long": "📏", "gibberish": "🤔", "injection": "🚨"}
    title_map = {"too_short": "Question too short", "too_long": "Question too long", "gibberish": "Unrecognised input", "injection": "Suspicious input detected"}
    guardrail_card("oos", icon_map[error_type], title_map[error_type], error_msg)
    st.stop()

# G3 — Generate SQL + out-of-scope check
with st.spinner("Translating your question to SQL..."):
    try:
        sql_query, formats, oos_reason = generate_sql(question)
    except Exception as e:
        st.error(f"Failed to generate SQL: {e}")
        st.stop()

if oos_reason:
    guardrail_card("oos", "🔭", "That's outside my dataset", oos_reason, "Try asking about customers, revenue, loyalty tiers, segments, or campaign performance.")
    st.stop()

# G4 — SQL validation
try:
    validate_sql(sql_query)
except ValueError as e:
    guardrail_card("oos", "🚫", "Query blocked", str(e))
    st.stop()

# G5 — Enforce LIMIT
sql_query = enforce_limit(sql_query)

# ── Generated SQL ─────────────────────────────────────────────────────────────
with st.container(border=True):
    st.markdown('<div class="section-label">Generated SQL</div>', unsafe_allow_html=True)
    st.code(sql_query, language="sql", wrap_lines=True)

# ── Run query ─────────────────────────────────────────────────────────────────
with st.spinner("Fetching results from Databricks..."):
    try:
        st.session_state["last_query_time"] = time.time()
        df = run_query(sql_query)
    except Exception as e:
        guardrail_card("oos", "⚠️", "Query failed", str(e))
        st.stop()

if df.empty:
    st.info("Query returned no results.")
    st.stop()

add_to_history(question, len(df))
st.session_state["last_question"] = question

# G6 — Truncation warning
if len(df) >= RESULT_LIMIT:
    st.markdown(
        f'<div class="truncation-banner">⚠️ Results capped at {RESULT_LIMIT} rows — add filters to narrow down.</div>',
        unsafe_allow_html=True,
    )

# ── KPI row ───────────────────────────────────────────────────────────────────
numeric_cols     = df.select_dtypes(include="number").columns.tolist()
categorical_cols = df.select_dtypes(exclude="number").columns.tolist()

if numeric_cols and len(df) > 1:
    kpi_cols = st.columns(min(len(numeric_cols), 4))
    for i, col in enumerate(numeric_cols[:4]):
        with kpi_cols[i]:
            fmt_type = formats.get(col, "text")
            # Use mean for averages/rates/percents, sum for totals/counts
            if fmt_type in ("percent", "decimal") or any(
                x in col.lower() for x in ("avg", "rate", "pct", "score", "risk", "frequency")
            ):
                val       = df[col].mean()
                agg_label = "avg"
            else:
                val       = df[col].sum()
                agg_label = "total"
            fmt     = FORMAT_MAP.get(fmt_type)
            display = fmt.format(val) if fmt and fmt != "{}" else f"{val:,.0f}"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-value">{display}</div>
                <div class="kpi-label">{agg_label} {col.replace("_", " ")}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── Results table ─────────────────────────────────────────────────────────────
with st.container(border=True):
    label_col, dl_col = st.columns([3, 1])
    with label_col:
        st.markdown(f'<div class="section-label">Results — {len(df):,} rows</div>', unsafe_allow_html=True)
    with dl_col:
        st.download_button(
            label="⬇ Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"dataplay_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    # Auto-fit table height — no empty rows
    row_h      = 35
    header_h   = 38
    table_h    = min(450, header_h + row_h * len(df) + 4)
    try:
        st.dataframe(format_dataframe(df, formats), use_container_width=True, height=table_h)
    except Exception:
        st.dataframe(df, use_container_width=True, height=table_h)

# ── Chart ─────────────────────────────────────────────────────────────────────
if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
    with st.container(border=True):
        st.markdown('<div class="section-label">Chart</div>', unsafe_allow_html=True)
        chart_col = st.selectbox("Select metric to chart:", numeric_cols, key="chart_metric")
        st.bar_chart(df.set_index(categorical_cols[0])[[chart_col]], color="#a78bfa", use_container_width=True)

elif len(numeric_cols) >= 2:
    with st.container(border=True):
        st.markdown('<div class="section-label">Chart</div>', unsafe_allow_html=True)
        st.line_chart(df.set_index(df.columns[0])[numeric_cols[1:]], use_container_width=True)

# ── AI Insight + Follow-up Questions ──────────────────────────────────────────
with st.spinner("Generating insight..."):
    try:
        insight, followups = generate_insight(question, sql_query, df)
    except Exception:
        insight, followups = "", []

if insight:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-label">✦ AI Insight</div>
        <div class="insight-text">{insight}</div>
    </div>
    """, unsafe_allow_html=True)

if followups:
    st.markdown('<div class="followup-label">Ask a follow-up</div>', unsafe_allow_html=True)
    fu_cols = st.columns(len(followups))
    for i, fq in enumerate(followups):
        with fu_cols[i]:
            if st.button(f"→ {fq}", key=f"fu_{i}", use_container_width=True):
                st.session_state["pending_question"] = fq
                st.rerun()
