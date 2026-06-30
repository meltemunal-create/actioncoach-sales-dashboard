"""
Core data loading and processing for ActionCoach Turkey Sales Dashboard.

Key business logic implemented here:
1. Pull "YEAR TO DATE 2026" sheet from the public Google Sheet (no auth needed).
2. Detect and exclude duplicate Sales entries: a row is a duplicate if the same
   person+product has an EARLIER row where Sales is filled and Cashbank is empty
   (an "open sale"), and this row has BOTH Sales and Cashbank filled in a
   DIFFERENT month. That later row's Sales value is a data-entry error and must
   not be counted as a new sale (but its Cashbank value still counts).
3. Cashbank counts/amounts are NEVER filtered -- every row with a Cashbank value
   counts toward that row's month, regardless of whether a matching Sales row
   exists (orphan cashbank, e.g. old installments) or whether it's a delayed
   payment for a sale made in an earlier month ("previous period").
4. Group all products starting with "SB" or "SB-" into a single "Saturday
   Boosters" line in the summary tables. The product "Satuday Boostes x 4
   Package" is worth 4 Saturday Boosters units per occurrence (not 1) when
   counting volume -- this only affects the unit count, not the euro amount
   (the package price is already the correct total euro value for that row).
5. A separate detailed breakdown table (no targets) is available for the
   individual SB- sub-products.
"""

from __future__ import annotations

import re
from io import StringIO

import pandas as pd
import requests
import streamlit as st

SHEET_ID = "1qkuhcLBT9JoEh7prK03M6RMRbP9uf94XlMZkQaRRvgE"
SHEET_NAME = "YEAR TO DATE 2026"

MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December",
]
MONTH_SHORT = {
    "January": "Jan", "February": "Feb", "March": "Mar", "April": "Apr",
    "May": "May", "June": "Jun", "July": "Jul", "August": "Aug",
    "September": "Sep", "October": "Oct", "November": "Nov", "December": "Dec",
}
QUARTER_MONTHS = {
    "Q1": ["January", "February", "March"],
    "Q2": ["April", "May", "June"],
    "Q3": ["July", "August", "September"],
    "Q4": ["October", "November", "December"],
}

SATURDAY_BOOSTER_PACKAGE_NAME = "Satuday Boostes x 4 Package"
SATURDAY_BOOSTER_PACKAGE_MULTIPLIER = 4
SATURDAY_BOOSTERS_LABEL = "Saturday Boosters"


def _normalize_name(name: str) -> str:
    """Normalize a person's name for matching: trims, collapses whitespace/tabs,
    and lowercases with Turkish-aware case folding (so 'İ'/'I' don't collide
    with unrelated ASCII letters)."""
    if pd.isna(name):
        return ""
    s = str(name)
    s = s.replace("\t", " ").replace("\n", " ")
    s = re.sub(r"\s+", " ", s).strip()
    s = s.replace("İ", "i").replace("I", "ı")
    return s.lower()


def _csv_export_url(sheet_id: str, sheet_name: str) -> str:
    """Build a gviz CSV export URL for a single named sheet/tab in a public
    Google Sheet. Works without any API key as long as the sheet is shared as
    'Anyone with the link can view'."""
    from urllib.parse import quote

    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq"
        f"?tqx=out:csv&sheet={quote(sheet_name)}"
    )


@st.cache_data(ttl=900, show_spinner=False)
def fetch_raw_sheet(sheet_id: str = SHEET_ID, sheet_name: str = SHEET_NAME) -> pd.DataFrame:
    """Download the given sheet/tab as CSV directly from Google Sheets. Cached
    for 15 minutes to avoid hammering Google on every page interaction."""
    url = _csv_export_url(sheet_id, sheet_name)
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    df = pd.read_csv(StringIO(resp.text))
    return df


def _is_saturday_booster(product: str) -> bool:
    p = product.strip()
    if p.upper().startswith("SB"):
        return True
    if p == SATURDAY_BOOSTER_PACKAGE_NAME:
        return True
    return False


def _booster_units(product: str) -> int:
    """How many Saturday Booster 'units' one occurrence of this product is
    worth. The x4 package counts as 4; every other SB- product counts as 1."""
    if product.strip() == SATURDAY_BOOSTER_PACKAGE_NAME:
        return SATURDAY_BOOSTER_PACKAGE_MULTIPLIER
    return 1


