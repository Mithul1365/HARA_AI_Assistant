import json
import re
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL_NAME = "qwen3:4b"


def _evidence_snippet(evidence, index=0, limit=700):
    if not evidence:
        return "Engineering evidence not available."
    item = evidence[min(index, len(evidence) - 1)]
    return str(item.get("text", "")).strip()[:limit]


def _quick_hara(system, function, scenario, evidence):
    # Compatibility only. No hard-coded HARA candidates.
    return (
        "AI HARA generation failed. "
        "No hard-coded HARA candidates were substituted."
    )


def ask_qwen(prompt, summary_mode=False):
    """Generate one AI HARA candidate. analyze_with_qwen calls this 3 times."""
    start_time = time.time()

    instruction = (
        "Generate ONE HARA candidate from the supplied engineering context. "
        "Analyze the system yourself; do not use predefined domain-specific examples. "
        "Return ONLY a JSON object with exactly these four string fields: "
        "Potential Malfunction, Potential Hazard, Hazardous Event, Rationale. "
        "Keep every field concise. Do not return an array. Do not add markdown or explanation."
    )

    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an automotive functional-safety engineering assistant. "
                    "Identify a plausible malfunction from the supplied system, function, "
                    "scenario and engineering evidence."
                ),
            },
            {
                "role": "user",
                "content": "/no_think\n" + instruction + "\n\n" + prompt,
            },
        ],
        "stream": False,
        "think": False,
        "keep_alive": -1,
        "format": "json",
        "options": {
            "num_predict": 180,
            "num_ctx": 2048,
            "temperature": 0,
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
            result = json.loads(response.read().decode("utf-8"))
    except Exception as exc:
        print(f"[Qwen] Request failed: {exc}")
        return "Qwen3 could not be reached. Please ensure Ollama is running."

    message = result.get("message", {})
    answer = str(message.get("content", "")).strip()

    if not answer:
        answer = str(result.get("response", "")).strip()

    print(
        f"[Qwen] mode={'quick' if summary_mode else 'detailed'} "
        f"total={time.time() - start_time:.2f}s"
    )
    return answer or "Qwen3 did not return a response."


def _normalise_key(key):
    key = re.sub(r"[^a-z0-9]+", " ", str(key).lower()).strip()

    aliases = {
        "potential malfunction": "potential malfunction",
        "malfunction": "potential malfunction",
        "potential hazard": "potential hazard",
        "hazard": "potential hazard",
        "hazardous event": "hazardous event",
        "event": "hazardous event",
        "rationale": "rationale",
    }
    return aliases.get(key, key)


def _parse_qwen_hara(answer):
    candidates = []

    # First try JSON, because ask_qwen requests JSON.
    try:
        cleaned = answer.strip()

        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
            cleaned = re.sub(r"\s*```$", "", cleaned)

        parsed = json.loads(cleaned)

        if isinstance(parsed, dict):
            if isinstance(parsed.get("candidates"), list):
                parsed = parsed["candidates"]
            elif all(k in parsed for k in (
                "Potential Malfunction",
                "Potential Hazard",
                "Hazardous Event",
            )):
                parsed = [parsed]

        if isinstance(parsed, list):
            for item in parsed:
                if not isinstance(item, dict):
                    continue

                normalized = {
                    _normalise_key(k): str(v).strip()
                    for k, v in item.items()
                }

                if (
                    normalized.get("potential malfunction")
                    and normalized.get("potential hazard")
                    and normalized.get("hazardous event")
                ):
                    candidates.append({
                        "malfunction": normalized["potential malfunction"],
                        "hazard": normalized["potential hazard"],
                        "hazardous_event": normalized["hazardous event"],
                        "rationale": normalized.get("rationale", ""),
                    })

            if candidates:
                return candidates[:3]

    except Exception:
        pass

    # Fallback parser for plain-text Qwen output.
    lines = [line.strip() for line in answer.splitlines() if line.strip()]
    current = {}

    label_patterns = [
        (r"^(?:potential\s+)?malfunction\s*:\s*", "malfunction"),
        (r"^(?:potential\s+)?hazard\s*:\s*", "hazard"),
        (r"^hazardous\s+event\s*:\s*", "hazardous_event"),
        (r"^rationale\s*:\s*", "rationale"),
    ]

    def flush():
        nonlocal current
        if (
            current.get("malfunction")
            and current.get("hazard")
            and current.get("hazardous_event")
        ):
            candidates.append({
                "malfunction": current["malfunction"],
                "hazard": current["hazard"],
                "hazardous_event": current["hazardous_event"],
                "rationale": current.get("rationale", ""),
            })
        current = {}

    for line in lines:
        if re.match(r"^(?:scenario|candidate)\s*\d*\s*[:.\-]?\s*$", line, re.I):
            if current:
                flush()
            continue

        matched = False

        for pattern, key in label_patterns:
            match = re.match(pattern, line, re.I)

            if match:
                if key == "malfunction" and current.get("malfunction"):
                    flush()

                current[key] = line[match.end():].strip()
                matched = True
                break

        if not matched and current:
            last_key = list(current.keys())[-1]
            current[last_key] = (
                current[last_key] + " " + line
            ).strip()

    if current:
        flush()

    unique = []
    seen = set()

    for candidate in candidates:
        key = (
            candidate["malfunction"].lower(),
            candidate["hazard"].lower(),
            candidate["hazardous_event"].lower(),
        )

        if key not in seen:
            seen.add(key)
            unique.append(candidate)

    return unique[:3]


def _detailed_hara(system, function, scenario, evidence):
    return (
        "AI HARA generation failed. "
        "No hard-coded HARA candidates were substituted."
    )


def analyze_with_qwen(system, function, scenario, evidence, summary_mode=False):
    """Generate exactly three independent AI-generated HARA candidates."""
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

    base_prompt = f"""
SYSTEM / ITEM:
{system}

INTENDED FUNCTION:
{function}

OPERATIONAL SCENARIO:
{scenario}

RETRIEVED ENGINEERING EVIDENCE:
{evidence_text}

Rules:
- Analyze this exact automotive system and scenario.
- Use retrieved evidence as supporting context.
- Identify the malfunction yourself.
- Do not use predefined domain-specific HARA candidates.
- Do not invent sources, page numbers, measurements, or unsupported facts.
- Do not assign ASIL.
- Do not claim ISO 26262 compliance or safety approval.
"""

    candidates = []
    used_signatures = set()

    angles = [
        "Focus on failure to perform the intended protective function.",
        "Focus on unintended, incorrect, or false activation of the protective function.",
        "Focus on failure to detect, command, communicate, or respond to the relevant fault.",
    ]

    try:
        # Up to 6 AI calls: normally 3, with retries if Qwen duplicates a candidate.
        for candidate_number in range(1, 4):
            accepted = False

            for attempt in range(1, 3):
                diversity = (
                    f"\nGenerate candidate {candidate_number} of 3. "
                    f"{angles[candidate_number - 1]} "
                    "It MUST be materially different from previously generated candidates. "
                    "Do not repeat the same malfunction, hazard, or hazardous event."
                )

                if used_signatures:
                    diversity += (
                        "\nPreviously accepted candidates (do not duplicate them):\n"
                        + "\n".join(
                            f"- {sig[0]}" for sig in used_signatures
                        )
                    )

                answer = ask_qwen(
                    base_prompt + diversity,
                    summary_mode=summary_mode
                )

                parsed = _parse_qwen_hara(answer)

                if not parsed:
                    print(
                        f"[HARA] Candidate {candidate_number}, attempt {attempt}: "
                        "Qwen response could not be parsed."
                    )
                    continue

                candidate = parsed[0]

                signature = (
                    candidate["malfunction"].lower().strip(),
                    candidate["hazard"].lower().strip(),
                    candidate["hazardous_event"].lower().strip(),
                )

                if signature in used_signatures:
                    print(
                        f"[HARA] Candidate {candidate_number}, attempt {attempt}: "
                        "duplicate; retrying AI generation."
                    )
                    continue

                candidates.append(candidate)
                used_signatures.add(signature)
                accepted = True
                break

            if not accepted:
                raise ValueError(
                    f"Qwen could not generate a unique candidate {candidate_number}."
                )

        blocks = []

        for i, candidate in enumerate(candidates, 1):
            blocks.append(
                f"Scenario {i}\n"
                f"Potential Malfunction: {candidate['malfunction']}\n"
                f"Potential Hazard: {candidate['hazard']}\n"
                f"Hazardous Event: {candidate['hazardous_event']}\n"
                f"Rationale: {candidate['rationale']}"
            )

        result = "\n\n".join(blocks)

        print(
            f"[HARA] Qwen3 3-candidate generation total="
            f"{time.time() - start_time:.2f}s"
        )

        return result

    except Exception as exc:
        print(f"[HARA] Qwen generation failed: {exc}")

        return (
            "AI HARA generation failed. "
            "No hard-coded HARA candidates were substituted. "
            f"Reason: {exc}"
        )

