from common import *

init_page("HARA AI Assistant — Requirements")
page_header("SAFETY REQUIREMENTS", "Requirements", "Safety Goal, FSR, TSR and deterministic requirement quality checks.")

# 7. FUNCTIONAL SAFETY REQUIREMENTS (FSR)
# =========================================================

st.header(
    "7. Functional Safety Requirements (FSR)"
)

st.write(
    "Generate candidate Functional Safety Requirements "
    "automatically from the selected Safety Goal, HARA "
    "information and Candidate ASIL."
)

fsr_context_ready = (
    "safety_goal_result" in st.session_state
    and st.session_state.get("asil_assessment_completed", False)
    and st.session_state.get("safety_goal_hara_key")
    == st.session_state.get("active_hara_key")
)

if not fsr_context_ready:

    st.warning(
        "Complete S/E/C → Candidate ASIL → Safety Goal first. "
        "FSRs will then be available."
    )

else:

    safety_goal_data = st.session_state[
        "safety_goal_result"
    ]

    if (
        "candidate_asil" not in st.session_state
        or "asil_severity" not in st.session_state
        or "asil_exposure" not in st.session_state
        or "asil_controllability" not in st.session_state
    ):

        st.warning(
            "Complete the S/E/C assessment and Candidate ASIL "
            "calculation before generating FSRs."
        )

    else:

        with st.container(border=True):

            st.markdown(
                "### FSR Traceability Context"
            )

            st.write(
                f"**Safety Goal:** "
                f"{safety_goal_data['safety_goal']}"
            )

            st.write(
                f"**Candidate ASIL:** "
                f"{safety_goal_data['candidate_asil']}"
            )

            st.write(
                f"**S/E/C:** "
                f"{st.session_state['asil_severity']} / "
                f"{st.session_state['asil_exposure']} / "
                f"{st.session_state['asil_controllability']}"
            )

            st.write(
                f"**Hazard:** "
                f"{safety_goal_data['hazard']}"
            )

            st.write(
                f"**Hazardous Event:** "
                f"{safety_goal_data['hazardous_event']}"
            )

        if st.button(
            "🛡️ Generate Functional Safety Requirements",
            type="primary"
        ):

            with st.spinner(
                "Generating candidate Functional Safety Requirements..."
            ):

                fsr_results = generate_fsr(
                    system=safety_goal_data["system"],
                    function=safety_goal_data["function"],
                    malfunction=safety_goal_data.get(
                        "malfunction",
                        "Identified malfunction"
                    ),
                    hazard=safety_goal_data["hazard"],
                    hazardous_event=safety_goal_data[
                        "hazardous_event"
                    ],
                    safety_goal=safety_goal_data[
                        "safety_goal"
                    ],
                    candidate_asil=safety_goal_data[
                        "candidate_asil"
                    ]
                )

            st.session_state[
                "fsr_results"
            ] = fsr_results

            log_audit_event(
                event="Functional Safety Requirements generated",
                details=(
                    f"{len(fsr_results)} candidate FSR(s) generated "
                    f"from Safety Goal {safety_goal_data.get('id', 'SG-001')}."
                ),
                asil=safety_goal_data.get("candidate_asil"),
                safety_goal_id=safety_goal_data.get("id", "SG-001"),
            )

        if "fsr_results" in st.session_state:

            fsr_results = st.session_state[
                "fsr_results"
            ]

            st.success(
                f"{len(fsr_results)} candidate Functional "
                "Safety Requirement(s) generated."
            )

            for fsr in fsr_results:

                with st.container(border=True):

                    st.markdown(
                        f"### {fsr['id']}"
                    )

                    st.write(
                        f"**Requirement:** "
                        f"{fsr['requirement']}"
                    )

                    st.write(
                        f"**Rationale:** "
                        f"{fsr['rationale']}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.write(
                            f"**ASIL:** "
                            f"{fsr['candidate_asil']}"
                        )

                    with col2:

                        st.write(
                            "**Review Status:** "
                            f"{fsr['review_status']}"
                        )

                    with col3:

                        st.write(
                            f"**Source Hazard:** "
                            f"{fsr['hazard']}"
                        )

                    with st.expander(
                        "🔗 Traceability Details"
                    ):

                        st.write(
                            f"**System:** "
                            f"{fsr['system']}"
                        )

                        st.write(
                            f"**Function:** "
                            f"{fsr['function']}"
                        )

                        st.write(
                            f"**Malfunction:** "
                            f"{fsr['malfunction']}"
                        )

                        st.write(
                            f"**Hazardous Event:** "
                            f"{fsr['hazardous_event']}"
                        )

                        st.write(
                            f"**Linked Safety Goal:** "
                            f"{fsr['safety_goal']}"
                        )

            st.info(
                "These FSRs are AI-assisted candidate drafts. "
                "They must be reviewed, refined and approved "
                "by an authorized functional-safety engineer "
                "before being used as official safety requirements."
            )


