                key=f"village_{state_db}_{district}",
            )
            village_db = "" if village == "All Villages" else village

        with st.form("search_form"):
            q = st.text_input(
                "4. Search",
                placeholder="School name, short name, UDISE code, etc.",
            )
            go = st.form_submit_button(
                "SEARCH",
                type="primary",
                use_container_width=True,
            )

        with st.expander("Advanced Search", expanded=False):
            st.caption("Additional filters can be added here later.")

        if go:
            results = idx.search(
                q,
                state_db,
                district if district != "All Districts" else "",
                village_db,
                limit=3,
            )
            st.session_state["results"] = results
            st.session_state["selected_school"] = None

        results = st.session_state.get("results")

        if results is not None:
            st.subheader("Top 3 Results")

            if not results:
                st.info("No matching school found.")

            for i, record in enumerate(results, start=1):
                name = first_value(
                    record,
                    sem.get("updated_name"),
                    sem.get("school_name"),
                    default="School",
                )
                village_name = first_value(record, sem.get("village"))
                block_name = first_value(record, sem.get("block"))
                district_name = first_value(record, sem.get("district"))
                udise = first_value(record, sem.get("udise"))

                # IMPORTANT: read management + management type directly from Excel fields.
                management = first_value(
                    record,
                    sem.get("management"),
                    "School_Management__c",
                    default="Not available",
                )
                management_type = first_value(
                    record,
                    sem.get("management_type"),
                    "School_Management_Type__c",
                    default="Not available",
                )

                st.markdown(
                    f"""
                    <div class="result-card">
                        <b>{i}. {name}</b><br>
                        <span class="muted">
                            <b>V:</b> {village_name or '—'} &nbsp;•&nbsp;
                            <b>M:</b> {block_name or '—'} &nbsp;•&nbsp;
                            <b>D:</b> {district_name or '—'}
                        </span><br>
                        <span class="muted">UDISE: {udise or 'Not available'}</span><br>
                        <span class="muted">Management: {management}</span><br>
                        <span class="muted">Management Type: {management_type}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

                if st.button(
                    "View full school details →",
                    key=f"view_school_{i}_{udise or 'no_udise'}",
                    use_container_width=True,
                ):
                    st.session_state["selected_school"] = merge_enrichment(record)
                    st.rerun()


with right:
    with st.expander(
        "📍 Andhra Pradesh — District History",
        expanded=False,
    ):
        ap = hist[hist["state"].astype(str).str.casefold() == "andhra pradesh"]
        for old in sorted(ap["old_district"].dropna().astype(str).unique()):
            successors = ap.loc[
                ap["old_district"].astype(str) == old,
                "successor_district",
            ].dropna().astype(str).tolist()
            st.markdown(f"**{old}** → {' • '.join(successors)}")

    with st.expander(
        "📍 Telangana — District History",
        expanded=False,
    ):
        tg = hist[hist["state"].astype(str).str.casefold() == "telangana"]
        for old in sorted(tg["old_district"].dropna().astype(str).unique()):
            successors = tg.loc[
                tg["old_district"].astype(str) == old,
                "successor_district",
            ].dropna().astype(str).tolist()
            st.markdown(f"**{old}** → {' • '.join(successors)}")


st.divider()
st.caption(
    "Original Excel is preserved unchanged. SQLite is the read-only search accelerator."
)
