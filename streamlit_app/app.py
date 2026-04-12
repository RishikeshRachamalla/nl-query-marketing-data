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
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* ─── Base — body holds the bg so orbs show through transparent stApp ─── */
body { background: #05050f !important; }
.stApp { background: transparent !important; min-height: 100vh; }
/* Ensure main content blocks sit above the fixed orbs */
[data-testid="stAppViewContainer"] { position: relative; z-index: 1; }
[data-testid="stSidebar"] { position: relative; z-index: 2 !important; }

/* ─── Keyframes ─── */
@keyframes gradientShift {
    0%   { background-position: 0% 50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0% 50%; }
}
@keyframes fadeInDown {
    from { opacity: 0; transform: translateY(-28px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(24px); }
    to   { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleIn {
    from { opacity: 0; transform: scale(0.96); }
    to   { opacity: 1; transform: scale(1); }
}
@keyframes blink {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0; }
}
@keyframes shimmerSlide {
    0%   { transform: translateX(-350%); }
    100% { transform: translateX(600%); }
}
@keyframes floatUp {
    0%, 100% { transform: translateY(0); }
    50%       { transform: translateY(-6px); }
}
@keyframes pulseGlow {
    0%, 100% { box-shadow: 0 0 0 0 rgba(99,102,241,0.3); }
    50%       { box-shadow: 0 0 0 8px rgba(99,102,241,0); }
}
@keyframes inputPulse {
    0%, 100% { box-shadow: 0 0 0 1px rgba(99,102,241,0.12), 0 2px 16px rgba(0,0,0,0.4); }
    50%       { box-shadow: 0 0 0 1px rgba(99,102,241,0.22), 0 2px 24px rgba(99,102,241,0.08); }
}

/* ─── Sidebar ─── */
[data-testid="stSidebar"] {
    background: rgba(4, 4, 18, 0.98) !important;
    border-right: 1px solid rgba(99,102,241,0.15) !important;
    backdrop-filter: blur(24px) !important;
}
[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: #e2e8f0 !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
}
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] small { color: #64748b !important; }
[data-testid="stSidebar"] .stMarkdown strong { color: #818cf8 !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p strong {
    color: #6366f1 !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary {
    color: #94a3b8 !important;
    font-size: 0.82rem !important;
    font-weight: 500 !important;
    background: rgba(255,255,255,0.02) !important;
    border-radius: 10px !important;
    border: 1px solid rgba(255,255,255,0.05) !important;
    transition: all 0.22s ease !important;
}
[data-testid="stSidebar"] [data-testid="stExpander"] summary:hover {
    background: rgba(99,102,241,0.07) !important;
    border-color: rgba(99,102,241,0.22) !important;
    color: #c7d2fe !important;
    padding-left: 1rem !important;
}
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
    color: #334155 !important;
    font-size: 0.72rem !important;
}
[data-testid="stSidebar"] hr { border-color: rgba(99,102,241,0.1) !important; }

/* Sidebar toggle */
[data-testid="collapsedControl"] {
    display: flex !important;
    visibility: visible !important;
    opacity: 1 !important;
    z-index: 999999 !important;
}
[data-testid="stSidebarCollapseButton"] button,
[data-testid="collapsedControl"] button {
    background: rgba(99,102,241,0.1) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 8px !important;
    color: #818cf8 !important;
    transition: all 0.2s ease !important;
}
[data-testid="stSidebarCollapseButton"] button:hover,
[data-testid="collapsedControl"] button:hover {
    background: rgba(99,102,241,0.22) !important;
    transform: scale(1.08) !important;
}

/* ─── Hero — full ─── */
.hero-wrap {
    text-align: center;
    padding: 4rem 1rem 2.5rem;
    animation: fadeInDown 0.9s cubic-bezier(0.16, 1, 0.3, 1);
}
.hero-eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    background: rgba(99,102,241,0.08);
    border: 1px solid rgba(99,102,241,0.2);
    border-radius: 100px;
    padding: 0.35rem 1.1rem;
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #818cf8;
    margin-bottom: 1.8rem;
}
.hero-eyebrow-dot {
    width: 6px; height: 6px;
    background: #6366f1;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(99,102,241,0.8);
    animation: blink 2s ease infinite;
}
.hero-title {
    font-size: 4.5rem;
    font-weight: 900;
    line-height: 1.05;
    letter-spacing: -0.03em;
    /* Indigo → Blue → Cyan → Emerald — NO pink */
    background: linear-gradient(135deg,
        #a5b4fc 0%,
        #6366f1 18%,
        #38bdf8 38%,
        #06b6d4 55%,
        #10b981 72%,
        #6366f1 88%,
        #a5b4fc 100%
    );
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 6s linear infinite;
    margin-bottom: 1.2rem;
}
.hero-subtitle {
    font-size: 1.1rem;
    color: #94a3b8;
    font-weight: 400;
    max-width: 500px;
    margin: 0 auto 2.4rem;
    line-height: 1.7;
}
.hero-stats {
    display: flex;
    justify-content: center;
    gap: 0.9rem;
    flex-wrap: wrap;
    animation: fadeInUp 1s ease 0.3s both;
}
.stat-pill {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.45rem 1.1rem;
    border-radius: 100px;
    font-size: 0.8rem;
    font-weight: 500;
    backdrop-filter: blur(12px);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
    letter-spacing: 0.01em;
}
.stat-pill:hover {
    transform: translateY(-3px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.3);
}
.stat-pill.indigo {
    background: rgba(99,102,241,0.1);
    border: 1px solid rgba(99,102,241,0.22);
    color: #c7d2fe;
}
.stat-pill.cyan {
    background: rgba(6,182,212,0.1);
    border: 1px solid rgba(6,182,212,0.22);
    color: #a5f3fc;
}
.stat-pill.emerald {
    background: rgba(16,185,129,0.1);
    border: 1px solid rgba(16,185,129,0.22);
    color: #6ee7b7;
}

/* ─── Hero — compact ─── */
.hero-compact {
    text-align: center;
    padding: 1rem 0 0.4rem;
    animation: fadeIn 0.4s ease;
}
.hero-compact-title {
    font-size: 1.7rem;
    font-weight: 900;
    letter-spacing: -0.025em;
    background: linear-gradient(135deg, #a5b4fc, #6366f1, #38bdf8, #06b6d4, #10b981);
    background-size: 300% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    animation: gradientShift 6s linear infinite;
}

/* ─── Divider ─── */
.dp-divider {
    height: 1px;
    background: linear-gradient(90deg,
        transparent,
        rgba(99,102,241,0.3),
        rgba(6,182,212,0.25),
        rgba(16,185,129,0.15),
        transparent);
    border: none;
    margin: 1.8rem 0;
}

/* ─── Input — glows even at rest ─── */
.stTextInput > div > div > input {
    background: rgba(10, 10, 28, 0.9) !important;
    border: 1.5px solid rgba(99,102,241,0.28) !important;
    border-radius: 14px !important;
    color: #e2e8f0 !important;
    caret-color: #6366f1 !important;
    font-size: 1.05rem !important;
    padding: 0.95rem 1.3rem !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    backdrop-filter: blur(12px) !important;
    animation: inputPulse 4s ease-in-out infinite !important;
}
.stTextInput > div > div > input:focus {
    border-color: #6366f1 !important;
    background: rgba(15, 15, 38, 0.98) !important;
    box-shadow:
        0 0 0 3px rgba(99,102,241,0.18),
        0 0 40px rgba(99,102,241,0.15),
        0 4px 24px rgba(0,0,0,0.5) !important;
    animation: none !important;
}
.stTextInput > div > div > input::placeholder { color: #334155 !important; }

/* ─── Buttons ─── */
.stButton > button {
    background: rgba(99,102,241,0.06) !important;
    border: 1px solid rgba(99,102,241,0.2) !important;
    border-radius: 100px !important;
    color: #a5b4fc !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    padding: 0.48rem 0.9rem !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    white-space: normal !important;
    text-align: center !important;
    line-height: 1.35 !important;
}
.stButton > button:hover {
    background: rgba(99,102,241,0.15) !important;
    border-color: rgba(99,102,241,0.45) !important;
    color: #e0e7ff !important;
    transform: translateY(-2px) scale(1.02) !important;
    box-shadow: 0 6px 24px rgba(99,102,241,0.2) !important;
}
.stButton > button:active {
    transform: translateY(0) scale(0.98) !important;
}

/* ─── Glass cards ─── */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255,255,255,0.02) !important;
    border: 1px solid rgba(255,255,255,0.06) !important;
    border-radius: 18px !important;
    backdrop-filter: blur(24px) !important;
    -webkit-backdrop-filter: blur(24px) !important;
    transition: border-color 0.3s ease, box-shadow 0.35s ease !important;
    animation: scaleIn 0.45s cubic-bezier(0.16, 1, 0.3, 1) !important;
}
[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(99,102,241,0.18) !important;
    box-shadow: 0 12px 40px rgba(0,0,0,0.4) !important;
}

/* ─── Section labels ─── */
.section-label {
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #6366f1;
    margin-bottom: 0.9rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}
.section-label::before {
    content: '';
    display: inline-block;
    width: 3px; height: 13px;
    background: linear-gradient(180deg, #6366f1, #06b6d4);
    border-radius: 2px;
    flex-shrink: 0;
}

/* ─── KPI cards ─── */
.kpi-card {
    background: rgba(255,255,255,0.025);
    border: 1px solid rgba(255,255,255,0.06);
    border-radius: 18px;
    padding: 1.5rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    animation: fadeInUp 0.5s ease both;
    backdrop-filter: blur(12px);
}
/* Indigo → cyan → emerald top bar */
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg, #6366f1, #06b6d4, #10b981);
    background-size: 200% auto;
    animation: gradientShift 4s linear infinite;
}
/* Shimmer sweep */
.kpi-card::after {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 35%; height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255,255,255,0.035), transparent);
    animation: shimmerSlide 5s ease-in-out infinite;
}
.kpi-card:hover {
    border-color: rgba(99,102,241,0.25);
    transform: translateY(-6px);
    box-shadow:
        0 20px 50px rgba(0,0,0,0.5),
        0 0 30px rgba(99,102,241,0.08);
}
/* Value: indigo → cyan gradient text */
.kpi-value {
    font-size: 2rem;
    font-weight: 800;
    letter-spacing: -0.025em;
    background: linear-gradient(135deg, #c7d2fe, #38bdf8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    line-height: 1;
    margin-bottom: 0.5rem;
}
.kpi-label {
    font-size: 0.7rem;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-weight: 600;
}

/* ─── Download button ─── */
[data-testid="stDownloadButton"] button {
    background: rgba(16,185,129,0.07) !important;
    border: 1px solid rgba(16,185,129,0.2) !important;
    color: #6ee7b7 !important;
    border-radius: 100px !important;
    font-size: 0.78rem !important;
    font-weight: 500 !important;
    transition: all 0.25s ease !important;
}
[data-testid="stDownloadButton"] button:hover {
    background: rgba(16,185,129,0.14) !important;
    border-color: rgba(16,185,129,0.4) !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(16,185,129,0.12) !important;
}

/* ─── Guardrail cards ─── */
.oos-card {
    background: rgba(239,68,68,0.04);
    border: 1px solid rgba(239,68,68,0.16);
    border-radius: 18px;
    padding: 2.8rem 2rem;
    text-align: center;
    animation: scaleIn 0.45s ease;
    backdrop-filter: blur(12px);
}
.warn-card {
    background: rgba(245,158,11,0.04);
    border: 1px solid rgba(245,158,11,0.16);
    border-radius: 18px;
    padding: 2.8rem 2rem;
    text-align: center;
    animation: scaleIn 0.45s ease;
    backdrop-filter: blur(12px);
}
.guardrail-icon {
    font-size: 3.2rem;
    margin-bottom: 1rem;
    display: block;
    animation: floatUp 3s ease-in-out infinite;
}
.guardrail-title { font-size: 1.2rem; font-weight: 700; margin-bottom: 0.6rem; }
.oos-card  .guardrail-title { color: #fca5a5; }
.warn-card .guardrail-title { color: #fcd34d; }
.guardrail-body { font-size: 0.9rem; color: #475569; margin-bottom: 1rem; line-height: 1.7; }
.guardrail-hint { font-size: 0.78rem; color: #334155; font-style: italic; }

/* ─── AI Insight card ─── */
.insight-card {
    position: relative;
    background: rgba(10, 10, 28, 0.75);
    border-radius: 18px;
    padding: 1.9rem;
    margin-bottom: 1.2rem;
    overflow: hidden;
    animation: fadeInUp 0.65s cubic-bezier(0.16, 1, 0.3, 1);
    backdrop-filter: blur(24px);
    border: 1px solid rgba(99,102,241,0.16);
}
/* Animated indigo → cyan → emerald top border */
.insight-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
    background: linear-gradient(90deg,
        #6366f1, #38bdf8, #06b6d4, #10b981, #6366f1
    );
    background-size: 300% auto;
    animation: gradientShift 4s linear infinite;
}
.insight-card::after {
    content: '';
    position: absolute;
    inset: 0;
    background: radial-gradient(ellipse at top left, rgba(99,102,241,0.05), transparent 55%);
    pointer-events: none;
}
.insight-header {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    margin-bottom: 1rem;
}
.insight-label {
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.14em;
    text-transform: uppercase;
    color: #818cf8;
}
.insight-pulse {
    width: 7px; height: 7px;
    background: #6366f1;
    border-radius: 50%;
    box-shadow: 0 0 8px rgba(99,102,241,0.8);
    animation: blink 2s ease infinite;
    flex-shrink: 0;
}
.insight-text {
    font-size: 0.96rem;
    color: #cbd5e1;
    line-height: 1.85;
    font-weight: 400;
    position: relative;
    z-index: 1;
}

/* ─── Follow-up ─── */
.followup-label {
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1e293b;
    margin-bottom: 0.6rem;
    margin-top: 0.2rem;
}

/* ─── Banners ─── */
.truncation-banner {
    background: rgba(245,158,11,0.07);
    border: 1px solid rgba(245,158,11,0.2);
    border-radius: 10px;
    padding: 0.65rem 1.1rem;
    font-size: 0.82rem;
    color: #fbbf24;
    margin-bottom: 0.8rem;
    animation: fadeIn 0.4s ease;
}
.config-error {
    background: rgba(239,68,68,0.05);
    border: 1px solid rgba(239,68,68,0.2);
    border-radius: 16px;
    padding: 2rem;
    animation: fadeIn 0.4s ease;
}
.config-error-title { font-size: 1.05rem; font-weight: 700; color: #fca5a5; margin-bottom: 0.6rem; }
.config-error-body  { font-size: 0.85rem; color: #475569; font-family: monospace; line-height: 1.75; }

/* ─── Char counter ─── */
.char-counter { font-size: 0.7rem; color: #1e293b; text-align: right; margin-top: 0.25rem; }
.char-counter.warn { color: #fbbf24; }

/* ─── Try label ─── */
.try-label {
    font-size: 0.66rem;
    font-weight: 700;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    color: #1e293b;
    margin-bottom: 0.6rem;
    display: flex;
    align-items: center;
    gap: 0.4rem;
}

/* ─── Code ─── */
.stCode, pre {
    border-radius: 12px !important;
    background: rgba(0,0,0,0.5) !important;
    border: 1px solid rgba(99,102,241,0.12) !important;
}

/* ─── Misc ─── */
.stDataFrame { border-radius: 12px !important; overflow: hidden !important; animation: fadeIn 0.5s ease; }
.stSpinner > div {
    border-top-color: #6366f1 !important;
    border-right-color: transparent !important;
    border-bottom-color: transparent !important;
    border-left-color: transparent !important;
}
.stAlert { border-radius: 12px !important; animation: fadeIn 0.4s ease; }
.stSelectbox > div > div {
    background: rgba(10,10,28,0.85) !important;
    border: 1px solid rgba(99,102,241,0.25) !important;
    border-radius: 10px !important;
    color: #f1f5f9 !important;
}
::-webkit-scrollbar { width: 5px; height: 5px; }
::-webkit-scrollbar-track { background: rgba(0,0,0,0.3); }
::-webkit-scrollbar-thumb { background: rgba(99,102,241,0.3); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: rgba(99,102,241,0.5); }

/* ─── Hide chrome ─── */
header[data-testid="stHeader"] {
    background: transparent !important;
    border-bottom: none !important;
    box-shadow: none !important;
}
#MainMenu { display: none !important; }
footer { visibility: hidden !important; }
[data-testid="stToolbar"] { display: none !important; }
.stDeployButton { display: none !important; }
hr { border: none !important; }
</style>
""", unsafe_allow_html=True)


# ── Inject orbs + sidebar toggle ──────────────────────────────────────────────
components.html("""
<script>
(function() {
    var doc = window.parent.document;

    /* remove old */
    ['dp-orb-1','dp-orb-2','dp-orb-3','dp-orb-styles','dp-sidebar-btn'].forEach(function(id) {
        var el = doc.getElementById(id); if (el) el.remove();
    });

    /* orb keyframes */
    var style = doc.createElement('style');
    style.id = 'dp-orb-styles';
    style.textContent =
        '@keyframes dpF1{0%,100%{transform:translate(0,0) scale(1);opacity:.8;}' +
        '33%{transform:translate(50px,-60px) scale(1.08);opacity:1;}' +
        '66%{transform:translate(-35px,40px) scale(0.93);opacity:.6;}}' +
        '@keyframes dpF2{0%,100%{transform:translate(0,0) scale(1);opacity:.6;}' +
        '33%{transform:translate(-55px,50px) scale(1.06);opacity:.8;}' +
        '66%{transform:translate(40px,-30px) scale(0.94);opacity:.45;}}' +
        '@keyframes dpF3{0%,100%{transform:translate(0,0);opacity:.45;}' +
        '50%{transform:translate(28px,-40px);opacity:.65;}}';
    doc.head.appendChild(style);

    /* orbs: indigo / cyan / emerald — higher opacity so they punch through */
    var orbs = [
        {id:'dp-orb-1', top:'-120px', left:'-120px',     w:'800px', h:'800px',
         color:'rgba(99,102,241,0.22)',  anim:'dpF1 16s ease-in-out infinite'},
        {id:'dp-orb-2', bottom:'-120px', right:'-120px', w:'680px', h:'680px',
         color:'rgba(6,182,212,0.17)',   anim:'dpF2 20s ease-in-out infinite'},
        {id:'dp-orb-3', top:'32%', right:'4%',            w:'440px', h:'440px',
         color:'rgba(16,185,129,0.13)',  anim:'dpF3 26s ease-in-out infinite'},
    ];
    orbs.forEach(function(o) {
        var d = doc.createElement('div');
        d.id = o.id;
        var s = 'position:fixed;border-radius:50%;filter:blur(72px);pointer-events:none;z-index:0;';
        s += 'width:'+o.w+';height:'+o.h+';';
        s += 'background:radial-gradient(circle,'+o.color+',transparent 70%);';
        s += 'animation:'+o.anim+';';
        if (o.top)    s += 'top:'+o.top+';';
        if (o.bottom) s += 'bottom:'+o.bottom+';';
        if (o.left)   s += 'left:'+o.left+';';
        if (o.right)  s += 'right:'+o.right+';';
        d.style.cssText = s;
        doc.body.appendChild(d);
    });

    /* sidebar toggle */
    var btn = doc.createElement('button');
    btn.id = 'dp-sidebar-btn';
    btn.title = 'Toggle sidebar';
    btn.innerHTML = '&#9776;';
    btn.style.cssText = [
        'position:fixed','top:0.7rem','left:0.8rem','z-index:999999',
        'width:2.2rem','height:2.2rem',
        'background:rgba(99,102,241,0.12)',
        'border:1px solid rgba(99,102,241,0.28)',
        'border-radius:8px','color:#818cf8','font-size:1.1rem',
        'cursor:pointer','display:flex','align-items:center','justify-content:center',
        'transition:all 0.2s ease','line-height:1'
    ].join(';');
    btn.onmouseenter = function() {
        this.style.background = 'rgba(99,102,241,0.25)';
        this.style.transform = 'scale(1.08)';
    };
    btn.onmouseleave = function() {
        this.style.background = 'rgba(99,102,241,0.12)';
        this.style.transform = 'scale(1)';
    };
    btn.onclick = function() {
        var sels = [
            '[data-testid="collapsedControl"] button',
            '[data-testid="stSidebarCollapseButton"] button',
            'button[aria-label="Close sidebar"]',
            'button[aria-label="Open sidebar"]'
        ];
        for (var i = 0; i < sels.length; i++) {
            var b = doc.querySelector(sels[i]);
            if (b) { b.click(); return; }
        }
        var sb = doc.querySelector('[data-testid="stSidebar"]');
        if (sb) sb.style.display = (sb.style.display === 'none') ? 'flex' : 'none';
    };
    doc.body.appendChild(btn);
})();
</script>
""", height=0)


# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### Data Play")
    st.caption("AI-powered NL query layer over Databricks Gold tables.")
    st.markdown(
        '<div style="background:rgba(99,102,241,0.08);border:1px solid rgba(99,102,241,0.18);'
        'border-radius:10px;padding:0.42rem 0.9rem;font-size:0.73rem;color:#818cf8;'
        'margin-bottom:0.4rem;letter-spacing:0.02em;">'
        'Dec 2009 – Dec 2011</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("**Schema Explorer**")
    for table, meta in SCHEMA_SIDEBAR.items():
        icon = TABLE_ICONS.get(table, "")
        with st.expander(f"{icon}  gold.{table}", expanded=False):
            st.caption(meta["desc"])
            for col_name, col_type, _ in meta["cols"]:
                badge_color = TYPE_BADGE.get(col_type, "#64748b")
                c1, c2 = st.columns([1, 2])
                with c1:
                    st.markdown(
                        f'<span style="background:{badge_color}15;color:{badge_color};'
                        f'font-size:0.58rem;font-weight:700;padding:0.12rem 0.38rem;'
                        f'border-radius:4px;letter-spacing:0.04em;">{col_type}</span>',
                        unsafe_allow_html=True,
                    )
                with c2:
                    st.markdown(
                        f'<span style="font-size:0.74rem;color:#475569;">{col_name}</span>',
                        unsafe_allow_html=True,
                    )

    st.divider()
    st.markdown("**Query History**")
    history = st.session_state.get("query_history", [])
    if not history:
        st.markdown(
            '<div style="text-align:center;padding:1.2rem 0.5rem;">'
            '<div style="font-size:1.6rem;margin-bottom:0.5rem;opacity:0.3;">&#128269;</div>'
            '<div style="font-size:0.73rem;color:#1e293b;">No queries yet</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    else:
        for item in history:
            st.markdown(
                f'<div style="background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);'
                f'border-radius:10px;padding:0.55rem 0.75rem;margin-bottom:0.4rem;">'
                f'<div style="font-size:0.74rem;color:#94a3b8;line-height:1.4;">{item["question"]}</div>'
                f'<div style="font-size:0.63rem;color:#334155;margin-top:0.2rem;">'
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


# ── Hero ──────────────────────────────────────────────────────────────────────
active_question = st.session_state.get("last_question", "")

if not active_question:
    st.markdown("""
    <div class="hero-wrap">
        <div class="hero-eyebrow">
            <span class="hero-eyebrow-dot"></span>
            AI-Powered Marketing Analytics
        </div>
        <div class="hero-title">Data Play</div>
        <div class="hero-subtitle">
            Ask questions in plain English — Claude writes the SQL,
            Databricks runs it, you see results instantly.
        </div>
        <div class="hero-stats">
            <span class="stat-pill indigo">4 Gold Tables</span>
            <span class="stat-pill cyan">525K Transactions</span>
            <span class="stat-pill emerald">Claude AI Insights</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
    <div class="hero-compact">
        <span class="hero-compact-title">Data Play</span>
    </div>
    """, unsafe_allow_html=True)

st.markdown('<div class="dp-divider"></div>', unsafe_allow_html=True)


# ── Input ─────────────────────────────────────────────────────────────────────
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

st.markdown('<div class="try-label">&#10022; &nbsp;Try these</div>', unsafe_allow_html=True)
ex_cols = st.columns(len(EXAMPLES))
for i, example in enumerate(EXAMPLES):
    if ex_cols[i].button(example, use_container_width=True, key=f"ex_{i}"):
        st.session_state["pending_question"] = example
        st.rerun()

st.markdown('<div class="dp-divider"></div>', unsafe_allow_html=True)


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
    title_map = {"too_short": "Question too short", "too_long": "Question too long",
                 "gibberish": "Unrecognised input", "injection": "Suspicious input detected"}
    guardrail_card("oos", icon_map[error_type], title_map[error_type], error_msg)
    st.stop()

# G3 — Generate SQL
with st.spinner("Translating your question to SQL..."):
    try:
        sql_query, formats, oos_reason = generate_sql(question)
    except Exception as e:
        st.error(f"Failed to generate SQL: {e}")
        st.stop()

if oos_reason:
    guardrail_card("oos", "🔭", "That's outside my dataset", oos_reason,
                   "Try asking about customers, revenue, loyalty tiers, segments, or campaign performance.")
    st.stop()

# G4 — SQL validation
try:
    validate_sql(sql_query)
except ValueError as e:
    guardrail_card("oos", "🚫", "Query blocked", str(e))
    st.stop()

# G5 — Enforce LIMIT
sql_query = enforce_limit(sql_query)

# ── SQL display ───────────────────────────────────────────────────────────────
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
        f'<div class="truncation-banner">Results capped at {RESULT_LIMIT} rows — add filters to narrow down.</div>',
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
            <div class="kpi-card" style="animation-delay:{i * 0.08}s;">
                <div class="kpi-value">{display}</div>
                <div class="kpi-label">{agg_label}&nbsp;{col.replace("_", " ")}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

# ── Results table ─────────────────────────────────────────────────────────────
with st.container(border=True):
    label_col, dl_col = st.columns([3, 1])
    with label_col:
        st.markdown(
            f'<div class="section-label">Results &nbsp;·&nbsp; {len(df):,} rows</div>',
            unsafe_allow_html=True,
        )
    with dl_col:
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name=f"dataplay_{time.strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
    row_h   = 35
    header_h = 38
    table_h = min(450, header_h + row_h * len(df) + 4)
    try:
        st.dataframe(format_dataframe(df, formats), use_container_width=True, height=table_h)
    except Exception:
        st.dataframe(df, use_container_width=True, height=table_h)

# ── Chart ─────────────────────────────────────────────────────────────────────
if len(numeric_cols) >= 1 and len(categorical_cols) >= 1:
    with st.container(border=True):
        st.markdown('<div class="section-label">Chart</div>', unsafe_allow_html=True)
        chart_col = st.selectbox("Select metric to chart:", numeric_cols, key="chart_metric")
        st.bar_chart(
            df.set_index(categorical_cols[0])[[chart_col]],
            color="#6366f1",
            use_container_width=True,
        )
elif len(numeric_cols) >= 2:
    with st.container(border=True):
        st.markdown('<div class="section-label">Chart</div>', unsafe_allow_html=True)
        st.line_chart(df.set_index(df.columns[0])[numeric_cols[1:]], use_container_width=True)

# ── AI Insight + Follow-ups ───────────────────────────────────────────────────
with st.spinner("Generating insight..."):
    try:
        insight, followups = generate_insight(question, sql_query, df)
    except Exception:
        insight, followups = "", []

if insight:
    st.markdown(f"""
    <div class="insight-card">
        <div class="insight-header">
            <span class="insight-pulse"></span>
            <span class="insight-label">AI Insight</span>
        </div>
        <div class="insight-text">{insight}</div>
    </div>
    """, unsafe_allow_html=True)

if followups:
    st.markdown('<div class="followup-label">Ask a follow-up</div>', unsafe_allow_html=True)
    fu_cols = st.columns(len(followups))
    for i, fq in enumerate(followups):
        with fu_cols[i]:
            if st.button(f"-> {fq}", key=f"fu_{i}", use_container_width=True):
                st.session_state["pending_question"] = fq
                st.rerun()
