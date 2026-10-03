                name = (
                    r.get(sem["updated_name"], "")
                    or r.get(sem["school_name"], "")
                    or "School"
                )

                v = r.get(sem["village"], "") if sem["village"] else ""
                m = r.get(sem["block"], "") if sem["block"] else ""
                d = r.get(sem["district"], "") if sem["district"] else ""
                ud = r.get(sem["udise"], "") if sem["udise"] else ""

                st.markdown(
                    f"""
                    <div class="result">
                        <b>{i}. {name}</b><br>
                        <span class="muted">
                            <b>V:</b> {v or "—"} &nbsp;•&nbsp;
                            <b>M:</b> {m or "—"} &nbsp;•&nbsp;
                            <b>D:</b> {d or "—"}
                        </span><br>
                        <span class="muted">UDISE: {ud or "Not available"}</span>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                if st.button(
                    "View full school details →",
                    key=f"view_{ud or i}",
                    use_container_width=True
                ):
                    st.session_state["selected_school"] = merge_enrichment(r)
                    st.session_state["selected_school_udise"] = str(ud or "")
                    st.rerun()

        selected = st.session_state.get("selected_school")

        if selected:
            if st.button("← Back to search results", key="back_to_results"):
                st.session_state["selected_school"] = None
                st.session_state["selected_school_udise"] = None
                st.rerun()
            st.divider()
            st.subheader("School Profile")

            school_name = (
                selected.get(sem["updated_name"], "")
                or selected.get(sem["school_name"], "")
                or "School"
            )
            st.markdown(f"### {school_name}")

            v = selected.get(sem["village"], "") if sem["village"] else ""
            m = selected.get(sem["block"], "") if sem["block"] else ""
            d = selected.get(sem["district"], "") if sem["district"] else ""
            ud = selected.get(sem["udise"], "") if sem["udise"] else ""

            st.markdown(
                f"**V:** {v or '—'} &nbsp; • &nbsp; "
                f"**M:** {m or '—'} &nbsp; • &nbsp; "
                f"**D:** {d or '—'} &nbsp; • &nbsp; "
                f"**UDISE:** {ud or '—'}"
            )

            st.markdown("#### School Information")

            a, b, c = st.columns(3)

            with a:
                st.write("**School Category**", selected.get("School Category") or selected.get("School_Category__c") or "Not verified")
                st.write("**School Management**", selected.get("School Management") or selected.get("School_Management__c") or "Not verified")
                st.write("**Class**", selected.get("Class") or "Not verified")

            with b:
                st.write("**School Type**", selected.get("School Type") or selected.get("School_Type__c") or selected.get("School_Type") or "Not verified")
                st.write("**School Location**", selected.get("School Location") or selected.get("School_Location__c") or "Not verified")
                st.write("**LGD Block**", selected.get("LGD Block") or "Not verified")

            with c:
                st.write("**LGD Panchayat**", selected.get("LGD Panchayat") or "Not verified")
                st.write("**LGD Village**", selected.get("LGD Village") or "Not verified")
                st.write("**PIN Code**", selected.get("PIN Code") or "Not verified")

            st.markdown("#### Address")
            st.write(selected.get("Verified Address") or selected.get("School_Address__c") or "Not verified")

            if selected.get("Verification Status"):
                st.markdown("#### Verification")
                st.write("**Status:**", selected.get("Verification Status"))
                st.write("**Source:**", selected.get("Verification Source") or "—")
                st.write("**Source Year:**", selected.get("Source Year") or "—")
                st.write("**Last Verified:**", selected.get("Last Verified") or "—")
                if selected.get("Verification Source URL"):
                    st.markdown(f"**Source:** {selected.get('Verification Source URL')}")

            st.markdown("#### School Identity")
            st.write("**Original Excel School Name:**", selected.get("School_Name__c") or "—")
            st.write("**Updated School Name:**", selected.get("Updated_School_Name_c") or "—")
            st.write("**Cluster:**", selected.get("School_Cluster__c") or "—")

            with st.expander("View all original Excel fields"):
                for col in cols:
                    st.write(f"**{col}:** {selected.get(col, '')}")

with right:
    with st.expander("📍 Andhra Pradesh — District History", expanded=False):
        st.caption("Static reference only.")
        x = hist[hist["state"] == "Andhra Pradesh"]
        for old in sorted(x["old_district"].dropna().unique()):
            vals = x.loc[x["old_district"] == old, "successor_district"].tolist()
            st.markdown(f"**{old}** → {' • '.join(vals)}")

    with st.expander("📍 Telangana — District History", expanded=False):
        st.caption("Static reference only.")
        x = hist[hist["state"] == "Telangana"]
        for old in sorted(x["old_district"].dropna().unique()):
            vals = x.loc[x["old_district"] == old, "successor_district"].tolist()
            st.markdown(f"**{old}** → {' • '.join(vals)}")

st.divider()
st.caption("Original Excel is preserved unchanged. SQLite is the read-only search accelerator.")
