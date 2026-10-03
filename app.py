import streamlit as st
import pandas as pd
from pathlib import Path
from search_engine import FastSchoolIndex

st.set_page_config(
    page_title="AP & Telangana School Identity Search",
    page_icon="🏫",
    layout="wide"
)

BASE = Path(__file__).parent
DATA = BASE / "data"
XLSX = DATA / "SMS_Schools_Consolidated_Cohort_2026_01_Oct.xlsx"
DB = DATA / "school_search.sqlite"


@st.cache_data(show_spinner=False)
def metadata():
    d = pd.read_excel(XLSX, nrows=0, engine="openpyxl")
    cols = list(d.columns)

    def p(*terms):
        for c in cols:
            if any(t in c.lower() for t in terms):
                return c
        return None

    return cols, {
        "state": p("school_state", "state"),
        "district": p("school_district", "district"),
        "block": p("school_block", "mandal", "block"),
        "village": p("school_village", "village"),
        "school_name": p("school_name", "schoolname"),
        "updated_name": p("updated_school_name", "updated"),
        "udise": p("udise", "emis", "school_code"),
    }


@st.cache_resource(show_spinner=False)
def get_index():
    cols, sem = metadata()
    return FastSchoolIndex(
        DB,
        cols,
        sem,
        DATA / "verified_school_enrichment.csv"
    )


@st.cache_data(show_spinner=False)
def history():
    return pd.read_csv(DATA / "district_history.csv")


@st.cache_data(show_spinner=False)
def enrichment():
    p = DATA / "verified_school_enrichment.csv"

    if not p.exists():
        return pd.DataFrame()

    return pd.read_csv(
        p,
        dtype=str
    ).fillna("")


def merge_enrichment(record):
    e = enrichment()

    if e.empty or not sem["udise"]:
        return record

    code = str(
        record.get(sem["udise"], "")
    ).strip()

    if not code:
        return record

    matches = e[
        e["udise_code"].astype(str).str.strip() == code
    ]

    if matches.empty:
        return record

    extra = matches.iloc[0].to_dict()

    mapping = {
        "verified_school_name": "Verified School Name",
        "school_category": "School Category",
        "school_management": "School Management",
        "class_range": "Class",
        "school_type": "School Type",
        "school_location": "School Location",
        "lgd_block": "LGD Block",
        "lgd_panchayat": "LGD Panchayat",
        "lgd_village": "LGD Village",
        "address": "Verified Address",
        "pin_code": "PIN Code",
        "source": "Verification Source",
        "source_url": "Verification Source URL",
        "source_year": "Source Year",
        "verification_status": "Verification Status",
        "last_verified": "Last Verified",
    }

    for key, label in mapping.items():
        value = str(extra.get(key, "")).strip()

        if value:
            record[label] = extra[key]

    return record


cols, sem = metadata()
idx = get_index()
hist = history()


# -----------------------------
# Page styling
# -----------------------------

st.markdown(
    """
    <style>
    .block-container {
        max-width: 1280px;
        padding-top: 1.2rem;
    }

    .result {
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0;
    }

    .muted {
        color: #8a93a3;
        font-size: 0.88rem;
    }

    .profile {
        border: 1px solid #e5e7eb;
        border-radius: 14px;
        padding: 18px;
        margin-top: 12px;
    }
    </style>
    """,
    unsafe_allow_html=True
)


# -----------------------------
# Header
# -----------------------------

st.title("🏫 AP & Telangana School Identity Search")

st.caption(
    "Select State first. District and Village are optional filters. "
    "Results show the top 3 matches."
)


# -----------------------------
# Main layout
# -----------------------------

left, right = st.columns(
    [2.15, 1.65],
    gap="large"
)


# =========================================================
# LEFT COLUMN
# =========================================================

