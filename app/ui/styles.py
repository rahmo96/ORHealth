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
    direction: rtl;
}

.stApp, .stMarkdown, p, label, .stCaption, span {
    color: var(--text-main);
    font-family: "Heebo", "Segoe UI", system-ui, sans-serif !important;
}

[data-testid="stHeader"] {
    background: rgba(9, 10, 18, 0.92) !important;
}

.title {
    font-size: 2.2rem;
    font-weight: 800;
    letter-spacing: 0.15px;
    margin-bottom: 0.8rem;
}

h1, h2, h3 {
    font-weight: 700 !important;
}

section[data-testid="stSidebar"],
button[data-testid="collapsedControl"] {
    display: none !important;
}

/* Room for fixed bottom nav so last content is not hidden behind the bar */
section[data-testid="stMain"] {
    padding-bottom: calc(5.75rem + env(safe-area-inset-bottom, 0px)) !important;
}

/*
 * Fixed bottom navigation (only use st.container(border=True) for this bar in the app).
 * Matches “sticky” mobile tab bars: full width, rounded top corners, sits above content.
 */
[data-testid="stVerticalBlockBorderWrapper"] {
    position: fixed !important;
    left: 0 !important;
    right: 0 !important;
    bottom: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    margin: 0 !important;
    margin-top: 0 !important;
    z-index: 999990 !important;
    padding: 0.65rem 0.75rem calc(0.65rem + env(safe-area-inset-bottom, 0px)) !important;
    background: var(--nav-bar-bg) !important;
    border: none !important;
    border-top: 1px solid rgba(0, 0, 0, 0.06) !important;
    border-radius: 22px 22px 0 0 !important;
    box-shadow: 0 -10px 40px rgba(0, 0, 0, 0.28) !important;
    backdrop-filter: blur(12px);
}

[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] {
    text-align: center;
}

.bottom-nav-icon {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-bottom: 0.15rem;
    color: var(--nav-bar-text-muted);
}

[data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"]:has(button[kind="primary"]) .bottom-nav-icon {
    color: var(--accent-primary);
}

/* Active tab: filled accent */
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="primary"],
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[data-testid="baseButton-primary"] {
    background: var(--accent-primary) !important;
    color: #fff !important;
    font-weight: 700 !important;
    min-height: 40px !important;
    font-size: 0.82rem !important;
    border: none !important;
    box-shadow: 0 2px 8px rgba(109, 76, 130, 0.35) !important;
}

/* Inactive tabs: light ghost buttons on white bar */
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"],
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[data-testid="baseButton-secondary"] {
    background: transparent !important;
    color: var(--nav-bar-text) !important;
    border: 1px solid transparent !important;
    font-weight: 600 !important;
    min-height: 40px !important;
    font-size: 0.82rem !important;
}

[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"]:hover,
[data-testid="stVerticalBlockBorderWrapper"] .stButton > button[data-testid="baseButton-secondary"]:hover {
    background: rgba(109, 76, 130, 0.08) !important;
    color: var(--accent-primary) !important;
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
}

.summary-title {
    font-size: 0.9rem;
    color: var(--text-soft);
    margin-bottom: 0.35rem;
    font-weight: 500;
}

.summary-value {
    font-size: 2rem;
    font-weight: 800;
    color: var(--text-stat);
    line-height: 1;
}

.summary-icon {
    font-size: 1.5rem;
    float: left;
}

.entry-shell {
    margin-top: 1rem;
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid var(--border-subtle);
    background: var(--bg-soft);
    box-shadow: 0 8px 20px rgba(0,0,0,0.28);
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

.footer-meta {
    margin-top: 1.5rem;
    text-align: left;
    color: #9a9cab;
    font-size: 0.72rem;
}
"""


def inject_global_styles() -> None:
    """Inject global CSS in a way Streamlit reliably applies (single style block)."""
    compact: str = " ".join(_ORHEALTH_CSS.split())
    st.markdown(f"<style>{compact}</style>", unsafe_allow_html=True)
