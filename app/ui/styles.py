"""Custom CSS styles for Streamlit UI."""

from __future__ import annotations

import streamlit as st

# Single <style> block: external <link> tags are often stripped by Streamlit markdown sanitization.
# Fonts load via @import inside CSS (more reliable).
_ORHEALTH_CSS: str = """
@import url("https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;800&display=swap");

:root {
    --bg-deep: #090a12;
    --bg-soft: #121420;
    --bg-card: #161a29;
    --accent-primary: #6D4C82;
    --accent-secondary: #E76F51;
    --text-main: #f2efe9;
    --text-soft: #cfcbc2;
    --text-stat: #C7B67B;
    --border-subtle: rgba(255, 255, 255, 0.08);
    /* Fixed bottom nav (light “pill” like reference apps) */
    --nav-bar-bg: #f7f7fa;
    --nav-bar-text: #4a4a55;
    --nav-bar-text-muted: #8b8b96;
}

html, body, [data-testid="stAppViewContainer"], .stApp {
    font-family: "Heebo", "Segoe UI", system-ui, sans-serif !important;
    background-color: var(--bg-deep) !important;
}

.stApp {
    background:
        radial-gradient(circle at 18% 10%, rgba(109, 76, 130, 0.14), transparent 34%),
        radial-gradient(circle at 80% 30%, rgba(231, 111, 81, 0.08), transparent 40%),
        repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,0.012) 0 1px, transparent 1px 3px),
        var(--bg-deep) !important;
    color: var(--text-main) !important;
    direction: rtl !important;
    text-align: right !important;
}

.stApp, .stMarkdown, p, label, .stCaption, span {
    color: var(--text-main);
    font-family: "Heebo", "Segoe UI", system-ui, sans-serif !important;
}

/* App-wide RTL: Streamlit often sets LTR on inner wrappers; override explicitly */
.stApp .block-container,
.stApp [data-testid="stVerticalBlock"],
.stApp [data-testid="column"],
.stApp .element-container {
    direction: rtl !important;
    text-align: right !important;
}

.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5, .stApp h6 {
    text-align: right !important;
    direction: rtl !important;
}

.stApp [data-testid="stMarkdownContainer"],
.stApp [data-testid="stMarkdownContainer"] p {
    text-align: right !important;
    direction: rtl !important;
}

.stApp [data-testid="stWidgetLabel"] label,
.stApp [data-testid="stWidgetLabel"] p {
    text-align: right !important;
    direction: rtl !important;
}

.stApp div[data-baseweb="input"] input,
.stApp div[data-baseweb="textarea"] textarea {
    text-align: right !important;
    direction: rtl !important;
}

.stApp [data-baseweb="select"] > div {
    text-align: right !important;
    direction: rtl !important;
}

.stApp [data-testid="stDataFrame"] {
    direction: rtl !important;
}

.stApp [data-testid="stExpander"] details summary,
.stApp [data-testid="stExpander"] [data-testid="stMarkdownContainer"] {
    text-align: right !important;
    direction: rtl !important;
}

/* Main app content: force right alignment (Streamlit defaults often stay LTR) */
section[data-testid="stMain"],
section[data-testid="stMain"] .block-container,
section[data-testid="stMain"] [data-testid="stVerticalBlock"],
section[data-testid="stMain"] [data-testid="column"],
section[data-testid="stMain"] .stMarkdown,
section[data-testid="stMain"] p,
section[data-testid="stMain"] label,
section[data-testid="stMain"] .stCaption,
section[data-testid="stMain"] [data-testid="stWidgetLabel"] {
    direction: rtl !important;
    text-align: right !important;
}

section[data-testid="stMain"] h1,
section[data-testid="stMain"] h2,
section[data-testid="stMain"] h3,
section[data-testid="stMain"] h4 {
    text-align: right !important;
}

section[data-testid="stMain"] div[data-baseweb="select"] > div,
section[data-testid="stMain"] div[data-baseweb="input"] > div {
    text-align: right !important;
    direction: rtl !important;
}

section[data-testid="stMain"] [data-testid="stMetricValue"],
section[data-testid="stMain"] [data-testid="stMetricLabel"] {
    text-align: right !important;
}

section[data-testid="stMain"] [data-testid="stAlertContent"] {
    text-align: right !important;
    direction: rtl !important;
}

section[data-testid="stMain"] [data-testid="stCaption"],
section[data-testid="stMain"] [data-testid="stHeading"] {
    text-align: right !important;
    direction: rtl !important;
}

section[data-testid="stMain"] [data-testid="stDataFrame"] {
    direction: rtl !important;
}

/* Keep button captions centered inside the control; surrounding copy stays RTL */
section[data-testid="stMain"] .stButton > button,
section[data-testid="stMain"] div.stButton > button[kind="secondaryFormSubmit"] {
    text-align: center !important;
    direction: rtl !important;
}

[data-testid="stHeader"] {
    background: rgba(9, 10, 18, 0.92) !important;
}

.title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: 0.15px;
    margin-bottom: 0.8rem;
    text-align: right;
    direction: rtl;
}

h1, h2, h3 {
    font-weight: 700 !important;
    text-align: right;
}

section[data-testid="stSidebar"],
button[data-testid="collapsedControl"] {
    display: none !important;
}

/*
 * Bottom tab bar lives in Streamlit’s bottom dock (st._bottom / st.bottom), which stays
 * pinned to the viewport. Style the bordered block only — avoid position:fixed here
 * because Streamlit’s main layout uses transforms and breaks fixed positioning.
 */
section[data-testid="stBottom"] {
    direction: rtl !important;
}

[data-testid="stVerticalBlockBorderWrapper"] {
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    margin-top: 0 !important;
    padding: 0.45rem 0.55rem calc(0.45rem + env(safe-area-inset-bottom, 0px)) !important;
    background: var(--nav-bar-bg) !important;
    border: none !important;
    border-top: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 22px 22px 0 0 !important;
    box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.28) !important;
    backdrop-filter: blur(12px);
}

section[data-testid="stBottom"] [data-testid="element-container"] {
    margin-bottom: 0.15rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] div[role="radiogroup"],
[data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
    width: 100% !important;
    gap: 0.2rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] div[role="radiogroup"] button,
[data-testid="stVerticalBlockBorderWrapper"] button {
    min-height: 40px !important;
    padding-left: 0.35rem !important;
    padding-right: 0.35rem !important;
}

@media (max-width: 640px) {
    [data-testid="stVerticalBlockBorderWrapper"] {
        padding: 0.3rem 0.3rem calc(0.3rem + env(safe-area-inset-bottom, 0px)) !important;
        border-radius: 14px 14px 0 0 !important;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.2) !important;
    }

    section[data-testid="stBottom"] [data-testid="element-container"] {
        margin-bottom: 0 !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] div[role="radiogroup"],
    [data-testid="stVerticalBlockBorderWrapper"] [data-testid="stHorizontalBlock"] {
        gap: 0.1rem !important;
        flex-wrap: nowrap !important;
    }

    [data-testid="stVerticalBlockBorderWrapper"] div[role="radiogroup"] button,
    [data-testid="stVerticalBlockBorderWrapper"] button {
        min-height: 32px !important;
        padding: 0.15rem 0.2rem !important;
        font-size: clamp(0.58rem, 3.1vw, 0.72rem) !important;
        font-weight: 600 !important;
        line-height: 1.1 !important;
    }
}

/* Keep Streamlit Cloud “Manage app” / toolbar above the fixed nav */
[data-testid="stDecoration"],
[data-testid="stToolbar"] {
    z-index: 1000000 !important;
}

.summary-card {
    border: 1px solid var(--border-subtle);
    border-radius: 16px;
    padding: 0.9rem 1rem;
    background: linear-gradient(180deg, #191d2d 0%, #131827 100%);
    box-shadow: 0 10px 28px rgba(0, 0, 0, 0.35);
    min-height: 120px;
    text-align: right;
    direction: rtl;
}

.summary-title {
    font-size: 0.9rem;
    color: var(--text-soft);
    margin-bottom: 0.35rem;
    font-weight: 500;
    text-align: right;
}

.summary-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-stat);
    line-height: 1;
    text-align: right;
}

.summary-icon {
    font-size: 1.5rem;
    float: right;
    margin-left: 0.5rem;
}

.entry-shell {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid var(--border-subtle);
    background: var(--bg-soft);
    box-shadow: 0 8px 20px rgba(0,0,0,0.28);
    text-align: right;
    direction: rtl;
}

div[data-testid="stDateInput"] > div,
div[data-testid="stSelectbox"] > div,
div[data-testid="stNumberInput"] > div {
    border-radius: 12px !important;
    border: 1px solid var(--border-subtle) !important;
    background: #1a1f2f !important;
}

div[data-testid="stDateInput"] input,
div[data-testid="stSelectbox"] input,
div[data-testid="stNumberInput"] input {
    color: var(--text-main) !important;
    font-weight: 500;
}

div[data-testid="stDateInput"] svg,
div[data-testid="stSelectbox"] svg {
    color: var(--accent-secondary) !important;
}

div[data-testid="stToggleSwitch"] > label p {
    font-weight: 500;
}

div[data-testid="stToggleSwitch"] div[role="switch"] {
    background-color: #2b3044 !important;
}

div[data-testid="stToggleSwitch"] div[aria-checked="true"] {
    background-color: var(--accent-primary) !important;
}

/* Form primary CTA (meal add) */
div.stButton > button[kind="secondaryFormSubmit"] {
    width: 100% !important;
    border-radius: 12px !important;
    background: var(--accent-primary) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #fff !important;
    font-weight: 700 !important;
    min-height: 46px !important;
    transition: filter 0.2s ease !important;
}

div.stButton > button[kind="secondaryFormSubmit"]:hover {
    filter: brightness(1.08) !important;
}

"""


def inject_global_styles() -> None:
    """Inject global CSS in a way Streamlit reliably applies (single style block)."""
    compact: str = " ".join(_ORHEALTH_CSS.split())
    st.markdown(f"<style>{compact}</style>", unsafe_allow_html=True)
