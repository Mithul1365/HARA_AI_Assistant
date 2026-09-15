import json
import urllib.request


# =========================================================
# OLLAMA CONFIGURATION
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"


# =========================================================
# ASK LOCAL QWEN
# =========================================================

def ask_qwen(prompt, summary_mode=False):
    """
    Send a request to local Qwen3.

    summary_mode=True  -> short and fast response
    summary_mode=False -> detailed response
    """

    # -----------------------------------------------------
    # MODE SETTINGS
    # -----------------------------------------------------

    if summary_mode:

        mode_instruction = """
/no_think

Generate a SHORT HARA summary.

Do not provide long reasoning.
Focus only on the important engineering findings.
"""

        max_tokens = 300

    else:

        mode_instruction = """
/no_think

Generate a DETAILED HARA analysis.

Provide clear engineering reasoning,
but avoid unnecessary repetition.
"""

        max_tokens = 800


    # -----------------------------------------------------
    # FINAL PROMPT
    # -----------------------------------------------------

    final_prompt = (
        mode_instruction
        + "\n"
        + prompt
    )


    # -----------------------------------------------------
    # OLLAMA REQUEST
    # -----------------------------------------------------

    data = {
        "model": MODEL_NAME,

        "prompt": final_prompt,

        "stream": False,

        # Explicitly disable Qwen3 thinking
        "think": False,

        "options": {
            "num_predict": max_tokens
        }
    }


    request = urllib.request.Request(
        OLLAMA_URL,

        data=json.dumps(
            data
        ).encode("utf-8"),

        headers={
            "Content-Type": "application/json"
        },

        method="POST"
    )


    # -----------------------------------------------------
    # SEND REQUEST
    # -----------------------------------------------------

    with urllib.request.urlopen(
        request,
        timeout=300
    ) as response:

        raw_response = response.read().decode(
            "utf-8"
        )


    # -----------------------------------------------------
    # PARSE RESPONSE
    # -----------------------------------------------------

    result = json.loads(
        raw_response
    )


    # -----------------------------------------------------
    # GET MODEL ANSWER
    # -----------------------------------------------------

    answer = result.get(
        "response",
        ""
    )


    # -----------------------------------------------------
    # SAFETY FALLBACK
    # -----------------------------------------------------

    if not answer.strip():

        return (
            "Qwen3 did not return a text response. "
            "Please run the analysis again."
        )


    return answer.strip()


# =========================================================
# HARA ANALYSIS
# =========================================================

def analyze_with_qwen(
    system,
    function,
    scenario,
    evidence,
    summary_mode=False
):
    """
    Perform evidence-grounded HARA analysis
    using local Qwen3.
    """

    # -----------------------------------------------------
    # BUILD EVIDENCE
    # -----------------------------------------------------

    evidence_text = ""


    for i, item in enumerate(
        evidence,
        start=1
    ):

        evidence_text += f"""
--- Evidence {i} ---
Source: {item["source"]}
Page: {item["page"]}

{item["text"]}
"""


    # -----------------------------------------------------
    # BASE PROMPT
    # -----------------------------------------------------

    prompt = f"""
You are an automotive functional safety HARA assistant.

Analyze the following engineering item using
the provided engineering evidence.

SYSTEM:
{system}

FUNCTION:
{function}

OPERATIONAL SCENARIO:
{scenario}

ENGINEERING EVIDENCE:
{evidence_text}


IMPORTANT RULES:

1. Use the provided engineering evidence as the primary source.
2. Do not invent unsupported engineering facts.
3. Identify potential malfunctions relevant to the function.
4. Identify the potential hazard caused by each malfunction.
5. Identify the hazardous event considering the scenario.
6. Mention the source document and page.
7. Do not make a final safety approval decision.
8. This is an AI-assisted candidate analysis.
"""


    # =====================================================
    # QUICK SUMMARY MODE
    # =====================================================

    if summary_mode:

        prompt += """

QUICK SUMMARY FORMAT:

Provide up to 4 important findings.

For each finding use:

Malfunction:
<hardware/software/function malfunction>

Hazard:
<potential hazard>

Hazardous Event:
<hazardous event>

Evidence:
<source and page>

Keep every finding concise.
Do not provide long explanations.
"""


    # =====================================================
    # DETAILED MODE
    # =====================================================

    else:

        prompt += """

DETAILED HARA FORMAT:

Scenario 1:

Potential Malfunction:
<malfunction>

Potential Hazard:
<hazard>

Hazardous Event:
<hazardous event>

Rationale:
<clear engineering reasoning>

Evidence:
<source and page>


Scenario 2:

Potential Malfunction:
<malfunction>

Potential Hazard:
<hazard>

Hazardous Event:
<hazardous event>

Rationale:
<clear engineering reasoning>

Evidence:
<source and page>


Continue for other reasonably supported findings,
up to 4 scenarios.
"""


    # -----------------------------------------------------
    # CALL QWEN
    # -----------------------------------------------------

    return ask_qwen(
        prompt=prompt,
        summary_mode=summary_mode
    )