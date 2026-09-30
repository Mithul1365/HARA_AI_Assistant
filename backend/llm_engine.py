import json
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:8b"


def _evidence_snippet(evidence, index=0, limit=500):
    if not evidence:
        return "Engineering evidence not available."
    item = evidence[min(index, len(evidence) - 1)]
    return str(item.get("text", "")).strip()[:limit]


def _quick_hara(system, function, scenario, evidence):
    """Fast HARA candidate generation using the user's item/function first.

    The uploaded evidence is supporting context only. Explicit user input
    gets priority so a Body Safety document cannot accidentally trigger
    the EV/BMS candidate set just because the PDF mentions batteries.
    """
    context = f"{system} {function} {scenario}".lower()
    evidence_text = " ".join(
        str(x.get("text", "")) for x in evidence[:3]
    ).lower()

    # Detect the engineering domain from the user's actual item/function
    # before looking at retrieved evidence.
    if any(k in context for k in (
        "body safety", "door safety", "vehicle door", "door status",
        "door open", "door closed", "body electronics", "lighting"
    )):
        candidates = [
            (
                "Door status monitoring fails to detect an improperly closed door.",
                "Unsafe door condition remains undetected.",
                "Vehicle continues driving while a door is not properly closed.",
            ),
            (
                "Door warning indication fails to alert the driver.",
                "Driver is not informed about the door condition.",
                "Vehicle operates while an improperly closed door remains unnoticed.",
            ),
            (
                "Door status signal is incorrectly reported.",
                "Incorrect door-closure information is provided.",
                "Vehicle continues operation based on an incorrect door-closed status.",
            ),
        ]

    elif any(k in context for k in (
        "bms", "battery management", "battery pack", "pyro-fuse",
        "pyrofuse", "high-voltage battery", "high voltage battery",
        "electric vehicle", "ev"
    )):
        candidates = [
            (
                "BMS fails to detect abnormal battery temperature.",
                "Thermal runaway in the high-voltage battery pack.",
                "Battery overheating progresses to a potential thermal event or fire.",
            ),
            (
                "High-voltage battery isolation or pyro-fuse disconnection fails when required.",
                "Unsafe high-voltage energy remains connected.",
                "Battery remains connected during a fault or collision event.",
            ),
            (
                "Pyro-fuse trigger or energy-reservoir circuit fails.",
                "Battery disconnection is unavailable when required.",
                "High-voltage battery isolation is not achieved during a fault.",
            ),
        ]

    elif any(k in context for k in ("steering", "eps")):
        candidates = [
            (
                "Steering assistance fails.",
                "Reduced ability to control the vehicle path.",
                "Driver has difficulty maintaining the intended vehicle path.",
            ),
            (
                "Steering assistance is applied unintentionally.",
                "Unexpected vehicle directional response.",
                "Vehicle trajectory changes without the intended driver command.",
            ),
            (
                "EPS control or communication fails.",
                "Required steering safety response is unavailable.",
                "A steering fault remains active without timely mitigation.",
            ),
        ]

    elif any(k in context for k in ("brake", "braking", "emb")):
        candidates = [
            (
                "Brake actuation fails when braking is requested.",
                "Insufficient braking capability.",
                "Vehicle deceleration is lower than required.",
            ),
            (
                "Brake control information is incorrect.",
                "Incorrect brake response.",
                "Vehicle does not achieve the intended braking response.",
            ),
            (
                "Brake fault isolation or fallback fails.",
                "Loss of the required safe braking state.",
                "A brake fault persists without timely mitigation.",
            ),
        ]

    # Only use evidence-based domain detection when the user did not
    # provide enough domain-specific wording.
    elif any(k in evidence_text for k in (
        "door status", "door open", "door closed", "door warning"
    )):
        candidates = [
            (
                "Door status monitoring fails to detect an improperly closed door.",
                "Unsafe door condition remains undetected.",
                "Vehicle continues driving while a door is not properly closed.",
            ),
            (
                "Door warning indication fails to alert the driver.",
                "Driver is not informed about the door condition.",
                "Vehicle operates while an improperly closed door remains unnoticed.",
            ),
            (
                "Door status signal is incorrectly reported.",
                "Incorrect door-closure information is provided.",
                "Vehicle continues operation based on an incorrect door-closed status.",
            ),
        ]
    else:
        candidates = [
            (
                "Safety-relevant monitoring fails to detect a fault.",
                "Unsafe operating condition remains undetected.",
                "Vehicle continues operation while a hazardous condition is present.",
            ),
            (
                "Safety-relevant control fails to execute the required response.",
                "Required protective action is unavailable.",
                "The hazardous condition continues without timely mitigation.",
            ),
            (
                "Safety-relevant communication or diagnosis fails.",
                "Fault information or safety commands are unavailable.",
                "A hazardous condition is not detected or controlled in time.",
            ),
        ]

    return "\n\n".join(
        f"Scenario {i}\n"
        f"Malfunction: {m}\n"
        f"Hazard: {h}\n"
        f"Hazardous Event: {e}"
        for i, (m, h, e) in enumerate(candidates, 1)
    )


