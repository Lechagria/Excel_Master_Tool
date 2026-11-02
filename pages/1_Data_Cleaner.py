import re

import pandas as pd
import streamlit as st

from utils.excel_io import download_xlsx, summary_metrics, to_excel_bytes, upload_single_sheet

st.title("🧹 Data Cleaner")

df, base = upload_single_sheet("clean")
if df is None:
    st.stop()

with st.expander("Preview original", expanded=False):
    st.dataframe(df.head(200), use_container_width=True)

st.subheader("Cleaning options")
c1, c2 = st.columns(2)
with c1:
    header_row = st.number_input("Header is on row (1 = first row)", 1, 50, 1,
                                 help="Use this if the real headers sit below a title block.")
    trim = st.checkbox("Trim extra spaces in text", True)
    drop_empty_rows = st.checkbox("Remove fully blank rows", True)
    drop_empty_cols = st.checkbox("Remove fully blank columns", True)
    drop_dupes = st.checkbox("Remove duplicate rows", True)
with c2:
    col_style = st.selectbox("Column name style", ["Keep as is", "Title Case", "snake_case", "UPPERCASE"])
    text_case = st.selectbox("Text value case", ["Keep as is", "Title Case", "UPPERCASE", "lowercase"])
    fill_blank = st.text_input("Fill remaining blanks with (leave empty to skip)", "")

if header_row > 1:
    new_header = df.iloc[header_row - 2].astype(str).tolist()
    df = df.iloc[header_row - 1:].reset_index(drop=True)
    df.columns = new_header

cols = list(df.columns)
c3, c4, c5 = st.columns(3)
num_cols = c3.multiselect("Convert to numbers", cols, help="Strips $, commas and % first.")
date_cols = c4.multiselect("Convert to dates", cols)
required_cols = c5.multiselect("Remove rows where these are blank", cols)


def rename(c: str) -> str:
    c = re.sub(r"\s+", " ", str(c)).strip()
    if col_style == "Title Case":
        return c.title()
    if col_style == "snake_case":
        return re.sub(r"[^0-9a-zA-Z]+", "_", c).strip("_").lower()
    if col_style == "UPPERCASE":
        return c.upper()
    return c


def clean(raw: pd.DataFrame) -> pd.DataFrame:
    out = raw.copy()
    text_cols = out.select_dtypes(include=["object", "string"]).columns

    if trim:
        for c in text_cols:
            out[c] = out[c].map(lambda v: re.sub(r"\s+", " ", v).strip() if isinstance(v, str) else v)
            out[c] = out[c].replace("", pd.NA)
    if text_case != "Keep as is":
        fn = {"Title Case": str.title, "UPPERCASE": str.upper, "lowercase": str.lower}[text_case]
        skip = set(num_cols) | set(date_cols)
        for c in text_cols:
            if c not in skip:
                out[c] = out[c].map(lambda v: fn(v) if isinstance(v, str) else v)
    for c in num_cols:
        s = out[c].astype(str).str.replace(r"[,$€£\s]", "", regex=True)
        pct = s.str.endswith("%")
        s = pd.to_numeric(s.str.rstrip("%"), errors="coerce")
        out[c] = s.where(~pct, s / 100)
    for c in date_cols:
        out[c] = pd.to_datetime(out[c], errors="coerce")
    if drop_empty_rows:
        out = out.dropna(how="all")
    if drop_empty_cols:
        out = out.dropna(axis=1, how="all")
    if required_cols:
        out = out.dropna(subset=[c for c in required_cols if c in out.columns])
    if drop_dupes:
        out = out.drop_duplicates()
    if fill_blank:
        for c in out.columns:
            if c not in date_cols and out[c].isna().any():
                out[c] = out[c].astype(object).where(out[c].notna(), fill_blank)
    out.columns = [rename(c) for c in out.columns]
    return out.reset_index(drop=True)


cleaned = clean(df)

st.subheader("Result")
summary_metrics(df, cleaned)
st.dataframe(cleaned.head(500), use_container_width=True)

download_xlsx(to_excel_bytes({"Cleaned": cleaned}), f"{base}_cleaned.xlsx")
