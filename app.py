import csv
import html
from pathlib import Path

import streamlit as st

from search_engine import FastSchoolIndex


st.set_page_config(
    page_title="AP & Telangana School Identity Search",
    page_icon="🏫",
    layout="wide",
)

BASE = Path(__file__).parent
DATA = BASE / "data"
DB = DATA / "school_search.sqlite"
HISTORY_CSV = DATA / "district_history.csv"
ENRICHMENT_CSV = DATA / "verified_school_enrichment.csv"

# Exact columns in the master Excel dataset.
COLUMNS = [
    "Id",
    "School_Udise_Code__c",
    "School_State__c",
    "School_District__c",
    "School_Block__c",
    "School_Cluster__c",
    "School_Name__c",
    "Updated_School_Name_c",
    "School_Management__c",
    "School_Management_Type__c",
    "School_Village__c",
    "School_Category__c",
    "School_Location__c",
    "School_Address__c",
]

SEMANTIC = {
    "state": "School_State__c",
    "district": "School_District__c",
    "block": "School_Block__c",
    "village": "School_Village__c",
    "school_name": "School_Name__c",
    "updated_name": "Updated_School_Name_c",
    "udise": "School_Udise_Code__c",
    "management": "School_Management__c",
    "management_type": "School_Management_Type__c",
    "category": "School_Category__c",
    "location": "School_Location__c",
    "address": "School_Address__c",
    "cluster": "School_Cluster__c",
}


def _read_csv(path: Path):
    if not path.exists():
        return []

    with path.open(
        "r",
        encoding="utf-8-sig",
        newline=""
    ) as f:
        return list(csv.DictReader(f))


@st.cache_resource(show_spinner=False)
def get_index():
    if not DB.exists():
        raise FileNotFoundError(
            f"Search database not found: {DB}. "
            "Make sure data/school_search.sqlite is committed to GitHub."
        )

    return FastSchoolIndex(
        DB,
        COLUMNS,
        SEMANTIC,
        ENRICHMENT_CSV,
    )


@st.cache_data(show_spinner=False)
def get_history():
    return _read_csv(HISTORY_CSV)


@st.cache_data(show_spinner=False)
def get_enrichment():
    return _read_csv(ENRICHMENT_CSV)


def first_value(record, *keys, default=""):
    for key in keys:
        if not key:
            continue

        value = record.get(key, "")

        if value is not None and str(value).strip():
            return str(value).strip()

    return default


def merge_enrichment(record):
    result = dict(record)
    rows = get_enrichment()

    if not rows:
        return result

    code = first_value(
        result,
        SEMANTIC["udise"]
    )

    if not code:
        return result

    match = next(
        (
            row
            for row in rows
            if str(
                row.get("udise_code", "")
            ).strip() == code
        ),
        None,
    )

    if not match:
        return result

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

    for source_key, display_key in mapping.items():
        value = str(
            match.get(source_key, "")
        ).strip()

        if value:
            result[display_key] = value

    return result


