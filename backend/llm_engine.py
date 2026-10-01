import json
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen3:4b"


def _evidence_snippet(evidence, index=0, limit=500):
    if not evidence:
        return "Engineering evidence not available."
    item = evidence[min(index, len(evidence) - 1)]
    return str(item.get("text", "")).strip() if "user-provided item definition" in str(item.get("source", "")).lower() else str(item.get("text", "")).strip()[:limit]


def _quick_hara(system, function, scenario, evidence):
    """Generate fast, function-specific HARA candidates from the item definition."""
    context = f"{system} {function} {scenario}".lower()

    # BODY / BCM / CENTRAL DOOR LOCKING
    if (
        any(k in context for k in (
            "body control module", "body control", "bcm",
            "central door locking", "central locking",
            "door locking", "door lock", "vehicle door",
        ))
        or any(k in context for k in ("door", "locking"))
    ):
        if any(k in context for k in (
            "fails to keep the doors locked",
            "fail to keep the doors locked",
            "doors remain unlocked",
            "door remains unlocked",
            "fails to lock",
            "cannot lock",
            "unable to lock",
            "locking function fails",
        )):
            candidates = [
                (
                    "Central door locking fails to keep one or more doors locked.",
                    "A vehicle door remains unsecured during vehicle motion.",
                    "An occupant is exposed to an unsecured door condition while the vehicle is moving.",
                ),
                (
                    "Door-lock status is incorrectly reported as locked.",
                    "An unlocked door condition remains undetected.",
                    "The vehicle continues moving while the occupant or driver believes the door is secured.",
                ),
                (
                    "Door-locking failure is not detected or indicated to the driver.",
                    "The driver is not warned about an unsecured door.",
                    "The vehicle continues operation with an unsecured door condition that is not timely recognized.",
                ),
            ]
        else:
            candidates = [
                (
                    "Central door locking command is not executed as intended.",
                    "One or more doors are not secured when required.",
                    "The vehicle operates with an unintended unsecured door condition.",
                ),
                (
                    "Door-lock status is incorrectly detected or reported.",
                    "The actual door security state is unknown or misrepresented.",
                    "The driver or occupants rely on an incorrect door-lock status during vehicle operation.",
                ),
                (
                    "Door-locking fault is not detected or indicated.",
                    "An unsafe door condition remains without timely warning.",
                    "Vehicle operation continues while the door condition is not recognized.",
                ),
            ]

    # EV / BATTERY
    elif any(k in context for k in (
        "bms", "battery management", "battery pack", "pyro-fuse",
        "pyrofuse", "high-voltage battery", "high voltage battery",
        "electric vehicle",
    )):
        candidates = [
            (
                "BMS fails to detect abnormal battery temperature.",
                "Battery thermal conditions become unsafe.",
                "Battery overheating progresses toward a potential thermal event.",
            ),
            (
                "High-voltage battery isolation fails when required.",
                "Unsafe high-voltage energy remains connected.",
                "The battery remains electrically connected during a fault or collision event.",
            ),
            (
                "Battery fault detection or protection fails.",
                "Required battery protective action is unavailable.",
                "A hazardous battery condition persists without timely mitigation.",
            ),
        ]

    # STEERING
    elif any(k in context for k in ("steering", "eps")):
        candidates = [
            (
                "Steering assistance fails when requested.",
                "Required steering capability is reduced or unavailable.",
                "The driver has difficulty maintaining the intended vehicle path.",
            ),
            (
                "Steering assistance is applied unintentionally.",
                "Unexpected steering response occurs.",
                "Vehicle trajectory changes without the intended driver command.",
            ),
            (
                "Steering control or communication fails.",
                "The required steering safety response is unavailable.",
                "A steering fault remains active without timely mitigation.",
            ),
        ]

    # BRAKING
    elif any(k in context for k in ("brake", "braking", "emb")):
        candidates = [
            (
                "Brake actuation fails when braking is requested.",
                "Required braking capability is reduced or unavailable.",
                "Vehicle deceleration is lower than required during a braking event.",
            ),
            (
                "Brake control information is incorrect.",
                "The commanded braking response is incorrect.",
                "The vehicle does not achieve the intended braking response.",
            ),
            (
                "Brake fault isolation or fallback fails.",
                "The required safe braking state is unavailable.",
                "A brake fault persists without timely mitigation.",
            ),
        ]

    # GENERIC FUNCTION-AWARE FALLBACK
    else:
        function_text = function.strip() or "the intended vehicle function"
        candidates = [
            (
                f"{function_text} fails to perform its intended function.",
                "The intended function becomes unavailable during the specified operation.",
                "The vehicle remains in a potentially hazardous operating condition.",
            ),
            (
                f"{function_text} provides an incorrect or unintended response.",
                "The vehicle receives an incorrect functional response.",
                "Vehicle behavior deviates from the intended operating condition.",
            ),
            (
                f"A fault affecting {function_text.lower()} is not detected in time.",
                "The resulting unsafe condition remains unrecognized.",
                "Vehicle operation continues while the fault is present.",
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
            page = item.get("page", None)
            raw_text = str(item.get("text", "")).strip()

            # User-provided item definitions must be shown completely.
            # Retrieved PDF evidence is shown in full so engineering context is not lost.
            is_user_definition = (
                "user-provided item definition" in source.lower()
                or "engineer-provided item definition" in source.lower()
            )

            if is_user_definition:
                formatted_text = raw_text
                page_label = "Not applicable"
            else:
                formatted_text = " ".join(raw_text.split())
                page_label = page if page not in (None, "", "—", "-") else "Not available"

            ev = f"{source}, Page {page_label} — {formatted_text}"
        else:
            ev = "No retrieved engineering evidence available."

        out.append(
            f"Scenario {i}\n"
            f"Potential Malfunction: {fields.get('malfunction', '')}\n"
            f"Potential Hazard: {fields.get('hazard', '')}\n"
            f"Hazardous Event: {fields.get('hazardous event', '')}\n"
            f"Rationale: The malfunction is directly related to the stated function and operating scenario; retrieved evidence is supporting context.\n"
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

    result = _detailed_hara(system, function, scenario, evidence)
    print(f"[HARA] detailed local generation total={time.time() - start_time:.3f}s")
    return result



