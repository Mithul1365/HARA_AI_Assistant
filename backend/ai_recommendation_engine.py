import re

import json
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:4b"


def _ask(instruction, payload, timeout=75):
    prompt = (
        "/no_think\n"
        + instruction
        + "\n\nCONTEXT:\n"
        + json.dumps(payload, ensure_ascii=False)
    )

    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an automotive functional-safety engineering assistant. "
                    "Provide conservative, evidence-grounded candidate recommendations. "
                    "Do not claim certification, compliance or final engineering approval."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "stream": False,
        "think": False,
        "keep_alive": -1,
        "format": "json",
        "options": {
            "num_predict": 280,
            "num_ctx": 2048,
            "temperature": 0.2,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=timeout) as response:
        result = json.loads(response.read().decode("utf-8"))

    answer = str(
        result.get("message", {}).get("content", "")
    ).strip()

    if not answer:
        answer = str(
            result.get("response", "")
        ).strip()

    if not answer:
        raise ValueError("Qwen3 returned an empty response.")

    try:
        parsed = json.loads(answer)

    except json.JSONDecodeError:
        start = answer.find("{")
        end = answer.rfind("}")

        if start < 0 or end <= start:
            raise ValueError(
                "Qwen3 did not return valid JSON."
            )

        parsed = json.loads(
            answer[start:end + 1]
        )

    if not isinstance(parsed, dict):
        raise ValueError(
            "Qwen3 returned an unexpected JSON structure."
        )

    return parsed


