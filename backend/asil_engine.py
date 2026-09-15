# ---------------------------------------------------------
# ASIL ENGINE
# Deterministic S / E / C based ASIL recommendation
# ---------------------------------------------------------


def calculate_asil(severity, exposure, controllability):
    """
    Calculate a candidate ASIL from S/E/C values.

    This is a prototype decision-support implementation.
    Final ASIL classification must be reviewed and approved
    by a qualified functional-safety engineer.
    """

    # Convert values to numeric levels

    severity_level = {
        "S0": 0,
        "S1": 1,
        "S2": 2,
        "S3": 3
    }

    exposure_level = {
        "E0": 0,
        "E1": 1,
        "E2": 2,
        "E3": 3,
        "E4": 4
    }

    controllability_level = {
        "C0": 0,
        "C1": 1,
        "C2": 2,
        "C3": 3
    }

    s = severity_level.get(severity)
    e = exposure_level.get(exposure)
    c = controllability_level.get(controllability)

    if s is None or e is None or c is None:
        return None

    # -----------------------------------------------------
    # QM / ASIL decision support
    # -----------------------------------------------------

    # No safety impact
    if s == 0:
        return "QM"

    # Low severity
    if s == 1:
        if e <= 1 or c <= 1:
            return "QM"

        return "A"

    # Medium severity
    if s == 2:

        if e <= 1 and c <= 1:
            return "QM"

        if e <= 2 and c <= 2:
            return "A"

        return "B"

    # High severity
    if s == 3:

        if e <= 1 and c <= 1:
            return "A"

        if e <= 2 and c <= 2:
            return "B"

        if e <= 3 and c <= 2:
            return "C"

        return "D"

    return "QM"


def get_asil_rationale(
    severity,
    exposure,
    controllability,
    asil
):
    """
    Generate a simple deterministic explanation
    for the candidate ASIL result.
    """

    return (
        f"Candidate ASIL {asil} is determined from "
        f"Severity={severity}, "
        f"Exposure={exposure}, and "
        f"Controllability={controllability}. "
        "This result is decision-support only and "
        "requires functional-safety engineer review."
    )