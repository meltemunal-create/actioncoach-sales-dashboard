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
