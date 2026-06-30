"""
Entry point for the ActionCoach Turkey Sales Dashboard.

Streamlit automatically builds the left-hand navigation menu from the files
inside the `pages/` folder (YTD, Quarterly, Monthly). This file is just a
landing screen with a short description and links.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(page_title="ActionCoach Turkey — Sales Dashboard", layout="wide")

st.title("ActionCoach Turkey — Sales Dashboard 2026")

st.write(
    "Use the menu on the left to navigate between **YTD**, **Quarterly**, and "
    "**Monthly** views. All data is pulled live from the team's "
    "**YEAR TO DATE 2026** Google Sheet (auto-refreshed every 15 minutes)."
)

st.info(
    "**YTD** — full-year matrix table (one row per product, one column per "
    "month) with a toggle between Sales count / Sales € / Cashbank €, plus "
    "the standard product summary table.\n\n"
    "**Quarterly** — pick Q1–Q4, see the product summary table for that "
    "quarter.\n\n"
    "**Monthly** — pick any month, see the product summary table for that "
    "month."
)

# ---------------------------------------------------------------------------
# TEMPORARY DEBUG SECTION -- remove once the data pipeline is confirmed
# working. Shows exactly what comes back from the sheet fetch, at every
# stage, so we can see where it goes wrong.
# ---------------------------------------------------------------------------
st.divider()
st.subheader("🔧 Debug: data pipeline")

import data as _data

if st.button("Run debug fetch"):
    try:
        raw = _data.fetch_raw_sheet()
        st.write("**Step 1 — fetch_raw_sheet() result:**")
        st.write(f"Shape: {raw.shape}")
        st.write(f"Columns: {raw.columns.tolist()}")
        st.dataframe(raw.head(5))
    except Exception as e:
        st.error(f"fetch_raw_sheet() FAILED: {type(e).__name__}: {e}")
        st.stop()

    try:
        processed = _data.process_data(raw)
        st.write("**Step 2 — process_data() result:**")
        st.write(f"Shape: {processed.shape}")
        st.write(f"Months found: {sorted(processed['Months'].dropna().unique().tolist())}")
        st.dataframe(processed[["Name_raw", "Product", "Sales", "Cashbank", "Months"]].head(10))
    except Exception as e:
        st.error(f"process_data() FAILED: {type(e).__name__}: {e}")
