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
        tsrs = [
            {
                "id": "TSR-001",
                "requirement": (
                    "The braking control unit shall monitor safety-relevant "
                    "braking signals and detect specified faults within the "
                    "defined diagnostic time."
                ),
                "rationale": (
                    "Technical monitoring supports detection of failures "
                    "that may result in loss of braking capability."
                )
            },
            {
                "id": "TSR-002",
                "requirement": (
                    "The braking system shall transition to the defined safe "
                    "braking state when a critical safety-relevant fault is detected."
                ),
                "rationale": (
                    "A defined technical reaction helps maintain safe "
                    "braking behavior after a critical fault."
                )
            },
            {
                "id": "TSR-003",
                "requirement": (
                    "The braking control path shall prevent unintended brake "
                    "commands caused by detected safety-relevant faults."
                ),
                "rationale": (
                    "Command inhibition reduces the risk of unexpected "
                    "vehicle deceleration."
                )
            }
        ]

    elif "driver monitoring" in system_lower or "dms" in system_lower:
        tsrs = [
            {
                "id": "TSR-001",
                "requirement": (
                    "The DMS processing unit shall monitor driver-state "
                    "signals and identify the defined distraction or "
                    "drowsiness conditions."
                ),
                "rationale": (
                    "Technical driver-state monitoring supports the linked FSR."
                )
            },
            {
                "id": "TSR-002",
                "requirement": (
                    "The DMS shall issue the defined safety indication or "
                    "intervention when the specified driver-state threshold is reached."
                ),
                "rationale": (
                    "A defined technical response supports mitigation of "
                    "the identified hazardous event."
                )
            }
        ]

    elif "adas" in system_lower or "advanced driver" in system_lower:
        tsrs = [
            {
                "id": "TSR-001",
                "requirement": (
                    "The ADAS control unit shall monitor safety-relevant "
                    "sensor and control inputs and detect specified failures "
                    "within the defined diagnostic time."
                ),
                "rationale": (
                    "Monitoring supports detection of failures that could "
                    "result in unsafe assistance behavior."
                )
            },
            {
                "id": "TSR-002",
                "requirement": (
                    "The ADAS control unit shall inhibit the affected "
                    "assistance function or transition it to the defined "
                    "safe state when a critical failure is detected."
                ),
                "rationale": (
                    "Technical degradation or safe-state behavior reduces "
                    "the risk of unsafe assistance."
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
