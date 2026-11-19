"""Atlas Platform — 1:1 Streamlit presentation of the reference HTML dashboard."""

from __future__ import annotations

import os
from pathlib import Path

import streamlit as st

from atlas.data import DatasetError, build_dashboard, read_csv_records
from atlas.renderer import render_dashboard

ROOT = Path(__file__).resolve().parent
DATA_DIR = Path(os.getenv("ATLAS_DATA_DIR", str(ROOT / "data"))).expanduser().resolve()

st.set_page_config(
    page_title="Atlas | ATO Executive Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Remove Streamlit's default padding and extra chrome, not the original Atlas CSS.
st.markdown(
    """<style>
      [data-testid="stAppViewContainer"] {background: #f1f5fc;}
      [data-testid="stHeader"] {background: transparent; height: 0;}
      [data-testid="stDecoration"] {display: none;}
      .block-container {max-width: 100% !important; padding: 0 !important;}
      [data-testid="stVerticalBlock"] {gap: 0 !important;}
      [data-testid="stElementContainer"] {margin: 0 !important;}
      iframe[title="streamlit_iframe"] {display: block;}
    </style>""",
    unsafe_allow_html=True,
)

try:
    applications = read_csv_records(DATA_DIR, "applications")
    if len(applications) > 1:
        with st.sidebar:
            st.caption("Application")
            current_app = st.selectbox(
                "Select application",
                [row["application_id"] for row in applications],
                format_func=lambda key: next(
                    (r["name"] for r in applications if r["application_id"] == key), key
                ),
                label_visibility="collapsed",
            )
    else:
        current_app = None
    dashboard = build_dashboard(DATA_DIR, ROOT, current_app)
except (DatasetError, OSError) as exc:
    st.error(f"CSV data could not be loaded: {exc}")
    st.info("Check your data/ CSV files, column names, and ATLAS_DATA_DIR setting.")
    st.stop()

html = render_dashboard(dashboard)
# Streamlit 1.67 st.iframe natively supports an HTML string.
st.iframe(html, height="content", width="stretch", alt="Atlas ATO executive dashboard")
