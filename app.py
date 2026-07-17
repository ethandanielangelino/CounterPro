import streamlit as st
import streamlit_shadcn_ui as ui

from database import ensure_database
from tabs.home import render_home
from tabs.summary import render_summary

st.set_page_config(
    page_title="CounterPro",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="collapsed",
)

ensure_database()

st.markdown(
    """
    <style>
        :root {
            --kk-ink: #111827;
            --kk-muted: #64748b;
            --kk-line: #e2e8f0;
            --kk-soft: #f8fafc;
            --kk-accent: #0f766e;
        }
        .stApp { background: #f8fafc; }
        .block-container {
            max-width: 1180px;
            padding-top: 1.5rem;
            padding-bottom: 3rem;
        }
        h1, h2, h3 { letter-spacing: -0.025em; color: var(--kk-ink); }
        .kk-header {
            background: rgba(255,255,255,.92);
            border: 1px solid var(--kk-line);
            border-radius: 18px;
            padding: 22px 24px;
            margin-bottom: 18px;
            box-shadow: 0 8px 30px rgba(15, 23, 42, .05);
        }
        .kk-brand { font-size: 1.75rem; font-weight: 750; color: var(--kk-ink); }
        .kk-subtitle { color: var(--kk-muted); margin-top: 4px; }
        .kk-section-title { font-size: 1.25rem; font-weight: 700; margin-bottom: 2px; }
        .kk-section-copy { color: var(--kk-muted); margin-bottom: 18px; }
        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--kk-line) !important;
            border-radius: 16px !important;
            background: #ffffff;
            box-shadow: 0 5px 18px rgba(15, 23, 42, .035);
        }
        div[data-testid="stNumberInput"] input,
        div[data-baseweb="select"] > div,
        div[data-testid="stDateInput"] input,
        div[data-testid="stTimeInput"] input {
            border-radius: 10px !important;
        }
        .kk-item-line {
            padding: 7px 0;
            border-bottom: 1px solid #eef2f7;
        }
        .kk-card-title { font-size: 1.08rem; font-weight: 750; color: var(--kk-ink); }
        .kk-card-meta { color: var(--kk-muted); font-size: .88rem; margin-top: 2px; }
        .kk-card-items {
            color: #334155;
            font-size: .94rem;
            line-height: 1.45;
            height: 43px;
            overflow: hidden;
            margin-top: 11px;
        }
        .kk-card-stats { color: var(--kk-muted); font-size: .84rem; margin-top: 10px; }
        footer { visibility: hidden; }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="kk-header">
        <div class="kk-brand">KedaiKira</div>
        <div class="kk-subtitle">Cash counter and transaction management for traditional hardware stores.</div>
    </div>
    """,
    unsafe_allow_html=True,
)

page = ui.tabs(
    options=["Cash Counter", "Transaction Summary"],
    default_value="Cash Counter",
    key="main_navigation",
)

st.write("")
if page == "Transaction Summary":
    render_summary()
else:
    render_home()
