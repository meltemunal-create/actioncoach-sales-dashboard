"""
YTD page: a single big table with products as rows and all 12 months as
columns, with a toggle to switch the displayed metric between Sales count,
Sales €, and Cashbank €. Each cell is colour-coded against that month's
target for that product, when a target exists.

Also shows the standard Looker-style summary table (Year-To-Date totals) and
the Saturday Booster sub-product detail breakdown.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

import aggregations as agg
import components as ui
import targets as tg
from data import MONTH_ORDER, MONTH_SHORT, get_processed_data, months_in_data

st.set_page_config(page_title="YTD — ActionCoach Turkey Sales", layout="wide")

st.title("Year To Date 2026")

try:
    df = get_processed_data()
except Exception as e:
    st.error(f"Could not load data from Google Sheets: {e}")
    st.stop()

available_months = months_in_data(df)
if not available_months:
    st.warning("No data found in the sheet yet.")
    st.stop()

start_label = available_months[0]
end_label = available_months[-1]
ui.render_date_caption("Period covered", start_label, end_label)

# ---------------------------------------------------------------------------
# Top KPI row (YTD totals across every month present in the data)
# ---------------------------------------------------------------------------
kpis = agg.overall_kpis(df, available_months)
ui.render_kpi_row(kpis)

st.divider()

# ---------------------------------------------------------------------------
# 12-month matrix table with metric toggle
# ---------------------------------------------------------------------------
st.subheader("Monthly progress by product")
ui.render_date_caption("Showing", start_label, end_label)

metric = st.radio(
    "Metric",
    options=["Sales count", "Sales €", "Cashbank €"],
    horizontal=True,
    label_visibility="collapsed",
)

sub = df[df["Months"].isin(available_months)]


def _pct_color_cell(value, target) -> str:
    try:
        target_f = float(target)
    except (TypeError, ValueError):
        return "color: #999;"
    if pd.isna(target_f) or target_f == 0:
        return "color: #999;"
    try:
        value_f = float(value)
    except (TypeError, ValueError):
        return "color: #999;"
    pct = value_f / target_f * 100
    if pct >= 100:
        return "background-color: #EAF3DE; color: #27500A; font-weight: 600;"
    if pct >= 50:
        return "background-color: #FAEEDA; color: #633806; font-weight: 600;"
    return "background-color: #FCEBEB; color: #791F1F; font-weight: 600;"


def build_matrix(metric_name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Returns (values_df, targets_df) both indexed by display_product,
    columned by month-short-name, for the chosen metric."""
    if metric_name == "Sales count":
        rows = sub[sub["counts_as_sale"]]
        pivot = rows.groupby(["display_product", "Months"])["booster_units"].sum().unstack(
            fill_value=0
        )
        target_lookup = tg.UNIT_TARGETS
    elif metric_name == "Sales €":
        rows = sub[sub["counts_as_sale"]]
        pivot = rows.groupby(["display_product", "Months"])["Sales"].sum().unstack(
            fill_value=0
        )
        target_lookup = None  # no per-product euro targets provided
    else:  # Cashbank €
        rows = sub[sub["counts_as_cashbank"]]
        pivot = rows.groupby(["display_product", "Months"])["Cashbank"].sum().unstack(
            fill_value=0
        )
        target_lookup = None

    pivot = pivot.reindex(columns=[m for m in MONTH_ORDER if m in pivot.columns], fill_value=0)
    pivot = pivot.rename(columns=MONTH_SHORT)

    from aggregations import _product_sort_key

    pivot["_sort"] = pivot.index.map(_product_sort_key)
    pivot = pivot.sort_values("_sort").drop(columns="_sort")

    targets_df = pd.DataFrame(index=pivot.index, columns=pivot.columns, dtype="float64")
    if target_lookup:
        for product in pivot.index:
            for month_full, month_short in MONTH_SHORT.items():
                if month_short in targets_df.columns:
                    targets_df.loc[product, month_short] = target_lookup.get(
                        product, {}
                    ).get(month_full)

    return pivot, targets_df


values, target_grid = build_matrix(metric)

def _fmt_matrix_num(v) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return "--"
    if pd.isna(f):
        return "--"
    return f"{f:,.0f}"


values_display = values.copy()
values_display.insert(0, "Total", values.sum(axis=1))
fmt_values = values_display.map(_fmt_matrix_num)
fmt_values = fmt_values.reset_index().rename(columns={"display_product": "Product"})


def style_matrix(row):
    styles = [""] * len(row)
    product = row["Product"]
    for i, col in enumerate(row.index):
        if col in ("Product", "Total"):
            continue
        raw_val = values.loc[product, col] if col in values.columns else None
        raw_target = (
            target_grid.loc[product, col]
            if (product in target_grid.index and col in target_grid.columns)
            else None
        )
        styles[i] = _pct_color_cell(raw_val, raw_target)
    return styles


styled_matrix = fmt_values.style.apply(style_matrix, axis=1)
st.dataframe(styled_matrix, use_container_width=True, hide_index=True)

if metric == "Sales count":
    st.caption(
        "Cells are colour-coded against that month's unit target for the product "
        "(green ≥100%, amber 50–99%, red <50%, grey = no target set)."
    )
else:
    st.caption(
        "Per-product monthly targets are only defined for unit counts; "
        "this view shows raw totals without colour-coding."
    )

st.divider()

# ---------------------------------------------------------------------------
# Standard Looker-style summary table (YTD totals)
# ---------------------------------------------------------------------------
st.subheader("Product summary — Year To Date")
ui.render_date_caption("Showing", start_label, end_label)

summary_table = agg.build_product_table(df, available_months)
grand_total = agg.grand_total_row(summary_table)
ui.render_product_table(summary_table, grand_total)

st.divider()

# ---------------------------------------------------------------------------
# Saturday Booster detail breakdown (no targets)
# ---------------------------------------------------------------------------
st.subheader("Saturday Boosters — sub-product detail")
ui.render_date_caption("Showing", start_label, end_label)
st.caption("No targets shown here — for tracking individual SB- product mix only.")

sb_detail = agg.build_sb_detail_table(df, available_months)
ui.render_sb_detail_table(sb_detail)
