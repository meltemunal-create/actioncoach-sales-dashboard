# ActionCoach Turkey — Sales Dashboard 2026

A Streamlit dashboard that pulls live data from the team's **YEAR TO DATE
2026** Google Sheet and presents it as three pages: **YTD**, **Quarterly**,
and **Monthly**.

## Pages

- **YTD** — a 12-month matrix table (one row per product, one column per
  month) with a toggle between **Sales count / Sales € / Cashbank €**, plus
  the standard product summary table and a Saturday Boosters sub-product
  detail breakdown.
- **Quarterly** — pick Q1–Q4, see the product summary table for that quarter.
- **Monthly** — pick a single month, see the product summary table for that
  month.

Every table shows its date range. The whole app is in English.

## Business logic implemented

- **Duplicate sale detection**: if a person+product has an "open" sale (Sales
  filled, Cashbank empty) in one month, and the SAME person+product has BOTH
  Sales and Cashbank filled in a DIFFERENT month, that second row's Sales
  value is a data-entry error and is excluded from the sales count/€ (its
  Cashbank value still counts normally).
- **Cashbank is never filtered**: every row with a Cashbank value counts
  toward that row's month, whether or not a matching Sales row exists
  (e.g. legacy installments) and whether it's the same month as the sale or a
  later one ("Previous Period Cashbank" — shown for reference, not
  subtracted).
- **Saturday Boosters grouping**: every product starting with "SB" (e.g.
  "SB- Financial Literacy Training") plus the "Satuday Boostes x 4 Package"
  product are grouped into a single "Saturday Boosters" line in every summary
  table. The x4 package counts as **4** Saturday Booster units per
  occurrence (its euro amount is unchanged). A separate, target-free detail
  table breaks the individual SB- sub-products back out.

## Updating monthly targets

Edit `targets.py`:

- `UNIT_TARGETS` — per-product, per-month unit (count) targets.
- `REVENUE_TARGETS` — total monthly revenue target in EUR (all products
  combined).

Push the change to GitHub and Streamlit Cloud redeploys automatically.

## Data source

Pulled directly from the public CSV export of the
`YEAR TO DATE 2026` tab of this Google Sheet:

```
https://docs.google.com/spreadsheets/d/1qkuhcLBT9JoEh7prK03M6RMRbP9uf94XlMZkQaRRvgE
```

The sheet must stay shared as **"Anyone with the link can view"** for the
live app to be able to read it. Data is cached for 15 minutes
(`@st.cache_data(ttl=900)` in `data.py`) to avoid hitting Google on every
click — refresh the browser after 15 minutes to see new rows.

## Local development

```bash
pip install -r requirements.txt
streamlit run Home.py
```

## Deploying to Streamlit Cloud

1. Push this folder to a new GitHub repo.
2. Go to [share.streamlit.io](https://share.streamlit.io), connect the repo.
3. Set the main file to `Home.py`.
4. Deploy — no secrets or API keys needed, since the sheet is read as a
   public CSV export.