def show_profile(record):
    st.title("🏫 School Profile")

    if st.button(
        "← Back to search results",
        key="back_to_results"
    ):
        st.session_state["selected_school"] = None
        st.rerun()

    school_name = first_value(
        record,
        "Verified School Name",
        SEMANTIC["updated_name"],
        SEMANTIC["school_name"],
        default="School",
    )

    village = first_value(
        record,
        SEMANTIC["village"],
        "LGD Village",
    )

    block = first_value(
        record,
        SEMANTIC["block"],
        "LGD Block",
    )

    district = first_value(
        record,
        SEMANTIC["district"]
    )

    udise = first_value(
        record,
        SEMANTIC["udise"],
        "udise_code"
    )

    st.header(school_name)

    st.markdown(
        f"""
        **V:** {html.escape(village or '—')}
        &nbsp;•&nbsp;
        **M:** {html.escape(block or '—')}
        &nbsp;•&nbsp;
        **D:** {html.escape(district or '—')}
        """
    )

    st.caption(
        f"UDISE: {udise or '—'}"
    )

    st.markdown("### School Information")

    c1, c2, c3 = st.columns(3)

    with c1:

        st.write(
            "**School Category**",
            first_value(
                record,
                "School Category",
                SEMANTIC["category"],
                default="Not verified",
            ),
        )

        st.write(
            "**School Management**",
            first_value(
                record,
                "School Management",
                SEMANTIC["management"],
                default="Not verified",
            ),
        )

        st.write(
            "**Class**",
            first_value(
                record,
                "Class",
                default="Not verified",
            ),
        )

    with c2:

        st.write(
            "**School Management Type**",
            first_value(
                record,
                SEMANTIC["management_type"],
                default="Not verified",
            ),
        )

        st.write(
            "**School Type**",
            first_value(
                record,
                "School Type",
                default="Not verified",
            ),
        )

        st.write(
            "**School Location**",
            first_value(
                record,
                "School Location",
                SEMANTIC["location"],
                default="Not verified",
            ),
        )

    with c3:

        st.write(
            "**LGD Block**",
            first_value(
                record,
                "LGD Block",
                default="Not verified",
            ),
        )

        st.write(
            "**LGD Panchayat**",
            first_value(
                record,
                "LGD Panchayat",
                default="Not verified",
            ),
        )

        st.write(
            "**LGD Village**",
            first_value(
                record,
                "LGD Village",
                default="Not verified",
            ),
        )

        st.write(
            "**PIN Code**",
            first_value(
                record,
                "PIN Code",
                default="Not verified",
            ),
        )

    st.markdown("### Address")

    st.write(
        first_value(
            record,
            "Verified Address",
            SEMANTIC["address"],
            default="Not verified",
        )
    )

    if first_value(
        record,
        "Verification Status"
    ):

        st.markdown("### Verification")

        st.write(
            "**Status:**",
            first_value(
                record,
                "Verification Status"
            )
        )

        st.write(
            "**Source:**",
            first_value(
                record,
                "Verification Source",
                default="—",
            )
        )

        st.write(
            "**Source Year:**",
            first_value(
                record,
                "Source Year",
                default="—",
            )
        )

        st.write(
            "**Last Verified:**",
            first_value(
                record,
                "Last Verified",
                default="—",
            )
        )

        source_url = first_value(
            record,
            "Verification Source URL"
        )

        if source_url:
            st.markdown(
                f"**Source URL:** {source_url}"
            )

    st.markdown("### School Identity")

    st.write(
        "**Original Excel School Name:**",
        first_value(
            record,
            SEMANTIC["school_name"],
            default="—",
        ),
    )

    st.write(
        "**Updated School Name:**",
        first_value(
            record,
            SEMANTIC["updated_name"],
            default="—",
        ),
    )

    st.write(
        "**Cluster:**",
        first_value(
            record,
            SEMANTIC["cluster"],
            default="—",
        ),
    )

    with st.expander(
        "View all original Excel fields",
        expanded=False
    ):

        for column in COLUMNS:
            st.write(
                f"**{column}:** "
                f"{record.get(column, '')}"
            )


def show_history(history_rows):

    left, right = st.columns(
        2,
        gap="large"
    )

    with left:

        with st.expander(
            "📍 Andhra Pradesh — District History",
            expanded=False
        ):

            st.caption(
                "Static reference only."
            )

            rows = [
                r
                for r in history_rows
                if str(
                    r.get("state", "")
                ).strip().casefold()
                == "andhra pradesh"
            ]

            grouped = {}

            for row in rows:

                old = str(
                    row.get(
                        "old_district",
                        ""
                    )
                ).strip()

                new = str(
                    row.get(
                        "successor_district",
                        ""
                    )
                ).strip()

                if old and new:
                    grouped.setdefault(
                        old,
                        []
                    ).append(new)

            for old in sorted(grouped):

                st.markdown(
                    f"**{old}** → "
                    f"{' • '.join(grouped[old])}"
                )

    with right:

        with st.expander(
            "📍 Telangana — District History",
            expanded=False
        ):

            st.caption(
                "Static reference only."
            )

            rows = [
                r
                for r in history_rows
                if str(
                    r.get("state", "")
                ).strip().casefold()
                == "telangana"
            ]

            grouped = {}

            for row in rows:

                old = str(
                    row.get(
                        "old_district",
                        ""
                    )
                ).strip()

                new = str(
                    row.get(
                        "successor_district",
                        ""
                    )
                ).strip()

                if old and new:
                    grouped.setdefault(
                        old,
                        []
                    ).append(new)

            for old in sorted(grouped):

                st.markdown(
                    f"**{old}** → "
                    f"{' • '.join(grouped[old])}"
                )