def recommend_asil(
    system,
    function,
    scenario,
    operating_conditions,
    malfunction,
    hazard,
    hazardous_event,
):
    """Ask Qwen for a normalized AI-assisted ASIL S/E/C recommendation."""

    prompt = f"""
You are an automotive functional-safety engineering assistant.

Analyze the supplied HARA context and recommend:
- Severity: exactly one of S0, S1, S2, S3
- Exposure: exactly one of E0, E1, E2, E3, E4
- Controllability: exactly one of C0, C1, C2, C3

SYSTEM:
{system}

FUNCTION:
{function}

OPERATIONAL SCENARIO:
{scenario}

OPERATING CONDITIONS:
{operating_conditions}

POTENTIAL MALFUNCTION:
{malfunction}

POTENTIAL HAZARD:
{hazard}

HAZARDOUS EVENT:
{hazardous_event}

Return ONLY valid JSON:

{{
  "severity": "S2",
  "exposure": "E3",
  "controllability": "C2",
  "confidence": "MEDIUM",
  "rationale": "Short engineering rationale."
}}

Rules:
- severity MUST be S0, S1, S2 or S3.
- exposure MUST be E0, E1, E2, E3 or E4.
- controllability MUST be C0, C1, C2 or C3.
- confidence MUST be LOW, MEDIUM or HIGH.
- Do not return descriptive text inside these fields.
- Do not calculate or assign final ASIL.
- This is decision support only.
- Do not add markdown.
"""

    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an automotive functional-safety assistant. "
                    "Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": "/no_think\n" + prompt,
            },
        ],
        "stream": False,
        "think": False,
        "keep_alive": -1,
        "format": "json",
        "options": {
            "temperature": 0.0,
            "num_predict": 180,
            "num_ctx": 1536,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_result = json.loads(
                response.read().decode("utf-8")
            )
    except Exception as exc:
        print(f"[AI ASIL] Ollama request failed: {exc}")
        return {
            "severity": "",
            "exposure": "",
            "controllability": "",
            "confidence": "LOW",
            "rationale": "",
            "review_required": True,
        }

    message = raw_result.get("message", {})
    answer = str(message.get("content", "")).strip()

    if not answer:
        answer = str(raw_result.get("response", "")).strip()

    print(f"[AI ASIL] Raw Qwen response: {answer[:1200]}")

    parsed = None

    # Normal JSON
    try:
        parsed = json.loads(answer)
    except Exception:
        pass

    # JSON embedded in text
    if parsed is None:
        first = answer.find("{")
        last = answer.rfind("}")

        if first != -1 and last > first:
            try:
                parsed = json.loads(answer[first:last + 1])
            except Exception:
                parsed = None

    if not isinstance(parsed, dict):
        print("[AI ASIL] Could not parse Qwen JSON.")
        return {
            "severity": "",
            "exposure": "",
            "controllability": "",
            "confidence": "LOW",
            "rationale": "",
            "review_required": True,
        }

    def pick(*keys):
        for key in keys:
            value = parsed.get(key)
            if value is not None and str(value).strip():
                return str(value).strip()
        return ""

    def normalize_code(value, prefix, maximum):
        value = str(value or "").upper().strip()

        # Exact form: S2 / E3 / C2
        match = re.search(
            rf"\b{re.escape(prefix)}\s*([0-{maximum}])\b",
            value,
        )

        if match:
            return f"{prefix}{match.group(1)}"

        # Numeric-only form: 2 / 3 / 2
        match = re.fullmatch(r"\D*([0-9])\D*", value)

        if match:
            number = int(match.group(1))
            if 0 <= number <= maximum:
                return f"{prefix}{number}"

        return ""

    severity_raw = pick(
        "severity",
        "Severity",
        "S",
        "severity_level",
    )

    exposure_raw = pick(
        "exposure",
        "Exposure",
        "E",
        "exposure_level",
    )

    controllability_raw = pick(
        "controllability",
        "Controllability",
        "C",
        "controllability_level",
    )

    severity = normalize_code(
        severity_raw,
        "S",
        3,
    )

    exposure = normalize_code(
        exposure_raw,
        "E",
        4,
    )

    controllability = normalize_code(
        controllability_raw,
        "C",
        3,
    )

    confidence = pick(
        "confidence",
        "Confidence",
    ).upper()

    if confidence not in {"LOW", "MEDIUM", "HIGH"}:
        confidence = "MEDIUM"

    rationale = pick(
        "rationale",
        "Rationale",
        "engineering_rationale",
        "engineeringRationale",
        "reason",
    )

    print(
        f"[AI ASIL] normalized "
        f"S={severity} E={exposure} C={controllability} "
        f"confidence={confidence}"
    )

    if not severity or not exposure or not controllability:
        print(
            "[AI ASIL] Invalid recommendation after normalization."
        )

        return {
            "severity": severity,
            "exposure": exposure,
            "controllability": controllability,
            "confidence": confidence,
            "rationale": rationale,
            "review_required": True,
        }

    return {
        "severity": severity,
        "exposure": exposure,
        "controllability": controllability,
        "confidence": confidence,
        "rationale": rationale,
        "review_required": True,
    }


def recommend_requirement(
    requirement_type,
    system,
    function,
    malfunction,
    hazard,
    hazardous_event,
    safety_goal,
    candidate_asil,
    source_requirement="",
    source_rationale="",
):
    """Direct Ollama-based AI recommendation for FSR/TSR."""

    requirement_type = str(requirement_type or "FSR").upper()

    prompt = f"""
You are an automotive functional safety engineering assistant.

Generate ONE candidate {requirement_type} based ONLY on this context.

SYSTEM:
{system}

FUNCTION:
{function}

MALFUNCTION:
{malfunction}

HAZARD:
{hazard}

HAZARDOUS EVENT:
{hazardous_event}

SAFETY GOAL:
{safety_goal}

ASIL:
{candidate_asil}

EXISTING REQUIREMENT:
{source_requirement}

EXISTING RATIONALE:
{source_rationale}

Return ONLY this JSON object:

{{
  "recommendation": "The system shall ...",
  "rationale": "Short engineering reason.",
  "verification_focus": "How this requirement can be verified.",
  "confidence": "MEDIUM"
}}

Rules:
- Generate exactly ONE requirement.
- Requirement must be a clear shall-statement.
- Keep all text concise.
- Make the requirement testable.
- The recommendation MUST remain semantically consistent with the EXISTING REQUIREMENT.
- Preserve the main function, component, failure mechanism and safety intent from the EXISTING REQUIREMENT.
- Do NOT introduce a new component, subsystem, sensor, hardware block, failure mode, hazard or operating condition that is not supported by the supplied context.
- Do NOT replace the existing requirement with a different safety concept.
- Do NOT invent numerical limits, timing values, voltage values, temperatures, distances, probabilities or performance targets.
- If an exact numerical value is not explicitly supported by the supplied context, use qualitative wording instead.
- If the existing requirement already provides the correct safety intent, refine its wording rather than inventing a new technical behavior.
- Do not assign ASIL.
- Do not claim certification.
- Do not add markdown.
"""

    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an automotive functional-safety "
                    "requirements engineer. Return valid JSON only."
                ),
            },
            {
                "role": "user",
                "content": "/no_think\n" + prompt,
            },
        ],
        "stream": False,
        "think": False,
        "keep_alive": -1,
        "format": "json",
        "options": {
            "temperature": 0.1,
            "num_predict": 220,
            "num_ctx": 1536,
        },
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            raw_result = json.loads(
                response.read().decode("utf-8")
            )
    except Exception as exc:
        print(
            f"[AI Requirement] Ollama request failed: {exc}"
        )
        return {
            "recommendation": "",
            "rationale": "",
            "verification_focus": "",
            "confidence": "LOW",
            "review_required": True,
        }

    message = raw_result.get("message", {})
    answer = str(message.get("content", "")).strip()

    if not answer:
        answer = str(
            raw_result.get("response", "")
        ).strip()

    print(
        f"[AI Requirement] Raw Qwen response: "
        f"{answer[:1200]}"
    )

    parsed = None

    # --------------------------------------------------------
    # 1. Normal JSON
    # --------------------------------------------------------
    try:
        parsed = json.loads(answer)
    except Exception:
        pass

    # --------------------------------------------------------
    # 2. JSON inside markdown/code/text
    # --------------------------------------------------------
    if parsed is None:
        first = answer.find("{")
        last = answer.rfind("}")

        if first != -1 and last > first:
            try:
                parsed = json.loads(
                    answer[first:last + 1]
                )
            except Exception:
                parsed = None

    if not isinstance(parsed, dict):
        print(
            "[AI Requirement] Could not parse Qwen JSON."
        )

        return {
            "recommendation": "",
            "rationale": "",
            "verification_focus": "",
            "confidence": "LOW",
            "review_required": True,
        }

    def pick(*keys):
        for key in keys:
            value = parsed.get(key)

            if value is not None and str(value).strip():
                return str(value).strip()

        return ""

    recommendation = pick(
        "recommendation",
        "Recommendation",
        "requirement",
        "Requirement",
        "candidate_requirement",
        "candidateRequirement",
        "fsr",
        "tsr",
    )

    rationale = pick(
        "rationale",
        "Rationale",
        "engineering_rationale",
        "engineeringRationale",
        "reason",
    )

    verification_focus = pick(
        "verification_focus",
        "verificationFocus",
        "Verification Focus",
        "verification",
        "test_focus",
    )

    confidence = pick(
        "confidence",
        "Confidence",
    ).upper()

    if confidence not in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }:
        confidence = "MEDIUM"

    print(
        f"[AI Requirement] {requirement_type} "
        f"recommendation parsed: "
        f"{bool(recommendation)}"
    )

    return {
        "recommendation": recommendation,
        "rationale": rationale,
        "verification_focus": verification_focus,
        "confidence": confidence,
        "review_required": True,
    }

