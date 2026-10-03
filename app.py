import streamlit as st
import pandas as pd
from pathlib import Path
from search_engine import FastSchoolIndex

st.set_page_config(
    page_title="AP & Telangana School Identity Search",
    page_icon="🏫",
    layout="wide",
)

BASE = Path(__file__).parent
DATA = BASE / "data"
XLSX = DATA / "SMS_Schools_Consolidated_Cohort_2026_01_Oct.xlsx"
DB = DATA / "school_search.sqlite"
ENRICHMENT = DATA / "verified_school_enrichment.csv"
HISTORY = DATA / "district_history.csv"


@st.cache_data(show_spinner=False)
def metadata():
    header = pd.read_excel(XLSX, nrows=0, engine="openpyxl")
    cols = list(header.columns)

    def find_col(*terms):
        for col in cols:
            low = col.lower()
            if any(term in low for term in terms):
                return col
        return None

    return cols, {
        "state": find_col("school_state", "state"),
        "district": find_col("school_district", "district"),
        "block": find_col("school_block", "mandal", "block"),
        "village": find_col("school_village", "village"),
        "school_name": find_col("school_name", "schoolname"),
        "updated_name": find_col("updated_school_name", "updated"),
        "udise": find_col("udise", "emis", "school_code"),
    }


@st.cache_resource(show_spinner=False)
def get_index():
    cols, sem = metadata()
    return FastSchoolIndex(DB, cols, sem, ENRICHMENT)


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


cols, sem = metadata()
idx = get_index()
hist = load_history()


def clean(value):
    if value is None:
        return ""
    text = str(value).strip()
    if text.lower() in {"nan", "none", "nat"}:
        return ""
    return text


def get_value(record, key):
    if not key:
        return ""
    return clean(record.get(key, ""))


def get_school_name(record):
    return (
        get_value(record, sem["updated_name"])
        or get_value(record, sem["school_name"])
        or "School"
    )


def merge_enrichment(record):
    """Add externally verified fields when a UDISE match exists."""
    output = dict(record)
    enrichment = load_enrichment()

    udise_col = sem.get("udise")
