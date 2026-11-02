# Excel Data Portal

A Streamlit portal with four tools for cleaning and formatting Excel workbooks.

| Tool | What it does |
|---|---|
| 🧹 Data Cleaner | Trim spaces, drop blank rows/columns and duplicates, fix header row, standardize column names, convert numbers/dates, fill blanks |
| 🎨 Formatter | Pick/reorder/rename columns, set Excel number formats (currency, %, dates), sort, header color, banded rows |
| 🔗 Combine Workbooks | Stack many files/sheets into one table, or join two tables on a key (VLOOKUP-style) with match report |
| ✂️ Split & Summarize | Split a sheet into tabs or separate files by a column value; build pivot summaries |

Every output is a styled `.xlsx` (bold header, frozen top row, filters, auto column widths).

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

## Deploy from GitHub (Streamlit Community Cloud)

1. Push this folder to a GitHub repo.
2. Go to https://share.streamlit.io → **Create app** → pick the repo and branch.
3. Set **Main file path** to `app.py` → **Deploy**.

Every push to the branch redeploys automatically.

## Project layout

```
app.py                      # portal home + navigation
pages/1_Data_Cleaner.py
pages/2_Formatter.py
pages/3_Combine_Workbooks.py
pages/4_Split_and_Summarize.py
utils/excel_io.py           # shared read/write/style helpers
```

To add or replace a tool, drop a new file in `pages/` and register it in the `st.navigation` block in `app.py`.
