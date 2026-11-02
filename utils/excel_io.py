"""Shared helpers: reading uploads, writing styled Excel files, download buttons."""
from __future__ import annotations

import io
import zipfile

import pandas as pd
import streamlit as st
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

EXCEL_TYPES = ["xlsx", "xlsm", "xls", "csv"]


@st.cache_data(show_spinner=False)
def read_file(name: str, data: bytes) -> dict[str, pd.DataFrame]:
    """Return {sheet_name: DataFrame} for an uploaded Excel or CSV file."""
    buf = io.BytesIO(data)
    if name.lower().endswith(".csv"):
        return {"Sheet1": pd.read_csv(buf)}
    return pd.read_excel(buf, sheet_name=None)


def upload_single_sheet(key: str) -> tuple[pd.DataFrame | None, str]:
    """File uploader + sheet picker. Returns (DataFrame, base filename)."""
    up = st.file_uploader("Upload an Excel workbook or CSV", type=EXCEL_TYPES, key=f"{key}_file")
    if up is None:
        st.info("Upload a file to get started.")
        return None, ""
    sheets = read_file(up.name, up.getvalue())
    names = list(sheets)
    sheet = st.selectbox("Sheet", names, key=f"{key}_sheet") if len(names) > 1 else names[0]
    base = up.name.rsplit(".", 1)[0]
    return sheets[sheet].copy(), base


def style_worksheet(ws, df: pd.DataFrame, header_color: str = "1F4E78",
                    number_formats: dict[str, str] | None = None, banded: bool = False) -> None:
    """Bold colored header, freeze top row, autofilter, auto column width, number formats."""
    number_formats = number_formats or {}
    header_fill = PatternFill("solid", fgColor=header_color.lstrip("#"))
    band_fill = PatternFill("solid", fgColor="F2F2F2")

    for cell in ws[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    ws.freeze_panes = "A2"
    if ws.max_row > 1 and ws.max_column > 0:
        ws.auto_filter.ref = ws.dimensions

    for idx, col in enumerate(df.columns, start=1):
        letter = get_column_letter(idx)
        values = [str(col)] + [str(v) for v in df[col].head(500).tolist()]
        ws.column_dimensions[letter].width = min(max(len(v) for v in values) + 2, 60)
        fmt = number_formats.get(col)
        if fmt:
            for (cell,) in ws.iter_rows(min_row=2, min_col=idx, max_col=idx):
                cell.number_format = fmt

    if banded:
        for r in range(3, ws.max_row + 1, 2):
            for cell in ws[r]:
                cell.fill = band_fill


def to_excel_bytes(sheets: dict[str, pd.DataFrame], **style_kwargs) -> bytes:
    """Write one or more DataFrames to a styled .xlsx and return the bytes."""
    out = io.BytesIO()
    with pd.ExcelWriter(out, engine="openpyxl") as writer:
        for name, df in sheets.items():
            safe = safe_sheet_name(name)
            df.to_excel(writer, sheet_name=safe, index=False)
            style_worksheet(writer.sheets[safe], df, **style_kwargs)
    return out.getvalue()


def to_zip_bytes(files: dict[str, bytes]) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
        for fname, data in files.items():
            zf.writestr(fname, data)
    return out.getvalue()


def safe_sheet_name(name) -> str:
    bad = '[]:*?/\\'
    s = "".join("_" if c in bad else c for c in str(name)).strip() or "Sheet"
    return s[:31]


def download_xlsx(data: bytes, filename: str, label: str = "Download Excel") -> None:
    st.download_button(
        label, data=data, file_name=filename, type="primary",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def summary_metrics(before: pd.DataFrame, after: pd.DataFrame) -> None:
    c1, c2, c3 = st.columns(3)
    c1.metric("Rows", f"{len(after):,}", f"{len(after) - len(before):,}")
    c2.metric("Columns", after.shape[1], after.shape[1] - before.shape[1])
    c3.metric("Blank cells", f"{int(after.isna().sum().sum()):,}",
              f"{int(after.isna().sum().sum() - before.isna().sum().sum()):,}", delta_color="inverse")