# =========================================================
# 8. TECHNICAL SAFETY REQUIREMENTS (TSR)
# =========================================================

st.header(
    "8. Technical Safety Requirements (TSR)"
)

st.write(
    "Generate candidate Technical Safety Requirements from the "
    "selected Functional Safety Requirement."
)

tsr_context_ready = (
    "safety_goal_result" in st.session_state
    and st.session_state.get("asil_assessment_completed", False)
    and st.session_state.get("safety_goal_hara_key")
    == st.session_state.get("active_hara_key")
    and "fsr_results" in st.session_state
    and bool(st.session_state.get("fsr_results"))
)

if not tsr_context_ready:
    st.warning(
        "Complete S/E/C → Candidate ASIL → Safety Goal → FSR first. "
        "TSRs will then be available."
    )
else:
    safety_goal_data = st.session_state["safety_goal_result"]
    fsr_results = st.session_state["fsr_results"]

    st.markdown("### Select FSR for Technical Decomposition")

    fsr_labels = [
        f"{fsr['id']} — {fsr['requirement']}"
        for fsr in fsr_results
    ]

    selected_fsr_label = st.selectbox(
        "Select Functional Safety Requirement",
        ["-- Select an FSR --"] + fsr_labels,
        index=0,
        key="tsr_fsr_selection"
    )

    if selected_fsr_label == "-- Select an FSR --":
        st.info(
            "Select an FSR to generate its candidate technical requirements."
        )
    else:
        selected_fsr_position = fsr_labels.index(selected_fsr_label)
        selected_fsr = fsr_results[selected_fsr_position]

        with st.container(border=True):
            st.markdown("### Selected FSR")
            st.write(
                f"**{selected_fsr['id']}:** "
                f"{selected_fsr['requirement']}"
            )
            st.write(
                f"**Candidate ASIL:** {selected_fsr['candidate_asil']}"
            )
            st.write(
                f"**Linked Safety Goal:** "
                f"{selected_fsr['safety_goal']}"
            )

        if st.button(
            "⚙️ Generate Technical Safety Requirements",
            type="primary",
            key="generate_tsr_button"
        ):
            with st.spinner(
                "Generating candidate Technical Safety Requirements..."
            ):
                tsr_results = generate_tsr(
                    system=selected_fsr["system"],
                    function=selected_fsr["function"],
                    malfunction=selected_fsr["malfunction"],
                    hazard=selected_fsr["hazard"],
                    hazardous_event=selected_fsr["hazardous_event"],
                    safety_goal=selected_fsr["safety_goal"],
                    fsr=selected_fsr["requirement"],
                    candidate_asil=selected_fsr["candidate_asil"]
                )

            st.session_state["tsr_results"] = tsr_results
            st.session_state["tsr_fsr_id"] = selected_fsr["id"]

            log_audit_event(
                event="Technical Safety Requirements generated",
                details=(
                    f"{len(tsr_results)} candidate TSR(s) generated "
                    f"from selected {selected_fsr['id']}."
                ),
                asil=selected_fsr.get("candidate_asil"),
                safety_goal_id=safety_goal_data.get("id", "SG-001"),
                fsr_id=selected_fsr.get("id"),
                tsr_ids=[
                    tsr.get("id", "")
                    for tsr in tsr_results
                ],
            )

        tsr_is_current = (
            "tsr_results" in st.session_state
            and st.session_state.get("tsr_fsr_id")
            == selected_fsr["id"]
        )

        if tsr_is_current:
            tsr_results = st.session_state["tsr_results"]

            st.success(
                f"{len(tsr_results)} candidate Technical Safety "
                "Requirement(s) generated."
            )

            for tsr in tsr_results:
                with st.container(border=True):
                    st.markdown(f"### {tsr['id']}")

                    st.write(
                        f"**Technical Requirement:** "
                        f"{tsr['requirement']}"
                    )

                    st.write(
                        f"**Rationale:** {tsr['rationale']}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(
                            f"**ASIL:** {tsr['candidate_asil']}"
                        )

                    with col2:
                        st.write(
                            f"**Review Status:** "
                            f"{tsr['review_status']}"
                        )

                    with col3:
                        st.write(
                            f"**Linked FSR:** {selected_fsr['id']}"
                        )

                    with st.expander("🔗 Traceability Details"):
                        st.write(
                            f"**System:** {tsr['system']}"
                        )
                        st.write(
                            f"**Function:** {tsr['function']}"
                        )
                        st.write(
                            f"**Malfunction:** {tsr['malfunction']}"
                        )
                        st.write(
                            f"**Hazard:** {tsr['hazard']}"
                        )
                        st.write(
                            f"**Hazardous Event:** "
                            f"{tsr['hazardous_event']}"
                        )
                        st.write(
                            f"**Safety Goal:** {tsr['safety_goal']}"
                        )
                        st.write(
                            f"**FSR:** {tsr['fsr']}"
                        )

            st.info(get_tsr_review_note())


