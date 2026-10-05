# =========================================================
# TECHNICAL SAFETY REQUIREMENT (TSR) ENGINE
# =========================================================

def generate_tsr(
    system,
    function,
    malfunction,
    hazard,
    hazardous_event,
    safety_goal,
    fsr,
    candidate_asil
):
    """
    Generate candidate Technical Safety Requirements from an FSR.

    This is an AI-assisted engineering draft. Final TSRs must be
    reviewed and approved by a qualified functional-safety engineer.
    """

    system_text = system.strip()
    function_text = function.strip()
    malfunction_text = malfunction.strip()
    hazard_text = hazard.strip()
    event_text = hazardous_event.strip()
    safety_goal_text = safety_goal.strip()
    fsr_text = fsr.strip()

    system_lower = system_text.lower()
    fsr_lower = fsr_text.lower()

    tsrs = []

    if "steering" in system_lower or "eps" in system_lower:
        tsrs = [
            {
                "id": "TSR-001",
                "requirement": (
                    "The EPS control unit shall monitor safety-relevant "
                    "steering-control signals and detect specified faults "
                    "within the defined diagnostic time."
                ),
                "rationale": (
                    "Technical monitoring supports detection of faults that "
                    "may cause loss or unintended steering assistance."
                )
            },
            {
                "id": "TSR-002",
                "requirement": (
                    "The EPS control unit shall transition the steering-"
                    "assistance function to the defined safe state when a "
                    "critical safety-relevant fault is confirmed."
                ),
                "rationale": (
                    "A controlled technical reaction limits unsafe steering "
                    "behavior following a critical fault."
                )
            },
            {
                "id": "TSR-003",
                "requirement": (
                    "The EPS control path shall inhibit unintended steering-"
                    "assistance commands when a relevant control or actuator "
                    "fault is detected."
                ),
                "rationale": (
                    "Command inhibition provides a technical measure against "
                    "unintended steering assistance."
                )
            },
            {
                "id": "TSR-004",
                "requirement": (
                    "The EPS shall store and communicate diagnostic status "
                    "information for detected safety-relevant steering faults."
                ),
                "rationale": (
                    "Diagnostic reporting supports fault handling, monitoring "
                    "and verification."
                )
            }
        ]

    elif "braking" in system_lower or "brake" in system_lower or "emb" in system_lower:
        # -------------------------------------------------
        # FSR-SPECIFIC EMB / BRAKING TSRs
        # -------------------------------------------------

        if "safe" in fsr_lower or "transition" in fsr_lower:
            tsrs = [
                {
                    "id": "TSR-001",
                    "requirement": (
                        "The braking control unit shall detect critical "
                        "safety-relevant faults and initiate the defined "
                        "safe braking state."
                    ),
                    "rationale": (
                        "Timely fault reaction supports transition to a "
                        "controlled braking condition."
                    )
                },
                {
                    "id": "TSR-002",
                    "requirement": (
                        "The braking control unit shall inhibit the affected "
                        "motor-control output when a critical braking fault "
                        "is confirmed."
                    ),
                    "rationale": (
                        "Inhibiting the affected control path prevents continued "
                        "unsafe actuator operation."
                    )
                },
                {
                    "id": "TSR-003",
                    "requirement": (
                        "The braking control unit shall maintain the defined "
                        "safe braking state until the critical fault is "
                        "cleared or the system enters the specified recovery state."
                    ),
                    "rationale": (
                        "Maintaining a controlled state prevents premature "
                        "return to potentially unsafe operation."
                    )
                }
            ]

        elif "unintended" in fsr_lower or "application" in fsr_lower:
            tsrs = [
                {
                    "id": "TSR-001",
                    "requirement": (
                        "The braking control unit shall validate brake-control "
                        "commands before applying the corresponding actuator output."
                    ),
                    "rationale": (
                        "Command validation helps prevent unintended brake "
                        "application caused by invalid control signals."
                    )
                },
                {
                    "id": "TSR-002",
                    "requirement": (
                        "The braking control path shall inhibit actuator commands "
                        "when a safety-relevant command fault is detected."
                    ),
                    "rationale": (
                        "Command inhibition reduces the risk of unexpected "
                        "brake application and vehicle deceleration."
                    )
                },
                {
                    "id": "TSR-003",
                    "requirement": (
                        "The braking control unit shall detect discrepancies "
                        "between commanded and monitored braking states and "
                        "report a safety-relevant fault."
                    ),
                    "rationale": (
                        "Command-versus-state monitoring supports detection "
                        "of unintended braking behavior."
                    )
                }
            ]

        elif "detect" in fsr_lower and (
            "fault" in fsr_lower or
            "loss of braking" in fsr_lower
        ):
            tsrs = [
                {
                    "id": "TSR-001",
                    "requirement": (
                        "The braking control unit shall monitor safety-relevant "
                        "braking signals and detect specified faults within the "
                        "defined diagnostic time."
                    ),
                    "rationale": (
                        "Technical fault monitoring supports timely detection "
                        "of conditions that may cause loss of braking capability."
                    )
                },
                {
                    "id": "TSR-002",
                    "requirement": (
                        "The braking control unit shall monitor brake position "
                        "and motor-control feedback for deviations indicating "
                        "a safety-relevant braking fault."
                    ),
                    "rationale": (
                        "Monitoring position and motor-control feedback supports "
                        "detection of braking-control failures."
                    )
                },
                {
                    "id": "TSR-003",
                    "requirement": (
                        "The braking control unit shall provide a diagnostic "
                        "fault indication when a safety-relevant braking fault "
                        "is detected."
                    ),
                    "rationale": (
                        "Diagnostic reporting supports fault handling, monitoring "
                        "and verification of the braking safety function."
                    )
                }
            ]

        else:
            tsrs = [
                {
                    "id": "TSR-001",
                    "requirement": (
                        "The braking control unit shall monitor safety-relevant "
                        "braking signals and detect specified faults within the "
                        "defined diagnostic time."
                    ),
                    "rationale": (
                        "Technical fault monitoring supports the linked FSR."
                    )
                },
                {
                    "id": "TSR-002",
                    "requirement": (
                        "The braking system shall transition to the defined "
                        "safe braking state when a critical safety-relevant "
                        "fault is detected."
                    ),
                    "rationale": (
                        "A defined technical reaction supports safe braking "
                        "behavior after a critical fault."
                    )
                },
                {
                    "id": "TSR-003",
                    "requirement": (
                        "The braking control path shall prevent unintended "
                        "brake commands caused by detected safety-relevant faults."
                    ),
                    "rationale": (
                        "Command inhibition reduces the risk of unexpected "
                        "vehicle deceleration."
                    )
                }
            ]
    else:
        tsrs = [
            {
                "id": "TSR-001",
                "requirement": (
                    f"The {system_text} control function shall monitor "
                    "safety-relevant inputs and detect specified faults "
                    "within the defined diagnostic time."
                ),
                "rationale": (
                    "Technical fault monitoring supports the linked FSR."
                )
            },
            {
                "id": "TSR-002",
                "requirement": (
                    f"The {system_text} shall transition to the defined "
                    "safe state when a critical safety-relevant fault is detected."
                ),
                "rationale": (
                    "The defined technical reaction is intended to reduce "
                    "the risk associated with the identified hazardous event."
                )
            }
        ]

    for tsr in tsrs:
        tsr["system"] = system_text
        tsr["function"] = function_text
        tsr["malfunction"] = malfunction_text
        tsr["hazard"] = hazard_text
        tsr["hazardous_event"] = event_text
        tsr["safety_goal"] = safety_goal_text
        tsr["fsr"] = fsr_text
        tsr["candidate_asil"] = candidate_asil
        tsr["review_status"] = "Pending Review"

    return tsrs


def get_tsr_review_note():
    return (
        "These Technical Safety Requirements are AI-assisted candidate "
        "drafts. They must be reviewed, refined and approved by an "
        "authorized functional-safety engineer before being used as "
        "official technical safety requirements."
    )
