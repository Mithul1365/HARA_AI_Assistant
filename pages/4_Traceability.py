from common import *

init_page("HARA AI Assistant — Traceability")
page_header("TRACEABILITY", "Traceability", "End-to-end HARA → ASIL → Safety Goal → FSR → TSR relationship.")

# 10. TRACEABILITY MATRIX
# =========================================================

st.header(
    "10. Traceability Matrix"
)

st.write(
    "End-to-end traceability for the selected HARA candidate, "
    "candidate ASIL, Safety Goal, selected FSR and its generated TSRs."
)

traceability_context_ready = (
    st.session_state.get("active_hara_key") is not None
    and st.session_state.get("asil_assessment_completed", False)
    and st.session_state.get("safety_goal_result") is not None
    and bool(st.session_state.get("fsr_results"))
    and st.session_state.get("tsr_fsr_id") is not None
)

if not traceability_context_ready:

    st.caption(
        "Traceability Matrix will be available after "
        "HARA → ASIL → Safety Goal → FSR → TSR generation."
    )

else:

    safety_goal_data = st.session_state["safety_goal_result"]
    all_fsr_results = st.session_state["fsr_results"]

    active_hara_key = st.session_state.get("active_hara_key")
    traceability_candidate = None

    for candidate in hara_candidates:

        candidate_key = (
            candidate.get("malfunction", "").strip().lower(),
            candidate.get("hazard", "").strip().lower(),
            candidate.get("hazardous_event", "").strip().lower()
        )

        if candidate_key == active_hara_key:
            traceability_candidate = candidate
            break

    selected_fsr_id = st.session_state.get("tsr_fsr_id")
    selected_fsr = next(
        (
            fsr for fsr in all_fsr_results
            if fsr.get("id") == selected_fsr_id
        ),
        None
    )

    if traceability_candidate is None:

        st.warning(
            "The current HARA candidate could not be resolved. "
            "Please reselect the HARA candidate."
        )

    elif selected_fsr is None:

        st.warning(
            "The selected FSR could not be resolved. "
            "Please select an FSR and generate its TSRs again."
        )

    else:

        tsr_results = st.session_state.get(
            "tsr_results",
            []
        )

        # Only the FSR selected for TSR decomposition is shown.
        selected_fsr_results = [selected_fsr]

        traceability_rows = build_traceability_matrix(
            hara_candidate=traceability_candidate,
            candidate_asil=st.session_state.get(
                "candidate_asil",
                safety_goal_data.get("candidate_asil", "")
            ),
            safety_goal=safety_goal_data,
            fsr_results=selected_fsr_results,
            tsr_results=tsr_results
        )

        st.session_state["traceability_rows"] = traceability_rows

        summary_col1, summary_col2, summary_col3, summary_col4 = (
            st.columns(4)
        )

        with summary_col1:
            st.metric("HARA", "HARA-001")

        with summary_col2:
            st.metric(
                "ASIL",
                safety_goal_data.get(
                    "candidate_asil",
                    st.session_state.get("candidate_asil", "—")
                )
            )

        with summary_col3:
            st.metric("Selected FSR", selected_fsr.get("id", "—"))

        with summary_col4:
            st.metric("TSR Links", len(tsr_results))

        st.divider()

        # Parent-to-child traceability view.
        st.markdown("### Selected Safety Chain")

        st.markdown(
            f"""
            **HARA-001** — {traceability_candidate['malfunction']}

            ↓

            **ASIL {safety_goal_data.get('candidate_asil', '—')}**

            ↓

            **{safety_goal_data.get('id', 'SG-001')}** — "
            f"{safety_goal_data.get('safety_goal', '')}

            ↓

            **{selected_fsr.get('id', 'FSR-001')}** — "
            f"{selected_fsr.get('requirement', '')}

            ↓

            **Derived Technical Safety Requirements**
            """
        )

        if tsr_results:

            tsr_rows = [
                {
                    "TSR ID": tsr.get("id", "TSR-001"),
                    "Technical Safety Requirement": tsr.get(
                        "requirement",
                        ""
                    )
                }
                for tsr in tsr_results
            ]

            st.dataframe(
                tsr_rows,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"{len(tsr_results)} TSR(s) linked to "
                f"{selected_fsr.get('id', 'the selected FSR')}."
            )

        else:

            st.caption(
                "No TSR links are currently available."
            )

        with st.expander(
            "🔗 Engineering Traceability Details",
            expanded=False
        ):

            st.write(
                f"**Selected Malfunction:** "
                f"{traceability_candidate['malfunction']}"
            )

            st.write(
                f"**Selected Hazard:** "
                f"{traceability_candidate['hazard']}"
            )

            st.write(
                f"**Selected Hazardous Event:** "
                f"{traceability_candidate['hazardous_event']}"
            )

            st.write(
                f"**Candidate ASIL:** "
                f"{safety_goal_data.get('candidate_asil', '—')}"
            )

            st.write(
                f"**Safety Goal ID:** "
                f"{safety_goal_data.get('id', 'SG-001')}"
            )

            st.write(
                f"**Selected FSR ID:** "
                f"{selected_fsr.get('id', '—')}"
            )

            st.write(
                f"**TSR Count:** {len(tsr_results)}"
            )

        st.info(
            get_traceability_review_note()
        )




