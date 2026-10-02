# =========================================================
# SAFETY GOAL ENGINE
# =========================================================


def generate_safety_goal(
    system,
    function,
    hazard,
    hazardous_event,
    candidate_asil
):
    """
    Generate a candidate Safety Goal from the
    identified HARA hazard and hazardous event.

    This is a draft engineering requirement only.
    Final Safety Goal must be reviewed and approved
    by a qualified functional-safety engineer.
    """

    system_text = system.strip()
    function_text = function.strip()
    hazard_text = hazard.strip()
    event_text = hazardous_event.strip()

    # -----------------------------------------------------
    # SYSTEM-SPECIFIC SAFETY GOAL TEMPLATES
    # -----------------------------------------------------

    system_lower = system_text.lower()

    if (
        "steering" in system_lower
        or "eps" in system_lower
    ):

        safety_goal = (
            "The Electric Power Steering (EPS) system "
            "shall prevent loss of steering assistance "
            "or unintended steering assistance that could "
            "lead to loss of vehicle directional control."
        )

    elif (
        "braking" in system_lower
        or "brake" in system_lower
        or "emb" in system_lower
    ):

        safety_goal = (
            "The braking system shall prevent unintended "
            "loss or application of braking capability "
            "that could lead to loss of vehicle control "
            "or an unsafe stopping condition."
        )

    elif (
        "driver monitoring" in system_lower
        or "dms" in system_lower
    ):

        safety_goal = (
            "The Driver Monitoring System (DMS) shall "
            "reliably monitor driver attention and shall "
            "provide the required safety indication or "
            "intervention when a relevant driver "
            "distraction or drowsiness condition is detected."
        )

    elif (
        "adas" in system_lower
        or "advanced driver" in system_lower
    ):

        safety_goal = (
            "The ADAS function shall prevent unsafe "
            "system behavior or failure to provide the "
            "intended assistance when a safety-relevant "
            "driving situation is detected."
        )

    else:

        safety_goal = (
            f"The {system_text} shall perform its intended "
            f"function of {function_text} without introducing "
            "an unsafe condition that could result from "
            "the identified malfunction."
        )

    return {
        "safety_goal": safety_goal,
        "system": system_text,
        "function": function_text,
        "hazard": hazard_text,
        "hazardous_event": event_text,
        "candidate_asil": candidate_asil
    }


def get_safety_goal_review_note():
    """
    Return the engineering review note for
    the generated Safety Goal.
    """

    return (
        "This Safety Goal is an AI-assisted candidate draft. "
        "It must be reviewed, refined and approved by an "
        "authorized functional-safety engineer before "
        "being used as an official safety requirement."
    )