with left:

    st.subheader("Find Your School")

    indexed = {
        str(x).strip().casefold(): str(x).strip()
        for x in idx.states()
    }

    display_states = [
        "Andhra Pradesh",
        "Telangana"
    ]

    available = [
        x
        for x in display_states
        if x.casefold() in indexed
    ]

    # -----------------------------
    # State
    # -----------------------------

    state = st.selectbox(
        "1. State *",
        ["Select State"] + available,
        key="state_filter"
    )

    # -----------------------------
    # State not selected
    # -----------------------------

    if state == "Select State":

        st.selectbox(
            "2. District",
            ["Select State first"],
            disabled=True
        )

        st.selectbox(
            "3. Village",
            ["Select District first"],
            disabled=True
        )

        with st.form("search_form"):

            q = st.text_input(
                "4. Search",
                placeholder=(
                    "School name, short name, UDISE code, etc."
                ),
                disabled=True
            )

            go = st.form_submit_button(
                "SEARCH",
                disabled=True,
                use_container_width=True
            )

        st.info(
            "State is mandatory. Select Andhra Pradesh or Telangana "
            "to continue."
        )

    # -----------------------------
    # State selected
    # -----------------------------

    else:

        state_db = indexed[state.casefold()]

        # -------------------------
        # District
        # -------------------------

        districts = idx.districts(state_db)

        district = st.selectbox(
            "2. District",
            ["All Districts"] + districts,
            key=f"district_{state_db}"
        )

        # -------------------------
        # Village
        # -------------------------

        if district == "All Districts":

            village = st.selectbox(
                "3. Village",
                ["Select District first"],
                disabled=True,
                key=f"village_disabled_{state_db}"
            )

            village_db = ""

        else:

            villages = idx.villages(
                state_db,
                district
            )

            village = st.selectbox(
                "3. Village",
                ["All Villages"] + villages,
                key=f"village_{state_db}_{district}"
            )

            village_db = (
                ""
                if village == "All Villages"
                else village
            )

        # -------------------------
        # Search
        # -------------------------

        with st.form("search_form"):

            q = st.text_input(
                "4. Search",
                placeholder=(
                    "School name, short name, UDISE code, etc."
                )
            )

            go = st.form_submit_button(
                "SEARCH",
                type="primary",
                use_container_width=True
            )

        # -------------------------
        # Advanced search
        # -------------------------

        with st.expander("Advanced Search"):

            st.caption(
                "More filters can be added here later without "
                "changing the fast indexed search."
            )

        # -------------------------
        # Execute search
        # -------------------------

        if go:

            results = idx.search(
                q,
                state_db,
                district
                if district != "All Districts"
                else "",
                village_db,
                limit=3
            )

            st.session_state["results"] = results
            st.session_state["selected_school"] = None
            st.session_state["selected_school_udise"] = None

        # -------------------------
        # Existing results
        # -------------------------

        results = st.session_state.get("results")

        if results is not None:

            st.subheader("Top 3 Results")

            if not results:

                st.info(
                    "No matching school found."
                )

            # ---------------------
            # Result cards
            # ---------------------

            for i, r in enumerate(results, 1):

                name = (
                    r.get(sem["updated_name"], "")
                    or r.get(sem["school_name"], "")
                    or "School"
                )

                v = (
                    r.get(sem["village"], "")
                    if sem["village"]
                    else ""
                )

                m = (
                    r.get(sem["block"], "")
                    if sem["block"]
                    else ""
                )

                d = (
                    r.get(sem["district"], "")
                    if sem["district"]
                    else ""
                )

                ud = (
                    r.get(sem["udise"], "")
                    if sem["udise"]
                    else ""
                )

                # -----------------
                # Result information
                # -----------------

                st.markdown(
                    f"""
                    <div class="result">
                        <b>{i}. {name}</b><br>
                        <span class="muted">
                            <b>V:</b> {v or "—"}
                            &nbsp;•&nbsp;
                            <b>M:</b> {m or "—"}
                            &nbsp;•&nbsp;
                            <b>D:</b> {d or "—"}
                        </span><br>
                        <span class="muted">
                            UDISE: {ud or "Not available"}
                        </span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                # -----------------
                # FIXED BUTTON
                # -----------------

                if st.button(
                    "View full school details →",
                    key=f"view_{ud or i}",
                    use_container_width=True
                ):

                    st.session_state[
                        "selected_school"
                    ] = merge_enrichment(r)

                    st.session_state[
                        "selected_school_udise"
                    ] = str(ud or "")

                    # Force Streamlit to rerun immediately
                    st.rerun()

        # -------------------------
        # Selected school
        # -------------------------

        selected = st.session_state.get(
            "selected_school"
        )

        if selected:

            # ---------------------
            # Back button
            # ---------------------

            if st.button(
                "← Back to search results",
                key="back_to_results"
            ):

                st.session_state[
                    "selected_school"
                ] = None

                st.session_state[
                    "selected_school_udise"
                ] = None

                st.rerun()

            st.divider()

            st.subheader("School Profile")

            # ---------------------
            # School name
            # ---------------------

            school_name = (
                selected.get(
                    sem["updated_name"],
                    ""
                )
                or selected.get(
                    sem["school_name"],
                    ""
                )
                or "School"
            )

            st.markdown(
                f"### {school_name}"
            )

            # ---------------------
            # Location / UDISE
            # ---------------------

            v = (
                selected.get(
                    sem["village"],
                    ""
                )
                if sem["village"]
                else ""
            )

            m = (
                selected.get(
                    sem["block"],
                    ""
                )
                if sem["block"]
                else ""
            )

            d = (
                selected.get(
                    sem["district"],
                    ""
                )
                if sem["district"]
                else ""
            )

            ud = (
                selected.get(
                    sem["udise"],
                    ""
                )
                if sem["udise"]
                else ""
            )

            st.markdown(
                f"**V:** {v or '—'} "
                f"&nbsp; • &nbsp; "
                f"**M:** {m or '—'} "
                f"&nbsp; • &nbsp; "
                f"**D:** {d or '—'} "
                f"&nbsp; • &nbsp; "
                f"**UDISE:** {ud or '—'}"
            )

            # ---------------------
            # School information
            # ---------------------

            st.markdown(
                "#### School Information"
            )

            a, b, c = st.columns(3)

            with a:

                st.write(
                    "**School Category**",
                    selected.get(
                        "School Category"
                    )
                    or selected.get(
                        "School_Category__c"
                    )
                    or "Not verified"
                )

                st.write(
                    "**School Management**",
                    selected.get(
                        "School Management"
                    )
                    or selected.get(
                        "School_Management__c"
                    )
                    or "Not verified"
                )

                st.write(
                    "**Class**",
                    selected.get(
                        "Class"
                    )
                    or "Not verified"
                )

            with b:

                st.write(
                    "**School Type**",
                    selected.get(
                        "School Type"
                    )
                    or selected.get(
                        "School_Type__c"
                    )
                    or selected.get(
                        "School_Type"
                    )
                    or "Not verified"
                )

                st.write(
                    "**School Location**",
                    selected.get(
                        "School Location"
                    )
                    or selected.get(
                        "School_Location__c"
                    )
                    or "Not verified"
                )

                st.write(
                    "**LGD Block**",
                    selected.get(
                        "LGD Block"
                    )
                    or "Not verified"
                )

            with c:

                st.write(
                    "**LGD Panchayat**",
                    selected.get(
                        "LGD Panchayat"
                    )
                    or "Not verified"
                )

                st.write(
                    "**LGD Village**",
                    selected.get(
                        "LGD Village"
                    )
                    or "Not verified"
                )

                st.write(
                    "**PIN Code**",
                    selected.get(
                        "PIN Code"
                    )
                    or "Not verified"
                )

            # ---------------------
            # Address
            # ---------------------

            st.markdown(
                "#### Address"
            )

            st.write(
                selected.get(
                    "Verified Address"
                )
                or selected.get(
                    "School_Address__c"
                )
                or "Not verified"
            )

            # ---------------------
            # Verification
            # ---------------------

            if selected.get(
                "Verification Status"
            ):

                st.markdown(
                    "#### Verification"
                )

                st.write(
                    "**Status:**",
                    selected.get(
                        "Verification Status"
                    )
                )

                st.write(
                    "**Source:**",
                    selected.get(
                        "Verification Source"
                    )
                    or "—"
                )

                st.write(
                    "**Source Year:**",
                    selected.get(
                        "Source Year"
                    )
                    or "—"
                )

                st.write(
                    "**Last Verified:**",
                    selected.get(
                        "Last Verified"
                    )
                    or "—"
                )

                if selected.get(
                    "Verification Source URL"
                ):

                    st.markdown(
                        "**Source:** "
                        + str(
                            selected.get(
                                "Verification Source URL"
                            )
                        )
                    )

            # ---------------------
            # School identity
            # ---------------------

            st.markdown(
                "#### School Identity"
            )

            st.write(
                "**Original Excel School Name:**",
                selected.get(
                    "School_Name__c"
                )
                or "—"
            )

            st.write(
                "**Updated School Name:**",
                selected.get(
                    "Updated_School_Name_c"
                )
                or "—"
            )

            st.write(
                "**Cluster:**",
                selected.get(
                    "School_Cluster__c"
                )
                or "—"
            )

            # ---------------------
            # Original Excel fields
            # ---------------------

            with st.expander(
                "View all original Excel fields"
            ):

                for col in cols:

                    st.write(
                        f"**{col}:**",
                        selected.get(
                            col,
                            ""
                        )
                    )


# =========================================================
# RIGHT COLUMN
# =========================================================

with right:

    # -----------------------------
    # Andhra Pradesh history
    # -----------------------------

    with st.expander(
        "📍 Andhra Pradesh — District History",
        expanded=False
    ):

        st.caption(
            "Static reference only."
        )

        x = hist[
            hist["state"] == "Andhra Pradesh"
        ]

        for old in sorted(
            x["old_district"]
            .dropna()
            .unique()
        ):

            vals = x.loc[
                x["old_district"] == old,
                "successor_district"
            ].tolist()

            st.markdown(
                f"**{old}** → "
                f"{' • '.join(vals)}"
            )

    # -----------------------------
    # Telangana history
    # -----------------------------

    with st.expander(
        "📍 Telangana — District History",
        expanded=False
    ):

        st.caption(
            "Static reference only."
        )

        x = hist[
            hist["state"] == "Telangana"
        ]

        for old in sorted(
            x["old_district"]
            .dropna()
            .unique()
        ):

            vals = x.loc[
                x["old_district"] == old,
                "successor_district"
            ].tolist()

            st.markdown(
                f"**{old}** → "
                f"{' • '.join(vals)}"
            )


# -----------------------------
# Footer
# -----------------------------

st.divider()

st.caption(
    "Original Excel is preserved unchanged. "
    "SQLite is the read-only search accelerator."
)