def _clean_currency(series: pd.Series) -> pd.Series:
    """Coerce a column that may contain currency-formatted strings into
    clean floats. The Google Sheets CSV export (gviz/tq) uses standard
    English/US number formatting: ',' is the thousands separator and '.' is
    the decimal separator (e.g. '1,100.50€', '750.00'). We strip the
    currency symbol and thousands-separator commas, leaving the decimal
    point untouched, then parse as a standard float."""
    if series.dtype.kind in "if":
        # Already numeric (e.g. when reading from an .xlsx file directly).
        return pd.to_numeric(series, errors="coerce")

    cleaned = (
        series.astype(str)
        .str.replace("€", "", regex=False)
        .str.replace("\u20ac", "", regex=False)
        .str.replace(",", "", regex=False)  # thousands separator
        .str.replace(" ", "", regex=False)
        .str.strip()
    )
    cleaned = cleaned.replace({"": None, "nan": None, "None": None})
    return pd.to_numeric(cleaned, errors="coerce")


def process_data(raw: pd.DataFrame) -> pd.DataFrame:
    """Clean the raw sheet and flag duplicate Sales rows according to the
    business rule described in the module docstring. Returns a row-level
    dataframe with extra helper columns: `key`, `sales_is_duplicate`,
    `counts_as_sale`, `display_product` (SB- products collapsed to
    'Saturday Boosters'), and `booster_units`."""
    df = raw.copy()
    df.columns = [str(c).strip() for c in df.columns]

    required_cols = {"Sales Date", "Name", "Product", "Sales", "Cashbank"}
    missing = required_cols - set(df.columns)
    if missing:
        raise ValueError(f"Sheet is missing expected columns: {missing}")

    df["Product"] = df["Product"].astype(str).str.strip()
    df["Name_raw"] = df["Name"].astype(str).str.strip()
    df["Name_norm"] = df["Name_raw"].apply(_normalize_name)
    df["Sales"] = _clean_currency(df["Sales"])
    df["Cashbank"] = _clean_currency(df["Cashbank"])
    df["Sales Date"] = pd.to_datetime(df["Sales Date"], errors="coerce")

    # Derive the month name directly from the Sales Date column rather than
    # trusting a separate "Months" column in the sheet, which may be absent,
    # blank, or written in a different language. This is the single source
    # of truth for which month a row belongs to.
    df["Months"] = df["Sales Date"].dt.month_name()

    df = df.dropna(subset=["Name_raw"])
    df = df[df["Name_raw"] != "nan"]
    df = df[df["Product"] != "nan"]
    df = df[df["Product"] != ""]

    df["key"] = df["Name_norm"] + " | " + df["Product"]
    df = df.reset_index(drop=True)
    df["row_id"] = df.index

    # --- Duplicate-sale detection ---
    # A key has an "open sale" in some month if Sales is filled and Cashbank
    # is empty in that month. Any row for that same key where BOTH Sales and
    # Cashbank are filled in a DIFFERENT month is a duplicate data-entry: the
    # sale was already recorded as open earlier, this is just the payment
    # update mis-entered into the Sales column again.
    open_sale_keys = set(
        df.loc[(df["Sales"].notna()) & (df["Cashbank"].isna()), "key"]
    )

    df["sales_is_duplicate"] = False
    if open_sale_keys:
        for key in open_sale_keys:
            sub = df[df["key"] == key]
            open_months = set(
                sub.loc[(sub["Sales"].notna()) & (sub["Cashbank"].isna()), "Months"]
            )
            both_filled = sub[(sub["Sales"].notna()) & (sub["Cashbank"].notna())]
            dup_row_ids = both_filled.loc[
                ~both_filled["Months"].isin(open_months), "row_id"
            ]
            df.loc[df["row_id"].isin(dup_row_ids), "sales_is_duplicate"] = True

    df["counts_as_sale"] = df["Sales"].notna() & ~df["sales_is_duplicate"]
    # Cashbank is NEVER filtered -- every filled cashbank row counts.
    df["counts_as_cashbank"] = df["Cashbank"].notna()

    # --- Saturday Booster grouping ---
    df["display_product"] = df["Product"].where(
        ~df["Product"].apply(_is_saturday_booster), SATURDAY_BOOSTERS_LABEL
    )
    # Unit count per row: 1 for every normal product, 4 for the x4 package,
    # 1 for every other individual SB- product. _booster_units already
    # encodes this correctly -- do NOT overwrite it afterwards.
    df["booster_units"] = df["Product"].apply(_booster_units)

    return df


def get_processed_data() -> pd.DataFrame:
    raw = fetch_raw_sheet()
    return process_data(raw)


def months_in_data(df: pd.DataFrame) -> list[str]:
    """Return the months present in the data, in calendar order."""
    present = set(df["Months"].unique())
    return [m for m in MONTH_ORDER if m in present]
