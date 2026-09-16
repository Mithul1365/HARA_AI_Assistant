# ============================================================
# TRACEABILITY ENGINE
# HARA AI Assistant
# ============================================================

def build_traceability_matrix(
    hara_candidate,
    candidate_asil,
    safety_goal,
    fsr_results,
    tsr_results=None
):
    """
    Build a traceability matrix connecting:

    HARA
      ↓
    ASIL
      ↓
    Safety Goal
      ↓
    FSR
      ↓
    TSR

    This is an engineering traceability aid.
    Final approval remains with the authorized
    functional-safety engineer.
    """

    if not hara_candidate:
        return []

    if not safety_goal:
        return []

    if not fsr_results:
        return []

    if tsr_results is None:
        tsr_results = []

    rows = []

    # --------------------------------------------------------
    # HARA INFORMATION
    # --------------------------------------------------------

    malfunction = hara_candidate.get(
        "malfunction",
        "Identified malfunction"
    )

    hazard = hara_candidate.get(
        "hazard",
        "Identified hazard"
    )

    hazardous_event = hara_candidate.get(
        "hazardous_event",
        "Identified hazardous event"
    )

    # --------------------------------------------------------
    # SAFETY GOAL INFORMATION
    # --------------------------------------------------------

    safety_goal_id = safety_goal.get(
        "id",
        "SG-001"
    )

    safety_goal_text = safety_goal.get(
        "safety_goal",
        ""
    )

    # --------------------------------------------------------
    # FSR → TSR TRACEABILITY
    # --------------------------------------------------------

    for fsr in fsr_results:

        fsr_id = fsr.get(
            "id",
            "FSR-001"
        )

        fsr_requirement = fsr.get(
            "requirement",
            ""
        )

        linked_tsrs = [
            tsr
            for tsr in tsr_results
            if tsr.get("fsr") == fsr_requirement
            or tsr.get("fsr_id") == fsr_id
        ]

        # ----------------------------------------------------
        # If no TSR exists yet
        # ----------------------------------------------------

        if not linked_tsrs:

            rows.append(
                {
                    "HARA ID": "HARA-001",
                    "Malfunction": malfunction,
                    "Hazard": hazard,
                    "Hazardous Event": hazardous_event,
                    "ASIL": candidate_asil,
                    "Safety Goal ID": safety_goal_id,
                    "Safety Goal": safety_goal_text,
                    "FSR ID": fsr_id,
                    "FSR": fsr_requirement,
                    "TSR ID": "Not Generated",
                    "TSR": "Not Generated"
                }
            )

        # ----------------------------------------------------
        # TSR exists
        # ----------------------------------------------------

        else:

            for tsr in linked_tsrs:

                rows.append(
                    {
                        "HARA ID": "HARA-001",
                        "Malfunction": malfunction,
                        "Hazard": hazard,
                        "Hazardous Event": hazardous_event,
                        "ASIL": candidate_asil,
                        "Safety Goal ID": safety_goal_id,
                        "Safety Goal": safety_goal_text,
                        "FSR ID": fsr_id,
                        "FSR": fsr_requirement,
                        "TSR ID": tsr.get(
                            "id",
                            "TSR-001"
                        ),
                        "TSR": tsr.get(
                            "requirement",
                            ""
                        )
                    }
                )

    return rows


def get_traceability_review_note():
    """
    Engineering governance note.
    """

    return (
        "Traceability is AI-assisted and intended to support "
        "engineering review. Final acceptance and approval "
        "must be performed by an authorized functional-safety "
        "engineer."
    )