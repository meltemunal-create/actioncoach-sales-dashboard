"""
Monthly targets, provided by the team.

To update targets for a month, just edit the dict below and redeploy (or edit
directly on GitHub -- Streamlit Cloud will pick up the change automatically).

UNIT_TARGETS: target count (number of sales) per product, per month.
  Use the canonical product names below. "Saturday Boosters" is the grouped
  label that covers all SB- products plus the x4 package (already converted
  to booster units).

REVENUE_TARGETS: total revenue target in EUR for the whole month (all
  products combined). This is the figure used for the overall "Sales €"
  progress bar on each page.
"""

from __future__ import annotations

# --- Per-product monthly unit targets ---
# Months not listed for a product simply have no target for that product
# (shown as "--" in the dashboard, not counted against any goal).
UNIT_TARGETS: dict[str, dict[str, int]] = {
    "Business MC": {
        "January": 6,
        "February": 12,
        "March": 12,
        "May": 30,
        "June": 10,
    },
    "Marketing MC": {
        "January": 10,
        "March": 18,
        "May": 18,
    },
    "Sales MC": {
        "February": 8,
        "April": 10,
        "June": 10,
    },
    "Management MC": {
        "March": 8,
        "June": 10,
    },
    "Leadership MC": {
        "April": 10,
        "May": 10,
    },
    "Saturday Boosters": {
        "February": 25,
        "March": 20,
        "April": 10,
        "May": 25,
        "June": 5,
    },
}

# --- Total monthly revenue targets (EUR), all products combined ---
REVENUE_TARGETS: dict[str, float] = {
    "January": 14000,
    "February": 17875,
    "March": 35600,
    "April": 18000,
    "May": 53600,
    "June": 26000,
}


def unit_target(product: str, month: str) -> float | None:
    """Return the unit target for a product/month, or None if not set."""
    return UNIT_TARGETS.get(product, {}).get(month)


def quarter_unit_target(product: str, months: list[str]) -> float | None:
    """Sum unit targets across a list of months for a product. Returns None
    if NO month in the list has a target set (so the UI can show '--' rather
    than a misleading 0)."""
    vals = [UNIT_TARGETS.get(product, {}).get(m) for m in months]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return sum(vals)


def revenue_target(month: str) -> float | None:
    return REVENUE_TARGETS.get(month)


def quarter_revenue_target(months: list[str]) -> float | None:
    vals = [REVENUE_TARGETS.get(m) for m in months]
    vals = [v for v in vals if v is not None]
    if not vals:
        return None
    return sum(vals)


def ytd_unit_target(product: str, months: list[str]) -> float | None:
    return quarter_unit_target(product, months)


def ytd_revenue_target(months: list[str]) -> float | None:
    return quarter_revenue_target(months)