def create_audit_report_pdf(history):
    """Generate a human-readable PDF audit report."""

    # ReportLab is only needed when the user views/downloads
    # the audit report, so import it lazily.
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="HARA AI Assistant - Audit Report",
        author="HARA AI Assistant",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AuditTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "AuditSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.grey,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "AuditHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "AuditBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    )

    small_style = ParagraphStyle(
        "AuditSmall",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9,
    )

    story = [
        Paragraph("HARA AI Assistant", title_style),
        Paragraph(
            "Decision History / Audit Evidence Report",
            subtitle_style,
        ),
        Paragraph(
            "Human-readable record of AI-assisted engineering actions "
            "and decision context.",
            body_style,
        ),
        Spacer(1, 12),
        Paragraph("Report Summary", heading_style),
    ]

    event_types = len({
        str(item.get("event", ""))
        for item in history
        if item.get("event")
    })

    latest = history[0] if history else {}

    summary_data = [
        ["Recorded Events", str(len(history))],
        ["Event Types", str(event_types)],
        ["HARA", str(latest.get("HARA ID", "—"))],
        ["ASIL", str(latest.get("ASIL", "—"))],
        ["Safety Goal", str(latest.get("Safety Goal ID", "—"))],
        ["FSR", str(latest.get("FSR ID", "—"))],
        ["TSRs", str(latest.get("TSR IDs", "—"))],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[150, 330],
    )

    summary_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E9EEF5")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story += [summary_table, Spacer(1, 14)]
    story.append(
        Paragraph("Recorded Engineering Actions", heading_style)
    )

    table_data = [[
        "Timestamp (UTC)",
        "Event",
        "Details",
        "HARA",
        "ASIL",
        "SG",
        "FSR",
        "TSRs",
    ]]

    for item in history:
        table_data.append([
            Paragraph(str(item.get("timestamp_utc", "")), small_style),
            Paragraph(str(item.get("event", "")), small_style),
            Paragraph(str(item.get("details", "")), small_style),
            Paragraph(str(item.get("HARA ID", "")), small_style),
            Paragraph(str(item.get("ASIL", "")), small_style),
            Paragraph(str(item.get("Safety Goal ID", "")), small_style),
            Paragraph(str(item.get("FSR ID", "")), small_style),
            Paragraph(str(item.get("TSR IDs", "")), small_style),
        ])

    action_table = Table(
        table_data,
        colWidths=[62, 70, 155, 42, 32, 32, 38, 49],
        repeatRows=1,
    )

    action_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20242C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ])
    )

    story += [action_table, Spacer(1, 14)]

    story.append(
        Paragraph(
            "<b>Engineering Review Notice:</b> This report records "
            "AI-assisted engineering actions and decision context. "
            "It is not an approval record and does not replace review "
            "or sign-off by an authorized functional-safety engineer.",
            body_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# =========================================================
