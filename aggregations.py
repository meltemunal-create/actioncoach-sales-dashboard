"""
Aggregation helpers: build the Looker-style product summary table for any
chosen set of months, and a few small KPI numbers used by the cards at the
top of each page.
"""

from __future__ import annotations

import pandas as pd

import targets as tg

MC_PRODUCT_ORDER = [
    "Business MC",
    "Management MC",
    "Marketing MC",
    "Sales MC",
    "Leadership MC",
]


def _product_sort_key(name: str) -> tuple[int, str]:
    if name in MC_PRODUCT_ORDER:
        return (0, str(MC_PRODUCT_ORDER.index(name)))
    if name == "Saturday Boosters":
        return (1, name)
    return (2, name)


def build_product_table(df: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    """Build the main Looker-style table for the given months, using the
    grouped `display_product` column (SB- products collapsed into
    'Saturday Boosters', x4 packages already converted to booster units in
    `booster_units`).

    Columns produced:
      Product, Units, Sales EUR, Cashbank EUR, Cashbank Count,
      Sales Target, Sales Cashbank (= Sales EUR, kept for Looker-parity
      naming), Previous Period Cashbank, Pending Collection EUR,
      Target Actual %
    """
    sub = df[df["Months"].isin(months)]

    sales_rows = sub[sub["counts_as_sale"]]
    sales_units = (
        sales_rows.groupby("display_product")["booster_units"].sum().rename("Units")
    )
    sales_eur = sales_rows.groupby("display_product")["Sales"].sum().rename("Sales EUR")

    cb_rows = sub[sub["counts_as_cashbank"]]
    cb_eur = cb_rows.groupby("display_product")["Cashbank"].sum().rename("Cashbank EUR")
    cb_count = cb_rows.groupby("display_product")["booster_units"].sum().rename(
        "Cashbank Count"
    )

    # "Previous period" cashbank: a cashbank row whose month differs from the
    # first sale-month on record for that key (or which has no sale row at
    # all -- e.g. legacy installments). This is informational only; it is
    # NOT subtracted from Cashbank EUR.
    first_sale_month = (
        sub[sub["Sales"].notna()]
        .sort_values("Sales Date")
        .groupby("key")
        .first()["Months"]
        .rename("sale_month")
    )
    cb_tagged = cb_rows.merge(first_sale_month, on="key", how="left")
    is_prev_period = (cb_tagged["sale_month"].isna()) | (
        cb_tagged["Months"] != cb_tagged["sale_month"]
    )
    prev_period_eur = (
        cb_tagged.loc[is_prev_period]
        .groupby("display_product")["Cashbank"]
        .sum()
        .rename("Previous Period Cashbank")
    )

    table = pd.concat(
        [sales_units, sales_eur, cb_eur, cb_count, prev_period_eur], axis=1
    ).fillna(0)

    table["Pending Collection EUR"] = (
        table["Sales EUR"] - table["Cashbank EUR"] + table["Previous Period Cashbank"]
    ).clip(lower=0)

    # Targets, summed across the chosen months (None if no month has a target)
    table["Sales Target"] = table.index.map(
        lambda p: tg.quarter_unit_target(p, months)
    )
    table["Target Actual %"] = table.apply(
        lambda r: (r["Units"] / r["Sales Target"] * 100) if r["Sales Target"] else None,
        axis=1,
    )

    table = table.reset_index().rename(columns={"display_product": "Product"})
    table["_sort"] = table["Product"].apply(_product_sort_key)
    table = table.sort_values("_sort").drop(columns="_sort").reset_index(drop=True)

    ordered_cols = [
        "Product",
        "Units",
        "Sales EUR",
        "Cashbank EUR",
        "Cashbank Count",
        "Sales Target",
        "Previous Period Cashbank",
        "Pending Collection EUR",
        "Target Actual %",
    ]
    return table[ordered_cols]


def grand_total_row(table: pd.DataFrame) -> dict:
    totals = {
        "Product": "Grand total",
        "Units": table["Units"].sum(),
        "Sales EUR": table["Sales EUR"].sum(),
        "Cashbank EUR": table["Cashbank EUR"].sum(),
        "Cashbank Count": table["Cashbank Count"].sum(),
        "Sales Target": table["Sales Target"].sum(skipna=True),
        "Previous Period Cashbank": table["Previous Period Cashbank"].sum(),
        "Pending Collection EUR": table["Pending Collection EUR"].sum(),
    }
    target_sum = totals["Sales Target"]
    totals["Target Actual %"] = (
        (totals["Units"] / target_sum * 100) if target_sum else None
    )
    return totals


def build_sb_detail_table(df: pd.DataFrame, months: list[str]) -> pd.DataFrame:
    """Detailed breakdown of the individual SB- sub-products (no targets, no
    grouping) -- units, sales EUR, cashbank EUR for the chosen months."""
    sub = df[df["Months"].isin(months)]
    sb_mask = sub["Product"].str.upper().str.startswith("SB")
    sb = sub[sb_mask]

    sales_rows = sb[sb["counts_as_sale"]]
    units = sales_rows.groupby("Product")["booster_units"].sum().rename("Units")
    sales_eur = sales_rows.groupby("Product")["Sales"].sum().rename("Sales EUR")

    cb_rows = sb[sb["counts_as_cashbank"]]
    cb_eur = cb_rows.groupby("Product")["Cashbank"].sum().rename("Cashbank EUR")

    table = pd.concat([units, sales_eur, cb_eur], axis=1).fillna(0)
    table = table.reset_index().rename(columns={"Product": "SB Product"})
    table = table.sort_values("SB Product").reset_index(drop=True)
    return table


def overall_kpis(df: pd.DataFrame, months: list[str]) -> dict:
    """The five top KPI numbers shown on every page (Looker-parity)."""
    sub = df[df["Months"].isin(months)]
    sales_rows = sub[sub["counts_as_sale"]]
    cb_rows = sub[sub["counts_as_cashbank"]]

    return {
        "num_products": int(sales_rows["booster_units"].sum()),
        "num_clients": int(sales_rows["Name_norm"].nunique()),
        "sales_eur": float(sales_rows["Sales"].sum()),
        "cashbank_eur": float(cb_rows["Cashbank"].sum()),
        "revenue_target": tg.quarter_revenue_target(months),
    }


def style_target_pct(pct) -> str:
    """Return a short color-coded label for a target percentage, used in the
    dataframe display via a Styler or a plain text column."""
    if pct is None or pd.isna(pct):
        return "--"
    return f"{pct:.0f}%"
