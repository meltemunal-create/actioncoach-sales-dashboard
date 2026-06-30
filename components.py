"""
Shared UI building blocks used by every page: the top KPI card row, the
color-coded Looker-style product table, and the simple SB- detail table.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

ORANGE = "#FF4801"


def render_date_caption(label: str, start, end) -> None:
    """Every table on every page must show its date range -- this is the
    single place that does it, so it's always present and always consistent."""
    st.caption(f"{label}: {start} – {end}")


def render_kpi_row(kpis: dict) -> None:
    cols = st.columns(5)
    with cols[0]:
        st.metric("Number of products", f"{kpis['num_products']:,}")
    with cols[1]:
        st.metric("Number of clients", f"{kpis['num_clients']:,}")
    with cols[2]:
        target = kpis.get("revenue_target")
        pct = f" ({kpis['sales_eur'] / target * 100:.1f}%)" if target else ""
        st.metric("Sales (€)", f"{kpis['sales_eur']:,.0f}{pct}")
        if target:
            st.progress(min(kpis["sales_eur"] / target, 1.0))
            st.caption(f"Target: {target:,.0f} €")
    with cols[3]:
        st.metric("Cashbank (€)", f"{kpis['cashbank_eur']:,.0f}")
    with cols[4]:
        if kpis.get("revenue_target"):
            st.metric("Revenue target (€)", f"{kpis['revenue_target']:,.0f}")
        else:
            st.metric("Revenue target (€)", "--")


def _pct_color(pct) -> str:
    if pct is None or pd.isna(pct):
        return "background-color: transparent; color: inherit;"
    if pct >= 100:
        return "background-color: #EAF3DE; color: #27500A; font-weight: 600;"
    if pct >= 50:
        return "background-color: #FAEEDA; color: #633806; font-weight: 600;"
    return "background-color: #FCEBEB; color: #791F1F; font-weight: 600;"


def render_product_table(table: pd.DataFrame, grand_total: dict) -> None:
    """Render the Looker-style product table with a color-coded Target
    Actual % column and a grand-total row pinned at the bottom."""
    display = table.copy()
    full = pd.concat([display, pd.DataFrame([grand_total])], ignore_index=True)

    fmt = full.copy()
    for col in ["Sales EUR", "Cashbank EUR", "Previous Period Cashbank", "Pending Collection EUR"]:
        fmt[col] = fmt[col].map(lambda v: f"{float(v):,.0f}")
    fmt["Units"] = fmt["Units"].map(lambda v: f"{float(v):,.0f}")
    fmt["Cashbank Count"] = fmt["Cashbank Count"].map(lambda v: f"{float(v):,.0f}")
    fmt["Sales Target"] = fmt["Sales Target"].map(
        lambda v: "--" if pd.isna(v) else f"{float(v):,.0f}"
    )
    fmt["Target Actual %"] = full["Target Actual %"].map(
        lambda v: "--" if v is None or pd.isna(v) else f"{float(v):.0f}%"
    )

    rename = {
        "Units": "# of Products",
        "Sales EUR": "Sales (€)",
        "Cashbank EUR": "Cashbank (€)",
        "Cashbank Count": "Cashbank Count",
        "Sales Target": "Sales Target",
        "Previous Period Cashbank": "Previous Period Cashbank (€)",
        "Pending Collection EUR": "Pending Collection (€)",
        "Target Actual %": "Target Actual %",
    }
    fmt = fmt.rename(columns=rename)

    def highlight_row(row):
        styles = [""] * len(row)
        pct_idx = list(row.index).index("Target Actual %")
        pct_raw = full.loc[row.name, "Target Actual %"]
        styles[pct_idx] = _pct_color(pct_raw)
        if row["Product"] == "Grand total":
            styles = ["font-weight: 600; background-color: #F5F5F5;" for _ in styles]
            styles[pct_idx] = _pct_color(pct_raw) + " font-weight: 600;"
        return styles

    styled = fmt.style.apply(highlight_row, axis=1)
    st.dataframe(styled, use_container_width=True, hide_index=True)


def render_sb_detail_table(sb_table: pd.DataFrame) -> None:
    if sb_table.empty:
        st.caption("No Saturday Booster sales in this period.")
        return
    fmt = sb_table.copy()
    fmt["Units"] = fmt["Units"].map(lambda v: f"{float(v):,.0f}")
    fmt["Sales EUR"] = fmt["Sales EUR"].map(lambda v: f"{float(v):,.0f}")
    fmt["Cashbank EUR"] = fmt["Cashbank EUR"].map(lambda v: f"{float(v):,.0f}")
    fmt = fmt.rename(columns={"Sales EUR": "Sales (€)", "Cashbank EUR": "Cashbank (€)"})
    st.dataframe(fmt, use_container_width=True, hide_index=True)
