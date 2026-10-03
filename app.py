import json
import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from search_engine import FastSchoolIndex

st.set_page_config(
    page_title="AP & Telangana School Identity Search",
    page_icon="🏫",
    layout="wide",
)

BASE = Path(__file__).resolve().parent
DATA = BASE / "data"
DB = DATA / "school_search.sqlite"
ENRICHMENT = DATA / "verified_school_enrichment.csv"
HISTORY = DATA / "district_history.csv"


def clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


# -----------------------------------------------------------------------------
# Load the schema from the already-built SQLite search index.
# This avoids reading the Excel workbook during every Streamlit startup.
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_schema():
    if not DB.exists():
        raise FileNotFoundError(f"Search database not found: {DB}")

    with sqlite3.connect(DB) as conn:
        row = conn.execute("SELECT data_json FROM schools LIMIT 1").fetchone()

    if not row:
        raise RuntimeError("The SQLite school database contains no school records.")

    record = json.loads(row[0])
    columns = list(record.keys())

    def find_col(*names):
        lower = {c.lower(): c for c in columns}
        for name in names:
            if name.lower() in lower:
                return lower[name.lower()]
        return None

    return columns, {
        "state": find_col("School_State__c"),
        "district": find_col("School_District__c"),
        "block": find_col("School_Block__c"),
        "village": find_col("School_Village__c"),
        "school_name": find_col("School_Name__c"),
        "updated_name": find_col("Updated_School_Name_c"),
        "udise": find_col("School_Udise_Code__c"),
    }


@st.cache_resource(show_spinner=False)
def get_index():
    columns, semantic = load_schema()
    return FastSchoolIndex(DB, columns, semantic, ENRICHMENT)


@st.cache_data(show_spinner=False)
def load_history():
    if not HISTORY.exists():
        return pd.DataFrame(columns=["state", "old_district", "successor_district"])
    return pd.read_csv(HISTORY, dtype=str).fillna("")


@st.cache_data(show_spinner=False)
def load_enrichment():
    if not ENRICHMENT.exists():
        return pd.DataFrame()
    return pd.read_csv(ENRICHMENT, dtype=str).fillna("")


# Show a useful error instead of an all-white page if startup data is broken.
try:
    cols, sem = load_schema()
    idx = get_index()
    hist = load_history()
except Exception as exc:
    st.error("The app could not load its school search data.")
    st.code(str(exc))
    st.info(
