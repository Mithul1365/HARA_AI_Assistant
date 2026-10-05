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
            "num_predict": 140,
            "num_ctx": 1024,
            "temperature": 0.80,
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



def ask_qwen_hara_batch(prompt, summary_mode=False):
    """Generate three diverse HARA candidates in one Qwen call."""
    start_time = time.time()

    instruction = (
        "Generate EXACTLY THREE materially different HARA candidates. "
        "Keep every field very concise, preferably under 18 words. "
        "Do not explain your reasoning outside the Rationale field. "
        "Return ONLY valid JSON. "
        "Use this exact structure: "
        '{"candidates":[{"Potential Malfunction":"...",'
        '"Potential Hazard":"...",'
        '"Hazardous Event":"...",'
        '"Rationale":"..."},'
        '{"Potential Malfunction":"...",'
        '"Potential Hazard":"...",'
        '"Hazardous Event":"...",'
        '"Rationale":"..."},'
        '{"Potential Malfunction":"...",'
        '"Potential Hazard":"...",'
        '"Hazardous Event":"...",'
        '"Rationale":"..."}]} '
        "The three candidates MUST use different failure mechanisms. "
        "Prioritize returning all three candidates over detailed wording. "
        "Do not add markdown or explanation outside JSON."
    )

    data = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an automotive functional-safety engineering assistant. "
                    "Generate three distinct HARA candidates."
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
            "num_predict": 300,
            "num_ctx": 1024,
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
        print(f"[Qwen] Batch request failed: {exc}")
        return []

    message = result.get("message", {})
    answer = str(message.get("content", "")).strip()

    if not answer:
        answer = str(result.get("response", "")).strip()

    candidates = []

    # --------------------------------------------------------
    # ROBUST QWEN JSON PARSER
    # --------------------------------------------------------
    # Qwen may return:
    #   1. normal JSON
    #   2. JSON inside markdown fences
    #   3. a JSON object with one candidate
    #   4. slightly different field-name casing
    #   5. truncated/embedded JSON
    # --------------------------------------------------------

    cleaned = answer.strip()

    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r"\s*```$", "", cleaned)

    parsed_objects = []

    # First try the complete response.
    try:
        parsed_objects.append(json.loads(cleaned))
    except Exception:
        pass

    # If complete parsing fails, locate JSON objects/arrays inside the response.
    if not parsed_objects:
        decoder = json.JSONDecoder()

        for index, char in enumerate(cleaned):
            if char not in "{[":
                continue

            try:
                obj, consumed = decoder.raw_decode(cleaned[index:])
                parsed_objects.append(obj)
                break
            except Exception:
                continue

    for parsed in parsed_objects:

        # Standard batch response:
        # {"candidates": [...]}
        if isinstance(parsed, dict):
            raw_candidates = parsed.get("candidates", [])

            # Sometimes Qwen may return candidates as a JSON string.
            if isinstance(raw_candidates, str):
                try:
                    raw_candidates = json.loads(raw_candidates)
                except Exception:
                    raw_candidates = []

            # Sometimes it returns one candidate directly.
            if not raw_candidates and (
                parsed.get("Potential Malfunction")
                or parsed.get("potential_malfunction")
                or parsed.get("malfunction")
            ):
                raw_candidates = [parsed]

        elif isinstance(parsed, list):
            raw_candidates = parsed

        else:
            raw_candidates = []

        if isinstance(raw_candidates, dict):
            raw_candidates = [raw_candidates]

        if not isinstance(raw_candidates, list):
            raw_candidates = []

        for item in raw_candidates:
            if not isinstance(item, dict):
                continue

            def pick(*keys):
                for key in keys:
                    value = item.get(key)
                    if value is not None and str(value).strip():
                        return str(value).strip()
                return ""

            malfunction = pick(
                "Potential Malfunction",
                "potential_malfunction",
                "Potential malfunction",
                "malfunction",
            )

            hazard = pick(
                "Potential Hazard",
                "potential_hazard",
                "Potential hazard",
                "hazard",
            )

            hazardous_event = pick(
                "Hazardous Event",
                "hazardous_event",
                "Hazardous event",
                "hazardousEvent",
                "event",
            )

            rationale = pick(
                "Rationale",
                "rationale",
                "Engineering Rationale",
                "engineering_rationale",
            )

            if malfunction and hazard and hazardous_event and rationale:
                candidates.append(
                    {
                        "malfunction": malfunction,
                        "hazard": hazard,
                        "hazardous_event": hazardous_event,
                        "rationale": rationale,
                    }
                )

    # Remove exact duplicates.
    unique_candidates = []
    seen = set()

    for candidate in candidates:
        signature = (
            candidate["malfunction"].lower().strip(),
            candidate["hazard"].lower().strip(),
            candidate["hazardous_event"].lower().strip(),
        )

        if signature not in seen:
            seen.add(signature)
            unique_candidates.append(candidate)

    candidates = unique_candidates[:3]

    if not candidates:
        print("[Qwen] No valid batch candidates parsed.")
        print("[Qwen] Raw response preview:")
        print(answer[:2500])

    print(
        f"[Qwen] batch HARA generation total="
        f"{time.time() - start_time:.2f}s "
        f"candidates={len(candidates)}"
    )

    return candidates[:3]


