                placeholder="School name, short name, UDISE code, etc.",
                disabled=True,
            )
            st.form_submit_button(
                "SEARCH",
                disabled=True,
                use_container_width=True,
            )
        st.info("State is mandatory. Select Andhra Pradesh or Telangana to continue.")

    else:
        state_db = indexed_states[state.casefold()]

        districts = index.districts(state_db)
        district = st.selectbox(
            "2. District",
            ["All Districts"] + districts,
            key=f"district_{state_db}",
        )

        if district == "All Districts":
            village_db = ""
            st.selectbox(
                "3. Village",
                ["Select District first"],
                disabled=True,
                key=f"village_disabled_{state_db}",
            )
        else:
            villages = index.villages(state_db, district)
            village = st.selectbox(
                "3. Village",
                ["All Villages"] + villages,
                key=f"village_{state_db}_{district}",
            )
            village_db = "" if village == "All Villages" else village

        with st.form("search_form"):
            query = st.text_input(
                "4. Search",
                placeholder="School name, short name, UDISE code, etc.",
            )
            search_clicked = st.form_submit_button(
                "SEARCH",
                type="primary",
                use_container_width=True,
            )

        with st.expander("Advanced Search", expanded=False):
            st.caption("Additional filters can be added later without changing the fast indexed search.")

        if search_clicked:
            st.session_state["results"] = index.search(
                query,
                state_db,
                district if district != "All Districts" else "",
                village_db,
                limit=3,
            )
            st.session_state["selected_school"] = None

        results = st.session_state.get("results")

        if results is not None:
            st.subheader("Top 3 Results")

            if not results:
                st.info("No matching school found.")

            for number, record in enumerate(results, start=1):
                name = first_value(
                    record,
                    SEMANTIC["updated_name"],
                    SEMANTIC["school_name"],
                    default="School",
                )
                village_name = first_value(record, SEMANTIC["village"])
                block_name = first_value(record, SEMANTIC["block"])
                district_name = first_value(record, SEMANTIC["district"])
                udise = first_value(record, SEMANTIC["udise"])
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

                with st.container(border=True):
                    st.markdown(f"### {name}")
                    st.markdown(
                        f"**V:** {village_name or '—'} "
                        f"• **M:** {block_name or '—'} "
                        f"• **D:** {district_name or '—'}"
                    )
                    st.write(f"**UDISE:** {udise or 'Not available'}")
                    st.write(f"**Management:** {management}")
                    st.write(f"**Management Type:** {management_type}")

                if st.button(
                    "View full school details →",
                    key=f"view_school_{number}_{udise or 'no_udise'}",
                    use_container_width=True,
                ):
                    st.session_state["selected_school"] = merge_enrichment(record)
                    st.rerun()

with right:
    show_history(history_rows)

st.divider()
st.caption(
    "Original Excel dataset is preserved unchanged. SQLite is used as the fast read-only search index."
)
