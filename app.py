"""Excel Data Portal: entry point. Run with:  streamlit run app.py"""
import streamlit as st

st.set_page_config(page_title="Excel Data Portal", page_icon="📊", layout="wide")


def home():
    st.title("📊 Excel Data Portal")
    st.write("Pick a tool to clean, format, combine or split your Excel workbooks. "
             "Files are processed in memory and never stored.")
    tools = [
        ("🧹 Data Cleaner", "pages/1_Data_Cleaner.py",
         "Trim spaces, remove blank rows and duplicates, fix column names, convert types, fill blanks."),
        ("🎨 Formatter", "pages/2_Formatter.py",
         "Rename, reorder and drop columns, apply date/currency/percent formats, style the output workbook."),
        ("🔗 Combine Workbooks", "pages/3_Combine_Workbooks.py",
         "Stack many files or sheets into one table, or join two tables on a key column."),
        ("✂️ Split & Summarize", "pages/4_Split_and_Summarize.py",
         "Split a sheet into tabs or files by a column, and build pivot summaries."),
    ]
    cols = st.columns(2)
    for i, (title, path, desc) in enumerate(tools):
        with cols[i % 2].container(border=True):
            st.subheader(title)
            st.write(desc)
            st.page_link(path, label=f"Open {title.split(' ', 1)[1]}", icon="➡️")


pg = st.navigation({
    "Portal": [st.Page(home, title="Home", icon="🏠", default=True)],
    "Tools": [
        st.Page("pages/1_Data_Cleaner.py", title="Data Cleaner", icon="🧹"),
        st.Page("pages/2_Formatter.py", title="Formatter", icon="🎨"),
        st.Page("pages/3_Combine_Workbooks.py", title="Combine Workbooks", icon="🔗"),
        st.Page("pages/4_Split_and_Summarize.py", title="Split & Summarize", icon="✂️"),
    ],
})
pg.run()