def ask_qwen(prompt, summary_mode=False):
    start_time = time.time()
    if summary_mode:
        mode_instruction = (
            "/no_think\nReturn exactly 3 very short HARA scenarios. "
            "Use only: Scenario, Potential Malfunction, Potential Hazard, Hazardous Event, Rationale, Evidence. "
            "Each field must be one short sentence. No introduction."
        )
        max_tokens, num_ctx = 150, 1536
    else:
        # FAST DETAILED MODE:
        # Ask Qwen for only the engineering core. The UI already has the
        # structured HARA fields, so generating long repeated text here
        # wastes CPU time.
        mode_instruction = (
            "/no_think\n"
            "Return exactly 3 HARA candidates. "
            "For each candidate give only: Malfunction, Hazard, Event, Rationale. "
            "Keep every field extremely short. "
            "Maximum about 20 words per field. "
            "No introduction, no conclusion, no Evidence section."
        )
        max_tokens, num_ctx = 220, 1536

    data = {
        "model": MODEL_NAME,
        "prompt": mode_instruction + "\n\n" + prompt,
        "stream": False,
        "think": False,
        "keep_alive": -1,
        "options": {"num_predict": max_tokens, "num_ctx": num_ctx, "temperature": 0},
    }
    request = urllib.request.Request(
        OLLAMA_URL, data=json.dumps(data).encode("utf-8"),
        headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"[Qwen] Request failed: {exc}")
        return "Qwen3 could not be reached. Please ensure Ollama is running."
    answer = result.get("response", "").strip()
    print(f"[Qwen] mode={'quick' if summary_mode else 'detailed'} total={time.time()-start_time:.2f}s")
    return answer or "Qwen3 did not return a response."


def _detailed_hara(system, function, scenario, evidence):
    """Structured detailed HARA with compact retrieved engineering evidence."""

    # Reuse the same domain-aware candidates as Quick mode, then add the
    # engineering rationale and a short evidence excerpt.
    quick_text = _quick_hara(system, function, scenario, evidence)

    # Parse the three compact candidates generated above.
    blocks = quick_text.split("\n\n")
    out = []

    evidence_items = evidence[:3] if evidence else []

    for i, block in enumerate(blocks, 1):
        fields = {}
        for line in block.splitlines():
            if ":" in line:
                key, value = line.split(":", 1)
                fields[key.strip().lower()] = value.strip()

        ev = ""
        if evidence_items:
            item = evidence_items[(i - 1) % len(evidence_items)]
            source = item.get("source", "Engineering Document")
            page = item.get("page", "?")
            excerpt = " ".join(str(item.get("text", "")).split())[:320]
            ev = f"{source}, Page {page} â€” {excerpt}"
        else:
            ev = "No retrieved engineering evidence available."

        out.append(
            f"Scenario {i}\n"
            f"Potential Malfunction: {fields.get('malfunction', '')}\n"
            f"Potential Hazard: {fields.get('hazard', '')}\n"
            f"Hazardous Event: {fields.get('hazardous event', '')}\n"
            f"Rationale: This candidate is supported by the system function, operational scenario, and retrieved engineering evidence.\n"
            f"Engineering Evidence: {ev}"
        )

    return "\n\n".join(out)


def analyze_with_qwen(system, function, scenario, evidence, summary_mode=False):
    """Generate HARA candidates with Qwen3 and keep a deterministic fallback."""

    start_time = time.time()

    evidence_lines = []

    for i, item in enumerate(evidence[:5], 1):
        source = item.get("source", "Engineering Document")
        page = item.get("page", "?")
        text = " ".join(str(item.get("text", "")).split())[:700]

        evidence_lines.append(
            f"Evidence {i} | Source: {source} | Page: {page}\n{text}"
        )

    evidence_text = "\n\n".join(evidence_lines)

    prompt = f"""
You are an automotive functional-safety engineering assistant.

Generate HARA candidates only for the exact automotive system and scenario
provided below.

SYSTEM / ITEM:
{system}

INTENDED FUNCTION:
{function}

OPERATIONAL SCENARIO:
{scenario}

RETRIEVED ENGINEERING EVIDENCE:
{evidence_text}

STRICT RULES:
1. Stay strictly within the provided System, Function and Scenario.
2. Use the retrieved engineering evidence as supporting context.
3. Do not introduce unrelated domains or non-automotive examples.
4. Do not invent evidence, sources, page numbers, measurements, or facts.
5. Generate exactly 3 plausible HARA candidates.
6. Each candidate must contain:
   Potential Malfunction:
   Potential Hazard:
   Hazardous Event:
   Rationale:
7. Keep every field concise and engineering-focused.
8. Do not assign ASIL.
9. Do not claim ISO 26262 compliance or safety approval.
10. Return only the three candidates.
"""

    try:
        answer = ask_qwen(
            prompt,
            summary_mode=summary_mode
        )

        lower = answer.lower()

        invalid_markers = [
            "could not be reached",
            "did not return a response",
            "kitchen",
            "bathroom",
            "household",
        ]

        # Validate that Qwen returned three complete HARA candidates.
        blocks = [
            block.strip()
            for block in answer.split("\n\n")
            if block.strip()
        ]

        required_fields = [
            "potential malfunction:",
            "potential hazard:",
            "hazardous event:",
            "rationale:",
        ]

        complete_candidates = 0

        for block in blocks:
            block_lower = block.lower()

            if all(
                field in block_lower
                for field in required_fields
            ):
                complete_candidates += 1

        if (
            not answer.strip()
            or any(marker in lower for marker in invalid_markers)
            or complete_candidates != 3
        ):
            raise ValueError(
                "Qwen returned an incomplete or invalid HARA response."
            )

        print(
            f"[HARA] Qwen3 generation total="
            f"{time.time() - start_time:.2f}s"
        )

        return answer

    except Exception as exc:
        print(f"[HARA] Qwen fallback: {exc}")

        if summary_mode:
            result = _quick_hara(
                system,
                function,
                scenario,
                evidence
            )
        else:
            result = _detailed_hara(
                system,
                function,
                scenario,
                evidence
            )

        print(
            f"[HARA] deterministic fallback total="
            f"{time.time() - start_time:.3f}s"
        )

        return result


