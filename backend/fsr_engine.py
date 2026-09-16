# =========================================================
# FUNCTIONAL SAFETY REQUIREMENT (FSR) ENGINE
# =========================================================


def generate_fsr(
    system,
    function,
    malfunction,
    hazard,
    hazardous_event,
    safety_goal,
    candidate_asil
):
    """
    Generate candidate Functional Safety Requirements (FSRs)
    from the selected Safety Goal and HARA information.

    This is an AI-assisted engineering draft.
    Final FSRs must be reviewed and approved by a
    qualified functional-safety engineer.
    """

    system_text = system.strip()
    function_text = function.strip()
    malfunction_text = malfunction.strip()
    hazard_text = hazard.strip()
    event_text = hazardous_event.strip()
    safety_goal_text = safety_goal.strip()

    system_lower = system_text.lower()

    fsrs = []

    # -----------------------------------------------------
    # EPS / STEERING
    # -----------------------------------------------------

    if (
        "steering" in system_lower
        or "eps" in system_lower
    ):

        fsrs = [

            {
                "id": "FSR-001",
                "requirement": (
                    "The EPS system shall detect "
                    "safety-relevant faults that may "
                    "result in loss or unintended "
                    "steering assistance."
                ),
                "rationale": (
                    "Fault detection is required to "
                    "identify conditions that could "
                    "lead to the identified steering hazard."
                )
            },

            {
                "id": "FSR-002",
                "requirement": (
                    "The EPS system shall transition "
                    "to a defined safe state when a "
                    "critical steering-control fault "
                    "is detected."
                ),
                "rationale": (
                    "A defined safe state reduces the "
                    "risk of unsafe steering behavior "
                    "following a critical fault."
                )
            },

            {
                "id": "FSR-003",
                "requirement": (
                    "The EPS system shall prevent "
                    "unintended steering assistance "
                    "caused by detected safety-relevant "
                    "faults."
                ),
                "rationale": (
                    "Prevention of unintended assistance "
                    "addresses the identified loss of "
                    "vehicle directional control hazard."
                )
            },

            {
                "id": "FSR-004",
                "requirement": (
                    "The EPS system shall provide "
                    "diagnostic information for "
                    "safety-relevant steering faults."
                ),
                "rationale": (
                    "Diagnostic information supports "
                    "fault detection and safety monitoring."
                )
            }

        ]

    # -----------------------------------------------------
    # BRAKING
    # -----------------------------------------------------

    elif (
        "braking" in system_lower
        or "brake" in system_lower
        or "emb" in system_lower
    ):

        fsrs = [

            {
                "id": "FSR-001",
                "requirement": (
                    "The braking system shall detect "
                    "safety-relevant faults that may "
                    "cause loss of braking capability."
                ),
                "rationale": (
                    "Fault detection is required to "
                    "identify braking failures that "
                    "could lead to an unsafe stopping condition."
                )
            },

            {
                "id": "FSR-002",
                "requirement": (
                    "The braking system shall maintain "
                    "or transition to a defined safe "
                    "braking state following detection "
                    "of a critical fault."
                ),
                "rationale": (
                    "Maintaining a safe braking state "
                    "helps reduce the consequences of "
                    "critical braking failures."
                )
            },

            {
                "id": "FSR-003",
                "requirement": (
                    "The braking system shall prevent "
                    "unintended brake application caused "
                    "by safety-relevant faults."
                ),
                "rationale": (
                    "Prevention of unintended braking "
                    "reduces the risk of unexpected "
                    "vehicle deceleration."
                )
            }

        ]

    # -----------------------------------------------------
    # DRIVER MONITORING SYSTEM
    # -----------------------------------------------------

    elif (
        "driver monitoring" in system_lower
        or "dms" in system_lower
    ):

        fsrs = [

            {
                "id": "FSR-001",
                "requirement": (
                    "The DMS shall detect relevant "
                    "driver distraction or drowsiness "
                    "conditions within the defined "
                    "operating conditions."
                ),
                "rationale": (
                    "Detection of driver state supports "
                    "the safety goal for maintaining "
                    "driver attention."
                )
            },

            {
                "id": "FSR-002",
                "requirement": (
                    "The DMS shall provide the required "
                    "safety indication or intervention "
                    "when a relevant driver condition "
                    "is detected."
                ),
                "rationale": (
                    "The safety response helps mitigate "
                    "the identified hazardous event."
                )
            }

        ]

    # -----------------------------------------------------
    # ADAS
    # -----------------------------------------------------

    elif (
        "adas" in system_lower
        or "advanced driver" in system_lower
    ):

        fsrs = [

            {
                "id": "FSR-001",
                "requirement": (
                    "The ADAS function shall detect "
                    "safety-relevant failures that may "
                    "result in unsafe assistance behavior."
                ),
                "rationale": (
                    "Failure detection supports prevention "
                    "of unsafe ADAS behavior."
                )
            },

            {
                "id": "FSR-002",
                "requirement": (
                    "The ADAS function shall transition "
                    "to a defined safe state when a "
                    "critical safety-relevant failure "
                    "is detected."
                ),
                "rationale": (
                    "A safe state limits the potential "
                    "consequences of critical ADAS failures."
                )
            }

        ]

    # -----------------------------------------------------
    # GENERIC SYSTEM
    # -----------------------------------------------------

    else:

        fsrs = [

            {
                "id": "FSR-001",
                "requirement": (
                    f"The {system_text} shall detect "
                    "safety-relevant faults that may "
                    "lead to the identified hazardous event."
                ),
                "rationale": (
                    "Fault detection supports mitigation "
                    "of the identified safety hazard."
                )
            },

            {
                "id": "FSR-002",
                "requirement": (
                    f"The {system_text} shall transition "
                    "to a defined safe state when a "
                    "critical safety-relevant fault is detected."
                ),
                "rationale": (
                    "The safe state is intended to reduce "
                    "the risk associated with the identified hazard."
                )
            }

        ]

    # -----------------------------------------------------
    # ADD TRACEABILITY INFORMATION
    # -----------------------------------------------------

    for fsr in fsrs:

        fsr["system"] = system_text
        fsr["function"] = function_text
        fsr["malfunction"] = malfunction_text
        fsr["hazard"] = hazard_text
        fsr["hazardous_event"] = event_text
        fsr["safety_goal"] = safety_goal_text
        fsr["candidate_asil"] = candidate_asil
        fsr["review_status"] = "Pending Review"

    return fsrs


def get_fsr_review_note():
    """
    Engineering review note.
    """

    return (
        "These Functional Safety Requirements are "
        "AI-assisted candidate drafts. They must be "
        "reviewed, refined and approved by an authorized "
        "functional-safety engineer before being used "
        "as official safety requirements."
    )