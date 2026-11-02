import pandas as pd
import streamlit as st

from utils.excel_io import download_xlsx, to_excel_bytes, upload_single_sheet

st.title("🎨 Formatter")

df, base = upload_single_sheet("fmt")
if df is None:
    st.stop()

FORMATS = {
    "General": None,
    "Number (1,234.56)": "#,##0.00",
    "Whole number (1,234)": "#,##0",
    "Currency ($1,234.56)": "$#,##0.00",
    "Percent (12.5%)": "0.0%",
    "Date (MM/DD/YYYY)": "mm/dd/yyyy",
    "Date (YYYY-MM-DD)": "yyyy-mm-dd",
    "Date (Mon DD, YYYY)": "mmm dd, yyyy",
    "Text": "@",
}

st.subheader("1. Choose, order and rename columns")
keep = st.multiselect("Columns to keep (in output order)", list(df.columns), default=list(df.columns))
if not keep:
    st.warning("Select at least one column.")
    st.stop()

config = pd.DataFrame({
    "Column": keep,
    "New name": keep,
    "Format": ["Date (MM/DD/YYYY)" if pd.api.types.is_datetime64_any_dtype(df[c])
               else "Number (1,234.56)" if pd.api.types.is_float_dtype(df[c])
               else "General" for c in keep],
})
st.subheader("2. Rename and set Excel formats")
edited = st.data_editor(
    config, hide_index=True, use_container_width=True, disabled=["Column"],
    column_config={"Format": st.column_config.SelectboxColumn(options=list(FORMATS), required=True)},
)

st.subheader("3. Sort and style")
c1, c2, c3, c4 = st.columns(4)
sort_by = c1.selectbox("Sort by", ["(none)"] + keep)
ascending = c2.radio("Order", ["Ascending", "Descending"], horizontal=True) == "Ascending"
header_color = c3.color_picker("Header color", "#1F4E78")
banded = c4.checkbox("Banded rows", True)
sheet_name = st.text_input("Output sheet name", "Formatted")

out = df[keep].copy()
if sort_by != "(none)":
    out = out.sort_values(sort_by, ascending=ascending, kind="stable")

rename_map = dict(zip(edited["Column"], edited["New name"].fillna(edited["Column"])))
out = out.rename(columns=rename_map)
number_formats = {rename_map[c]: FORMATS[f] for c, f in zip(edited["Column"], edited["Format"]) if FORMATS.get(f)}

# Make sure date-formatted columns are real dates so Excel applies the format.
for col, fmt in number_formats.items():
    if fmt in ("mm/dd/yyyy", "yyyy-mm-dd", "mmm dd, yyyy") and not pd.api.types.is_datetime64_any_dtype(out[col]):
        out[col] = pd.to_datetime(out[col], errors="coerce")

st.subheader("Preview")
st.dataframe(out.head(500), use_container_width=True)

data = to_excel_bytes({sheet_name: out}, header_color=header_color,
                      number_formats=number_formats, banded=banded)
download_xlsx(data, f"{base}_formatted.xlsx")