# =========================================================
# Load backend safely
# =========================================================

try:

    index = get_index()
    history_rows = get_history()

except Exception as exc:

    st.error(
        "The school search app could not start."
    )

    st.code(
        str(exc)
    )

    st.info(
        "Check that search_engine.py and the data folder "
        "are present in the GitHub repository. "
        "The file data/school_search.sqlite is required."
    )

    st.stop()


# =========================================================
# Global styling
# =========================================================

st.markdown(
    """
    <style>

    .block-container {
        max-width: 1280px;
        padding-top: 1.2rem;
    }

    /* Works with Streamlit light and dark themes */
    .result-card {
        border: 1px solid var(--secondary-background-color);
        border-radius: 12px;
        padding: 14px;
        margin: 8px 0 4px 0;
        background: var(--background-color);
        color: var(--text-color);
    }

    /* School name */
    .result-title {
        color: var(--text-color) !important;
        font-size: 1.04rem;
        font-weight: 700;
        line-height: 1.35;
        margin-bottom: 4px;
    }

    /* Supporting information */
    .muted {
        color: var(--text-color) !important;
        opacity: 0.75;
        font-size: 0.88rem;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Profile view
# =========================================================

selected = st.session_state.get(
    "selected_school"
)

if selected:

    show_profile(selected)

    st.stop()


# =========================================================
# Main Search
# =========================================================

st.title(
    "🏫 AP & Telangana School Identity Search"
)

st.caption(
    "Select State first. District and Village are optional filters. "
    "Results show the top 3 matches."
)

left, right = st.columns(
    [2.15, 1.65],
    gap="large"
)


# =========================================================
# LEFT SIDE
# =========================================================

with left:

    st.subheader(
        "Find Your School"
    )

    indexed_states = {
        str(value).strip().casefold():
        str(value).strip()
        for value in index.states()
    }

    display_states = [
        "Andhra Pradesh",
        "Telangana",
    ]

    available_states = [
        state
        for state in display_states
        if state.casefold() in indexed_states
    ]

    # -------------------------
    # State
    # -------------------------

    state = st.selectbox(
        "1. State *",
        ["Select State"] + available_states,
        key="state_filter",
    )

    # -------------------------
    # No state selected
    # -------------------------

    if state == "Select State":

        st.selectbox(
            "2. District",
            ["Select State first"],
            disabled=True,
            key="district_disabled",
        )

        st.selectbox(
            "3. Village",
            ["Select District first"],
            disabled=True,
            key="village_disabled",
        )

        with st.form(
            "search_form_disabled"
        ):

            st.text_input(
                "4. Search",
                placeholder=(
                    "School name, short name, "
                    "UDISE code, etc."
                ),
                disabled=True,
            )

            st.form_submit_button(
                "SEARCH",
                disabled=True,
                use_container_width=True,
            )

        st.info(
            "State is mandatory. "
            "Select Andhra Pradesh or Telangana "
            "to continue."
        )

    # -------------------------
    # State selected
    # -------------------------

    else:

        state_db = indexed_states[
            state.casefold()
        ]

        # ---------------------
        # District
        # ---------------------

        districts = index.districts(
            state_db
        )

        district = st.selectbox(
            "2. District",
            ["All Districts"] + districts,
            key=f"district_{state_db}",
        )

        # ---------------------
        # Village
        # ---------------------

        if district == "All Districts":

            village_db = ""

            st.selectbox(
                "3. Village",
                ["Select District first"],
                disabled=True,
                key=f"village_disabled_{state_db}",
            )

        else:

            villages = index.villages(
                state_db,
                district
            )

            village = st.selectbox(
                "3. Village",
                ["All Villages"] + villages,
                key=(
                    f"village_"
                    f"{state_db}_"
                    f"{district}"
                ),
            )

            village_db = (
                ""
                if village == "All Villages"
                else village
            )

        # ---------------------
        # Search box
        # ---------------------

        with st.form(
            "search_form"
        ):

            query = st.text_input(
                "4. Search",
                placeholder=(
                    "School name, short name, "
                    "UDISE code, etc."
                ),
            )

            search_clicked = st.form_submit_button(
                "SEARCH",
                type="primary",
                use_container_width=True,
            )

        # ---------------------
        # Advanced search
        # ---------------------

        with st.expander(
            "Advanced Search",
            expanded=False
        ):

            st.caption(
                "Additional filters can be added later "
                "without changing the fast indexed search."
            )

        # ---------------------
        # Run search
        # ---------------------

        if search_clicked:

            st.session_state["results"] = (
                index.search(
                    query,
                    state_db,
                    district
                    if district != "All Districts"
                    else "",
                    village_db,
                    limit=3,
                )
            )

            st.session_state[
                "selected_school"
            ] = None

        results = st.session_state.get(
            "results"
        )

        # ---------------------
        # Results
        # ---------------------

        if results is not None:

            st.subheader(
                "Top 3 Results"
            )

            if not results:

                st.info(
                    "No matching school found."
                )

            for number, record in enumerate(
                results,
                start=1
            ):

                name = first_value(
                    record,
                    SEMANTIC["updated_name"],
                    SEMANTIC["school_name"],
                    default="School",
                )

                village_name = first_value(
                    record,
                    SEMANTIC["village"]
                )

                block_name = first_value(
                    record,
                    SEMANTIC["block"]
                )

                district_name = first_value(
                    record,
                    SEMANTIC["district"]
                )

                udise = first_value(
                    record,
                    SEMANTIC["udise"]
                )

                management = first_value(
                    record,
                    SEMANTIC["management"],
                    default="Not available",
                )

                management_type = first_value(
                    record,
                    SEMANTIC["management_type"],
                    default="Not available",
                )

                # -----------------
                # Result card
                # -----------------

                st.markdown(
                    f"""
                    <div class="result-card">

                        <div class="result-title">
                            {number}. {html.escape(name)}
                        </div>

                        <span class="muted">
                            <b>V:</b>
                            {html.escape(village_name or '—')}

                            &nbsp;•&nbsp;

                            <b>M:</b>
                            {html.escape(block_name or '—')}

                            &nbsp;•&nbsp;

                            <b>D:</b>
                            {html.escape(district_name or '—')}
                        </span>

                        <br>

                        <span class="muted">
                            <b>UDISE:</b>
                            {html.escape(
                                udise or
                                "Not available"
                            )}
                        </span>

                        <br>

                        <span class="muted">
                            <b>Management:</b>
                            {html.escape(
                                management
                            )}
                        </span>

                        <br>

                        <span class="muted">
                            <b>Management Type:</b>
                            {html.escape(
                                management_type
                            )}
                        </span>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                # -----------------
                # View profile
                # -----------------

                if st.button(
                    "View full school details →",
                    key=(
                        f"view_school_"
                        f"{number}_"
                        f"{udise or 'no_udise'}"
                    ),
                    use_container_width=True,
                ):

                    st.session_state[
                        "selected_school"
                    ] = merge_enrichment(
                        record
                    )

                    st.rerun()


# =========================================================
# RIGHT SIDE
# =========================================================

with right:

    show_history(
        history_rows
    )


# =========================================================
# Footer
# =========================================================

st.divider()

st.caption(
    "Original Excel dataset is preserved unchanged. "
    "SQLite is used as the fast read-only search index."
)