def _detailed_hara(system, function, scenario, evidence):
    return (
        "AI HARA generation failed. "
        "No hard-coded HARA candidates were substituted."
    )


def _candidate_similarity(text_a, text_b):
    """Return lexical Jaccard similarity between two candidate texts."""
    import re

    def tokens(value):
        return {
            token
            for token in re.findall(r"[a-z0-9]+", str(value).lower())
            if len(token) >= 4
        }

    a = tokens(text_a)
    b = tokens(text_b)

    if not a or not b:
        return 0.0

    return len(a & b) / len(a | b)


def _candidate_signature(candidate):
    return (
        str(candidate.get("malfunction", "")).lower().strip(),
        str(candidate.get("hazard", "")).lower().strip(),
        str(candidate.get("hazardous_event", "")).lower().strip(),
    )

def _candidate_is_too_similar(candidate, accepted_candidates, threshold=0.85):
    """
    Reject genuinely duplicate or near-duplicate HARA candidates.

    The comparison is intentionally conservative so common engineering
    terminology does not cause valid candidates to be rejected.
    No domain-specific HARA answer is hardcoded.
    """
    import re

    def normalize(value):
        return {
            token
            for token in re.findall(r"[a-z0-9]+", str(value).lower())
            if len(token) >= 4
        }

    current_malfunction = normalize(candidate.get("malfunction", ""))
    current_full = normalize(" ".join([
        candidate.get("malfunction", ""),
        candidate.get("hazard", ""),
        candidate.get("hazardous_event", ""),
    ]))

    for previous in accepted_candidates:
        previous_malfunction = normalize(previous.get("malfunction", ""))
        previous_full = normalize(" ".join([
            previous.get("malfunction", ""),
            previous.get("hazard", ""),
            previous.get("hazardous_event", ""),
        ]))

        malfunction_similarity = 0.0
        if current_malfunction and previous_malfunction:
            malfunction_similarity = (
                len(current_malfunction & previous_malfunction)
                / len(current_malfunction | previous_malfunction)
            )

        full_similarity = 0.0
        if current_full and previous_full:
            full_similarity = (
                len(current_full & previous_full)
                / len(current_full | previous_full)
            )

        # Reject only when the malfunction itself is strongly similar,
        # or the complete HARA candidate is an obvious near-duplicate.
        if malfunction_similarity >= 0.70 or full_similarity >= threshold:
            return True

    return False



def analyze_with_qwen(system, function, scenario, evidence, summary_mode=False):
    """Generate three diverse AI-generated HARA candidates with one Qwen call."""
    start_time = time.time()

    evidence_lines = []

    for i, item in enumerate(evidence[:3], 1):
        source = item.get("source", "Engineering Document")
        page = item.get("page", "?")
        item_text = " ".join(str(item.get("text", "")).split())[:350]

        evidence_lines.append(
            f"Evidence {i} | Source: {source} | Page: {page}\n{item_text}"
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
- Generate three materially different failure mechanisms.
"""

    try:
        candidates = ask_qwen_hara_batch(
            base_prompt,
            summary_mode=summary_mode
        )

        valid = []

        for candidate in candidates:
            if all(
                candidate.get(key)
                for key in (
                    "malfunction",
                    "hazard",
                    "hazardous_event",
                    "rationale",
                )
            ):
                valid.append(candidate)

        unique = []
        seen = set()

        for candidate in valid:
            signature = (
                candidate["malfunction"].lower().strip(),
                candidate["hazard"].lower().strip(),
                candidate["hazardous_event"].lower().strip(),
            )

            if signature not in seen:
                seen.add(signature)
                unique.append(candidate)

        if not unique:
            raise ValueError("Qwen did not return a valid HARA candidate.")

        blocks = []

        for i, candidate in enumerate(unique[:3], 1):
            blocks.append(
                f"Scenario {i}\n"
                f"Potential Malfunction: {candidate['malfunction']}\n"
                f"Potential Hazard: {candidate['hazard']}\n"
                f"Hazardous Event: {candidate['hazardous_event']}\n"
                f"Rationale: {candidate['rationale']}"
            )

        result = "\n\n".join(blocks)

        print(
            f"[HARA] Qwen3 batch generation total="
            f"{time.time() - start_time:.2f}s "
            f"valid_candidates={len(unique)}"
        )

        return result

    except Exception as exc:
        print(f"[HARA] Qwen generation failed: {exc}")

        return (
            "AI HARA generation failed. "
            "No hard-coded HARA candidates were substituted. "
            f"Reason: {exc}"
        )