# =========================================================
# 9. REQUIREMENT QUALITY CHECKS
# =========================================================

st.header(
    "9. Requirement Quality Checks"
)

st.write(
    "Deterministic checks for candidate Functional Safety Requirements "
    "and Technical Safety Requirements."
)

quality_fsr_results = st.session_state.get("fsr_results", [])
quality_tsr_results = st.session_state.get("tsr_results", [])
quality_tsr_fsr_id = st.session_state.get("tsr_fsr_id")

quality_tsr_results = (
    quality_tsr_results
    if quality_tsr_fsr_id is not None
    else []
)

quality_context_ready = bool(quality_fsr_results) or bool(quality_tsr_results)

if not quality_context_ready:

    st.caption(
        "Requirement quality checks will be available after candidate "
        "FSR or TSR requirements are generated."
    )

else:

    quality_scope = st.radio(
        "Requirement set",
        ["Selected FSR", "Generated TSRs"],
        horizontal=True,
        key="requirement_quality_scope"
    )

    if quality_scope == "Selected FSR":

        selected_quality_fsr_id = st.session_state.get("tsr_fsr_id")
        selected_quality_fsr = next(
            (
                fsr for fsr in quality_fsr_results
                if fsr.get("id") == selected_quality_fsr_id
            ),
            None
        )

        if selected_quality_fsr is None:
            selected_quality_fsr = quality_fsr_results[0]

        quality_requirements = [selected_quality_fsr]
        st.caption(
            f"Checking selected FSR: {selected_quality_fsr.get('id', 'FSR-001')}"
        )

    else:

        quality_requirements = quality_tsr_results

        if not quality_requirements:
            st.caption(
                "Generate TSRs first to run quality checks on the technical requirements."
            )

    if quality_requirements:

        quality_results = check_requirements_quality(quality_requirements)

        total_pass = sum(item["passed"] for item in quality_results)
        total_review = sum(item["review"] for item in quality_results)
        total_fail = sum(item["failed"] for item in quality_results)

        qcol1, qcol2, qcol3, qcol4 = st.columns(4)

        with qcol1:
            st.metric("Requirements", len(quality_results))

        with qcol2:
            st.metric("PASS Checks", total_pass)

        with qcol3:
            st.metric("Review Checks", total_review)

        with qcol4:
            st.metric("Failed Checks", total_fail)

        st.divider()

        for result in quality_results:

            with st.container(border=True):

                st.markdown(
                    f"### {result['id']} — {result['overall']}"
                )

                st.write(
                    f"**Requirement:** {result['requirement']}"
                )

                check_rows = [
                    {
                        "Quality Check": check["Check"],
                        "Status": check["Status"],
                        "Details": check["Details"]
                    }
                    for check in result["checks"]
                ]

                st.dataframe(
                    check_rows,
                    use_container_width=True,
                    hide_index=True
                )

        if st.button(
            "🧾 Record Quality Check in Audit History",
            key="record_quality_audit_button"
        ):
            log_audit_event(
                event="Requirement quality check recorded",
                details=(
                    f"Checked {len(quality_results)} requirement(s) in "
                    f"scope '{quality_scope}'. PASS={total_pass}, "
                    f"REVIEW={total_review}, FAIL={total_fail}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=st.session_state.get(
                    "safety_goal_result", {}
                ).get("id", "SG-001"),
                fsr_id=(
                    st.session_state.get("tsr_fsr_id")
                    if quality_scope == "Selected FSR"
                    else None
                ),
                tsr_ids=(
                    [
                        item.get("id", "")
                        for item in quality_tsr_results
                    ]
                    if quality_scope == "Generated TSRs"
                    else []
                ),
            )
            st.success("Quality-check event recorded in audit history.")

        st.info(get_requirement_quality_review_note())


# =========================================================
