import pandas as pd
import streamlit as st

from utils.excel_io import EXCEL_TYPES, download_xlsx, read_file, to_excel_bytes

st.title("🔗 Combine Workbooks")

mode = st.radio("What do you want to do?",
                ["Stack files/sheets on top of each other", "Join two tables on a key column"],
                horizontal=True)

if mode.startswith("Stack"):
    files = st.file_uploader("Upload one or more workbooks", type=EXCEL_TYPES,
                             accept_multiple_files=True, key="stack_files")
    if not files:
        st.info("Upload files to combine. Every sheet of every file can be included.")
        st.stop()

    options = {}
    for f in files:
        for sheet, df in read_file(f.name, f.getvalue()).items():
            options[f"{f.name} › {sheet}"] = (f.name, sheet, df)

    chosen = st.multiselect("Sheets to include", list(options), default=list(options))
    c1, c2 = st.columns(2)
    add_source = c1.checkbox("Add 'Source File' and 'Source Sheet' columns", True)
    match = c2.radio("Columns", ["Keep all columns", "Only columns common to all"], horizontal=True)
    if not chosen:
        st.stop()

    frames = []
    for key in chosen:
        fname, sheet, df = options[key]
        df = df.copy()
        df.columns = [str(c).strip() for c in df.columns]
        if add_source:
            df.insert(0, "Source Sheet", sheet)
            df.insert(0, "Source File", fname)
        frames.append(df)
    combined = pd.concat(frames, ignore_index=True, join="outer" if match.startswith("Keep") else "inner")

    st.metric("Combined rows", f"{len(combined):,}")
    st.dataframe(combined.head(500), use_container_width=True)
    download_xlsx(to_excel_bytes({"Combined": combined}), "combined.xlsx")

else:
    c1, c2 = st.columns(2)
    tables = []
    for col, label in ((c1, "Left table"), (c2, "Right table")):
        with col:
            f = st.file_uploader(label, type=EXCEL_TYPES, key=f"join_{label}")
            if f:
                sheets = read_file(f.name, f.getvalue())
                s = st.selectbox("Sheet", list(sheets), key=f"join_sheet_{label}")
                tables.append(sheets[s])
    if len(tables) < 2:
        st.info("Upload both tables to join them.")
        st.stop()

    left, right = tables
    c1, c2, c3 = st.columns(3)
    lkey = c1.selectbox("Left key column", list(left.columns))
    rkey = c2.selectbox("Right key column", list(right.columns))
    how = c3.selectbox("Join type", ["left", "inner", "outer", "right"],
                       format_func={"left": "Keep all left rows (VLOOKUP-style)", "inner": "Only matches",
                                    "outer": "Keep everything", "right": "Keep all right rows"}.get)
    normalize = st.checkbox("Ignore case and extra spaces in keys", True)

    l, r = left.copy(), right.copy()
    if normalize:
        l["_k"] = l[lkey].astype(str).str.strip().str.lower()
        r["_k"] = r[rkey].astype(str).str.strip().str.lower()
        merged = l.merge(r, on="_k", how=how, suffixes=("", " (right)"), indicator=True).drop(columns="_k")
    else:
        merged = l.merge(r, left_on=lkey, right_on=rkey, how=how, suffixes=("", " (right)"), indicator=True)

    counts = merged["_merge"].value_counts()
    m1, m2, m3 = st.columns(3)
    m1.metric("Matched", int(counts.get("both", 0)))
    m2.metric("Left only", int(counts.get("left_only", 0)))
    m3.metric("Right only", int(counts.get("right_only", 0)))
    merged = merged.rename(columns={"_merge": "Match"}).replace(
        {"Match": {"both": "Matched", "left_only": "Left only", "right_only": "Right only"}})
    merged["Match"] = merged["Match"].astype(str)

    st.dataframe(merged.head(500), use_container_width=True)
    download_xlsx(to_excel_bytes({"Joined": merged}), "joined.xlsx")
