"""
Monthly page: pick a single month (Jan–Dec), see the KPI row and the
standard Looker-style product summary table for that month, plus the
Saturday Booster sub-product detail.
"""

from __future__ import annotations

import streamlit as st

import aggregations as agg
import components as ui
from data import MONTH_ORDER, get_processed_data, months_in_data

st.set_page_config(page_title="Monthly — ActionCoach Turkey Sales", layout="wide")

st.title("Monthly Sales Report")

try:
    df = get_processed_data()
except Exception as e:
    st.error(f"Could not load data from Google Sheets: {e}")
    st.stop()

available_months = months_in_data(df)
if not available_months:
    st.warning("No data found in the sheet yet.")
    st.stop()

month = st.selectbox("Month", options=MONTH_ORDER, index=MONTH_ORDER.index(available_months[-1]))

if month not in available_months:
    st.warning(f"No data available yet for {month}.")
    st.stop()

ui.render_date_caption("Month", month, month)

kpis = agg.overall_kpis(df, [month])
ui.render_kpi_row(kpis)

st.divider()

st.subheader(f"Product summary — {month}")
ui.render_date_caption("Showing", month, month)

table = agg.build_product_table(df, [month])
grand_total = agg.grand_total_row(table)
ui.render_product_table(table, grand_total)

st.divider()

st.subheader("Saturday Boosters — sub-product detail")
ui.render_date_caption("Showing", month, month)
st.caption("No targets shown here — for tracking individual SB- product mix only.")

sb_detail = agg.build_sb_detail_table(df, [month])
ui.render_sb_detail_table(sb_detail)
