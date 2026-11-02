import streamlit as st

from utils.excel_io import (download_xlsx, safe_sheet_name, to_excel_bytes,
                            to_zip_bytes, upload_single_sheet)

st.title("✂️ Split & Summarize")

df, base = upload_single_sheet("split")
if df is None:
    st.stop()

tab_split, tab_pivot = st.tabs(["Split by column", "Pivot summary"])

with tab_split:
    col = st.selectbox("Split by", list(df.columns), key="split_col")
    groups = {str(k): g for k, g in df.groupby(df[col].fillna("(blank)").astype(str), sort=True)}
    st.write(f"This creates **{len(groups)}** groups.")
    if len(groups) > 200:
        st.warning("That's a lot of groups. Did you pick an ID column by mistake?")
    output = st.radio("Output", ["One workbook, one tab per value", "Separate workbook per value (zip)"],
                      horizontal=True)
    include_all = st.checkbox("Include an 'All' tab", False) if output.startswith("One") else False

    st.dataframe(df[col].value_counts(dropna=False).rename("Rows"), use_container_width=True)

    if output.startswith("One"):
        sheets = ({"All": df} if include_all else {}) | groups
        download_xlsx(to_excel_bytes(sheets), f"{base}_split_by_{safe_sheet_name(col)}.xlsx")
    else:
        files = {f"{base}_{safe_sheet_name(k)}.xlsx": to_excel_bytes({safe_sheet_name(k): g})
                 for k, g in groups.items()}
        st.download_button("Download zip", to_zip_bytes(files), f"{base}_split.zip",
                           mime="application/zip", type="primary")

with tab_pivot:
    numeric = df.select_dtypes("number").columns.tolist()
    c1, c2, c3, c4 = st.columns(4)
    rows = c1.multiselect("Rows", list(df.columns), key="pv_rows")
    columns = c2.selectbox("Columns (optional)", ["(none)"] + list(df.columns), key="pv_cols")
    values = c3.multiselect("Values", numeric or list(df.columns), key="pv_vals")
    agg = c4.selectbox("Calculate", ["sum", "mean", "count", "min", "max"], key="pv_agg")

    if rows and values:
        pivot = df.pivot_table(index=rows, columns=None if columns == "(none)" else columns,
                               values=values, aggfunc=agg, margins=True, margins_name="Total")
        if not isinstance(pivot.columns, str) and pivot.columns.nlevels > 1:
            pivot.columns = [" | ".join(map(str, c)).strip() for c in pivot.columns]
        pivot = pivot.reset_index()
        st.dataframe(pivot, use_container_width=True)
        download_xlsx(to_excel_bytes({"Summary": pivot, "Data": df}, number_formats={}),
                      f"{base}_summary.xlsx", "Download summary")
    else:
        st.info("Pick at least one Rows field and one Values field.")
