"""Custom CSS styles for Streamlit UI."""

from __future__ import annotations

APP_CSS: str = """
<style>
    .stApp {
        background: radial-gradient(circle at top, #1e1e2f 0%, #151523 45%, #0f0f19 100%);
        color: #f4f7ff;
    }
    .title {
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.3px;
        margin-bottom: 0.5rem;
    }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(255, 255, 255, 0.12);
        border-radius: 12px;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.03);
    }
</style>
"""
