"""
Quarterly page: pick a quarter (Q1–Q4), see the KPI row and the standard
Looker-style product summary table for that quarter, plus the Saturday
Booster sub-product detail.
"""

from __future__ import annotations

import streamlit as st

import aggregations as agg
import components as ui
from data import QUARTER_MONTHS, get_processed_data, months_in_data

st.set_page_config(page_title="Quarterly — ActionCoach Turkey Sales", layout="wide")

st.title("Quarterly Sales Report")

try:
    df = get_processed_data()
except Exception as e:
    st.error(f"Could not load data from Google Sheets: {e}")
    st.stop()

available_months = set(months_in_data(df))

quarter = st.radio("Quarter", options=["Q1", "Q2", "Q3", "Q4"], horizontal=True)

q_months_all = QUARTER_MONTHS[quarter]
q_months_present = [m for m in q_months_all if m in available_months]

if not q_months_present:
    st.warning(f"No data available yet for {quarter} ({', '.join(q_months_all)}).")
    st.stop()

start_label = q_months_present[0]
end_label = q_months_present[-1]
ui.render_date_caption(f"{quarter} period", start_label, end_label)

kpis = agg.overall_kpis(df, q_months_present)
ui.render_kpi_row(kpis)

st.divider()

st.subheader(f"Product summary — {quarter}")
ui.render_date_caption("Showing", start_label, end_label)

table = agg.build_product_table(df, q_months_present)
grand_total = agg.grand_total_row(table)
ui.render_product_table(table, grand_total)

st.divider()

st.subheader("Saturday Boosters — sub-product detail")
ui.render_date_caption("Showing", start_label, end_label)
st.caption("No targets shown here — for tracking individual SB- product mix only.")

sb_detail = agg.build_sb_detail_table(df, q_months_present)
ui.render_sb_detail_table(sb_detail)
