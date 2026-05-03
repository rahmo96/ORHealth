"""Custom CSS styles for Streamlit UI."""

from __future__ import annotations

APP_CSS: str = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Heebo:wght@300;400;500;700;800&display=swap" rel="stylesheet">
<style>
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
    }
    .stApp {
        font-family: "Heebo", sans-serif;
        background:
            radial-gradient(circle at 18% 10%, rgba(109, 76, 130, 0.14), transparent 34%),
            radial-gradient(circle at 80% 30%, rgba(231, 111, 81, 0.08), transparent 40%),
            repeating-radial-gradient(circle at 50% 50%, rgba(255,255,255,0.01) 0 1px, transparent 1px 3px),
            var(--bg-deep);
        color: var(--text-main);
        direction: rtl;
    }
    .stApp, .stMarkdown, p, label, .stCaption {
        color: var(--text-main);
        font-family: "Heebo", sans-serif !important;
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
    section[data-testid="stMain"] {
        padding-bottom: 1.25rem !important;
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
        margin-top: 1.25rem;
        padding: 0.5rem 0.35rem 0.65rem !important;
        background: linear-gradient(180deg, rgba(13, 15, 24, 0.95) 0%, #101322 100%);
        border: 1px solid var(--border-subtle) !important;
        border-radius: 16px;
        box-shadow: 0 8px 28px rgba(0, 0, 0, 0.35);
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"] {
        text-align: center;
    }
    .bottom-nav-icon {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 0.15rem;
        color: var(--text-soft);
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] [data-testid="column"]:has(button[kind="primary"]) .bottom-nav-icon {
        color: var(--accent-primary);
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="primary"] {
        background: var(--accent-primary) !important;
        color: #fff !important;
        font-weight: 700;
        min-height: 40px;
        font-size: 0.82rem;
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"] {
        background: rgba(26, 31, 47, 0.95) !important;
        color: var(--text-soft) !important;
        border: 1px solid var(--border-subtle) !important;
        font-weight: 500;
        min-height: 40px;
        font-size: 0.82rem;
    }
    section[data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] .stButton > button[kind="secondary"]:hover {
        border-color: rgba(109, 76, 130, 0.45) !important;
        color: var(--text-main) !important;
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
    div.stButton > button[kind="secondaryFormSubmit"],
    div.stButton > button[kind="primary"] {
        width: 100%;
        border-radius: 12px;
        background: var(--accent-primary) !important;
        border: 1px solid rgba(255,255,255,0.15);
        color: #fff !important;
        font-weight: 700;
        min-height: 46px;
        transition: filter 0.2s ease;
    }
    div.stButton > button[kind="secondaryFormSubmit"]:hover,
    div.stButton > button[kind="primary"]:hover {
        filter: brightness(1.08);
    }
    .footer-meta {
        margin-top: 1.5rem;
        text-align: left;
        color: #9a9cab;
        font-size: 0.72rem;
    }
</style>
"""
