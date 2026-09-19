from common import *

init_page("HARA AI Assistant — Review & Audit")
page_header("GOVERNANCE", "Review & Audit", "Engineering review, verification evidence and decision history.")

# 11. DECISION HISTORY / AUDIT EVIDENCE
# =========================================================

st.header(
    "11. Decision History / Audit Evidence"
)

st.write(
    "Reviewable history of AI-assisted engineering actions and "
    "decision context recorded during the current project workflow."
)

audit_history = load_audit_history(AUDIT_HISTORY_PATH)

if not audit_history:

    st.caption(
        "No audit events have been recorded yet. Complete HARA, ASIL, "
        "Safety Goal, FSR or TSR actions to build the decision history."
    )

else:

    audit_col1, audit_col2, audit_col3 = st.columns(3)

    with audit_col1:
        st.metric("Recorded Events", len(audit_history))

    with audit_col2:
        unique_events = len(
            {
                item.get("event", "")
                for item in audit_history
            }
        )
        st.metric("Event Types", unique_events)

    with audit_col3:
        latest_event = audit_history[0].get(
            "event",
            "—"
        )
        st.metric("Latest Action", latest_event)

    st.divider()

    audit_rows = []

    for item in audit_history:

        audit_rows.append(
            {
                "Timestamp (UTC)": item.get(
                    "timestamp_utc",
                    ""
                ),
                "Event": item.get(
                    "event",
                    ""
                ),
                "Details": item.get(
                    "details",
                    ""
                ),
                "HARA": item.get(
                    "HARA ID",
                    ""
                ),
                "ASIL": item.get(
                    "ASIL",
                    ""
                ),
                "Safety Goal": item.get(
                    "Safety Goal ID",
                    ""
                ),
                "FSR": item.get(
                    "FSR ID",
                    ""
                ),
                "TSRs": item.get(
                    "TSR IDs",
                    ""
                ),
            }
        )

    st.dataframe(
        audit_rows,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Audit Report")

    st.caption(
        "Human-readable project report for documentation and engineering review."
    )

    audit_report_pdf = create_audit_report_pdf(audit_history)

    st.download_button(
        "📄 Download Audit Report (PDF)",
        data=audit_report_pdf,
        file_name="HARA_AI_Assistant_Audit_Report.pdf",
        mime="application/pdf",
    )

    with st.expander(
        "Advanced: Export Raw Audit Data (JSON)",
        expanded=False
    ):
        st.download_button(
            "Download audit_history.json",
            data=json.dumps(
                list(reversed(audit_history)),
                indent=2,
                ensure_ascii=False
            ),
            file_name="hara_audit_history.json",
            mime="application/json",
        )

    if st.button(
        "🗑️ Clear Audit History",
        key="clear_audit_history_button"
    ):
        clear_audit_history(AUDIT_HISTORY_PATH)
        st.success("Audit history cleared.")
        st.rerun()

st.info(
    get_audit_review_note()
)



# =========================================================
# 12. ENGINEERING REVIEW / APPROVAL WORKFLOW
# =========================================================

st.header(
    "12. Engineering Review / Approval Workflow"
)

st.write(
    "Review and record an authorized functional-safety engineer's decision "
    "for generated safety artifacts."
)

st.caption(
    "The application does not autonomously approve safety artifacts. "
    "Only the authorized engineer can record the review decision."
)

review_decisions = load_review_decisions(REVIEW_DECISIONS_PATH)

review_fsr_results = st.session_state.get("fsr_results", [])
review_tsr_results = st.session_state.get("tsr_results", [])
review_safety_goal = st.session_state.get("safety_goal_result")

review_artifacts = []

if review_safety_goal:
    review_artifacts.append(
        (
            "Safety Goal",
            review_safety_goal.get("id", "SG-001"),
            review_safety_goal.get("safety_goal", ""),
        )
    )

for fsr in review_fsr_results:
    review_artifacts.append(
        (
            "FSR",
            fsr.get("id", "FSR-001"),
            fsr.get("requirement", ""),
        )
    )

for tsr in review_tsr_results:
    review_artifacts.append(
        (
            "TSR",
            tsr.get("id", "TSR-001"),
            tsr.get("requirement", ""),
        )
    )

if not review_artifacts:

    st.caption(
        "Generate a Safety Goal, FSR or TSR first. Review decisions will "
        "then be available for each generated artifact."
    )

else:

    review_labels = [
        f"{artifact_type} — {artifact_id}"
        for artifact_type, artifact_id, _ in review_artifacts
    ]

    selected_review_label = st.selectbox(
        "Select artifact to review",
        review_labels,
        key="review_artifact_selection",
    )

    selected_review_index = review_labels.index(selected_review_label)
    selected_review_type, selected_review_id, selected_review_text = (
        review_artifacts[selected_review_index]
    )

    latest_review = get_latest_review_decision(
        review_decisions,
        selected_review_type,
        selected_review_id,
    )

    st.markdown(
        f"### {selected_review_type} — {selected_review_id}"
    )

    st.write(
        f"**Candidate text:** {selected_review_text}"
    )

    if latest_review:
        st.write(
            f"**Current recorded decision:** "
            f"{latest_review.get('decision', 'Pending Review')}"
        )
        st.caption(
            f"Last reviewed by {latest_review.get('reviewer_name', '—')} "
            f"at {latest_review.get('timestamp_utc', '—')}"
        )
        if latest_review.get("comment"):
            st.caption(
                f"Last review comment: {latest_review['comment']}"
            )
    else:
        st.write("**Current recorded decision:** Pending Review")

    reviewer_name = st.text_input(
        "Authorized reviewer name",
        key="reviewer_name_input",
        placeholder="Enter functional-safety engineer name",
    )

    reviewer_confirmed = st.checkbox(
        "I confirm that I am an authorized functional-safety engineer "
        "performing this review.",
        key="reviewer_authorization_confirmed",
    )

    review_decision = st.radio(
        "Engineering review decision",
        [
            "Reviewed — Accept for engineering use",
            "Reviewed — Return for revision",
            "Reviewed — Reject",
        ],
        horizontal=True,
        key="review_decision_input",
    )

    review_comment = st.text_area(
        "Review comment",
        key="review_comment_input",
        placeholder="Record the review rationale, changes requested, or acceptance note.",
    )

    if st.button(
        "📝 Record Engineering Review Decision",
        type="primary",
        key="record_engineering_review_button",
    ):

        if not reviewer_name.strip():
            st.warning(
                "Enter the authorized reviewer's name before recording the decision."
            )

        elif not reviewer_confirmed:
            st.warning(
                "Confirm authorized functional-safety engineer status before "
                "recording the review decision."
            )

        else:

            saved_decision = save_review_decision(
                path=REVIEW_DECISIONS_PATH,
                artifact_type=selected_review_type,
                artifact_id=selected_review_id,
                decision=review_decision,
                reviewer_name=reviewer_name,
                comment=review_comment,
            )

            log_audit_event(
                event="Engineering review decision recorded",
                details=(
                    f"{selected_review_type} {selected_review_id}: "
                    f"{review_decision}. Reviewer={reviewer_name.strip()}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=(
                    review_safety_goal.get("id", "SG-001")
                    if review_safety_goal
                    else None
                ),
                fsr_id=(
                    selected_review_id
                    if selected_review_type == "FSR"
                    else st.session_state.get("tsr_fsr_id")
                ),
                tsr_ids=(
                    [
                        item.get("id", "")
                        for item in review_tsr_results
                    ]
                    if selected_review_type == "TSR"
                    else []
                ),
            )

            st.success(
                f"Review decision recorded for "
                f"{selected_review_type} {selected_review_id}."
            )
            st.rerun()

    st.divider()

    st.markdown("### Review Status Overview")

    overview_rows = []

    for artifact_type, artifact_id, _ in review_artifacts:

        latest = get_latest_review_decision(
            review_decisions,
            artifact_type,
            artifact_id,
        )

        overview_rows.append(
            {
                "Artifact": f"{artifact_type} — {artifact_id}",
                "Status": (
                    latest.get("decision", "Pending Review")
                    if latest
                    else "Pending Review"
                ),
                "Reviewer": (
                    latest.get("reviewer_name", "")
                    if latest
                    else ""
                ),
                "Last Updated (UTC)": (
                    latest.get("timestamp_utc", "")
                    if latest
                    else ""
                ),
            }
        )

    st.dataframe(
        overview_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "📄 Export Review Decisions (JSON)",
        data=json.dumps(
            review_decisions,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="review_decisions.json",
        mime="application/json",
    )

    if st.button(
        "🗑️ Clear Review Decisions",
        key="clear_review_decisions_button",
    ):
        clear_review_decisions(REVIEW_DECISIONS_PATH)
        st.rerun()

    st.info(get_review_note())



# =========================================================
# 13. VERIFICATION EVIDENCE MAPPING
# =========================================================

st.header("13. Verification Evidence Mapping")

st.write(
    "Record verification evidence and link it to a generated safety "
    "requirement for end-to-end engineering traceability."
)

st.caption(
    "This is a traceability aid. Recorded verification results do not "
    "establish ISO 26262 compliance or replace formal verification and validation."
)

verification_records = load_verification_records(
    VERIFICATION_RECORDS_PATH
)

verification_options = []

if st.session_state.get("safety_goal_result"):
    verification_options.append(
        (
            "Safety Goal",
            st.session_state["safety_goal_result"].get("id", "SG-001"),
        )
    )

for fsr in st.session_state.get("fsr_results", []):
    verification_options.append(
        ("FSR", fsr.get("id", "FSR-001"))
    )

for tsr in st.session_state.get("tsr_results", []):
    verification_options.append(
        ("TSR", tsr.get("id", "TSR-001"))
    )

if not verification_options:
    st.caption(
        "Generate a Safety Goal, FSR or TSR first to create a verification link."
    )
else:
    requirement_labels = [
        f"{kind} — {artifact_id}"
        for kind, artifact_id in verification_options
    ]

    selected_requirement_label = st.selectbox(
        "Requirement to verify",
        requirement_labels,
        key="verification_requirement_selection",
    )

    artifact_id = st.text_input(
        "Verification artifact ID",
        key="verification_artifact_id",
        placeholder="Example: VER-001",
    )

    artifact_name = st.text_input(
        "Verification artifact / test name",
        key="verification_artifact_name",
        placeholder="Example: Brake fault detection test",
    )

    verification_method = st.selectbox(
        "Verification method",
        [
            "Test",
            "Simulation",
            "Inspection",
            "Analysis",
            "Review",
        ],
        key="verification_method_selection",
    )

    verification_result = st.selectbox(
        "Verification result",
        [
            "Pass",
            "Fail",
            "Pending Review",
        ],
        key="verification_result_selection",
    )

    evidence_reference = st.text_input(
        "Evidence reference",
        key="verification_evidence_reference",
        placeholder="Example: Test report / log / simulation result reference",
    )

    verification_notes = st.text_area(
        "Verification notes",
        key="verification_notes",
        placeholder="Briefly describe what was verified.",
    )

    if st.button(
        "🔗 Record Verification Evidence",
        type="primary",
        key="record_verification_evidence",
    ):
        selected_kind, selected_id = verification_options[
            requirement_labels.index(selected_requirement_label)
        ]

        if not artifact_id.strip():
            st.warning("Enter a verification artifact ID.")
        elif not artifact_name.strip():
            st.warning("Enter a verification artifact/test name.")
        elif not evidence_reference.strip():
            st.warning("Enter an evidence reference.")
        else:
            save_verification_record(
                path=VERIFICATION_RECORDS_PATH,
                artifact_id=artifact_id,
                artifact_name=artifact_name,
                verification_method=verification_method,
                result=verification_result,
                linked_requirement=f"{selected_kind} — {selected_id}",
                evidence_reference=evidence_reference,
                notes=verification_notes,
            )

            log_audit_event(
                event="Verification evidence mapping recorded",
                details=(
                    f"{artifact_id.strip()} linked to "
                    f"{selected_kind} {selected_id}; result={verification_result}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=(
                    st.session_state.get("safety_goal_result", {}).get(
                        "id", "SG-001"
                    )
                    if st.session_state.get("safety_goal_result")
                    else None
                ),
                fsr_id=(
                    selected_id
                    if selected_kind == "FSR"
                    else st.session_state.get("tsr_fsr_id")
                ),
                tsr_ids=(
                    [selected_id]
                    if selected_kind == "TSR"
                    else []
                ),
            )

            st.success(
                f"Verification evidence {artifact_id.strip()} recorded "
                f"against {selected_kind} {selected_id}."
            )
            st.rerun()

st.divider()

st.markdown("### Verification Evidence Register")

if verification_records:
    st.dataframe(
        [
            {
                "Artifact ID": item.get("artifact_id", ""),
                "Artifact / Test": item.get("artifact_name", ""),
                "Method": item.get("verification_method", ""),
                "Result": item.get("result", ""),
                "Linked Requirement": item.get("linked_requirement", ""),
                "Evidence": item.get("evidence_reference", ""),
                "Timestamp (UTC)": item.get("timestamp_utc", ""),
            }
            for item in verification_records
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "📄 Export Verification Register (JSON)",
        data=json.dumps(
            verification_records,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="verification_records.json",
        mime="application/json",
    )

    if st.button(
        "🗑️ Clear Verification Register",
        key="clear_verification_register",
    ):
        clear_verification_records(VERIFICATION_RECORDS_PATH)
        st.rerun()
else:
    st.caption("No verification evidence records have been added yet.")

st.info(get_verification_note())


# =========================================================
