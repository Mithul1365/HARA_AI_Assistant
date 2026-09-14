def analyze_malfunctions(system: str, function: str, scenario: str):
    """
    Phase-1 HARA prototype.

    Generates candidate malfunctions, hazards and hazardous events
    from the user-provided system, function and scenario.

    NOTE:
    This is a prototype. Later, approved engineering documents,
    RAG and an LLM will provide evidence-grounded suggestions.
    """

    text = function.lower()

    if "steering" in text or "assist" in text:
        malfunctions = [
            {
                "malfunction": "Loss of steering assistance",
                "hazard": "Reduced ability of the driver to control the vehicle",
                "hazardous_event": (
                    f"Loss of steering assistance during {scenario} "
                    "may result in unintended vehicle trajectory."
                ),
                "rationale": (
                    "The steering-assistance function is not available "
                    "when it is expected."
                )
            },
            {
                "malfunction": "Unintended steering assistance",
                "hazard": "Unexpected change in vehicle steering behavior",
                "hazardous_event": (
                    f"Unintended steering assistance during {scenario} "
                    "may cause an unexpected vehicle trajectory."
                ),
                "rationale": (
                    "Steering assistance is provided without the intended "
                    "driver or system demand."
                )
            },
            {
                "malfunction": "Incorrect steering assistance",
                "hazard": "Incorrect steering response",
                "hazardous_event": (
                    f"Incorrect steering assistance during {scenario} "
                    "may cause the vehicle to deviate from the intended path."
                ),
                "rationale": (
                    "The steering assistance does not correspond correctly "
                    "to the intended steering behavior."
                )
            },
            {
                "malfunction": "Delayed steering assistance",
                "hazard": "Delayed vehicle response to steering demand",
                "hazardous_event": (
                    f"Delayed steering assistance during {scenario} "
                    "may prevent the vehicle from following the intended path."
                ),
                "rationale": (
                    "The required steering assistance is provided later "
                    "than intended."
                )
            }
        ]

    elif "brak" in text:
        malfunctions = [
            {
                "malfunction": "Failure to perform braking when required",
                "hazard": "Vehicle does not decelerate as intended",
                "hazardous_event": (
                    f"Failure to brake during {scenario} "
                    "may result in a collision with an obstacle."
                ),
                "rationale": (
                    "Required braking action is not performed."
                )
            },
            {
                "malfunction": "Delayed braking",
                "hazard": "Insufficient vehicle deceleration",
                "hazardous_event": (
                    f"Delayed braking during {scenario} "
                    "may increase the collision risk."
                ),
                "rationale": (
                    "Braking is initiated later than required."
                )
            },
            {
                "malfunction": "Unintended braking",
                "hazard": "Unexpected vehicle deceleration",
                "hazardous_event": (
                    f"Unintended braking during {scenario} "
                    "may cause an unexpected change in vehicle motion."
                ),
                "rationale": (
                    "Braking occurs without the intended condition."
                )
            }
        ]

    else:
        malfunctions = [
            {
                "malfunction": "Function not performed",
                "hazard": "Loss of intended system functionality",
                "hazardous_event": (
                    f"The function is not performed during {scenario}, "
                    "which may lead to an unsafe vehicle condition."
                ),
                "rationale": (
                    "The intended function is completely unavailable."
                )
            },
            {
                "malfunction": "Function performed incorrectly",
                "hazard": "Incorrect system behavior",
                "hazardous_event": (
                    f"Incorrect function behavior during {scenario} "
                    "may result in an unsafe vehicle condition."
                ),
                "rationale": (
                    "The function is available but behaves incorrectly."
                )
            },
            {
                "malfunction": "Function performed too late",
                "hazard": "Delayed system response",
                "hazardous_event": (
                    f"Delayed function execution during {scenario} "
                    "may prevent the intended vehicle response."
                ),
                "rationale": (
                    "The required function occurs later than intended."
                )
            },
            {
                "malfunction": "Function performed unintentionally",
                "hazard": "Unexpected vehicle behavior",
                "hazardous_event": (
                    f"Unintended function activation during {scenario} "
                    "may cause an unexpected vehicle response."
                ),
                "rationale": (
                    "The function is activated without the intended condition."
                )
            }
        ]

    return malfunctions