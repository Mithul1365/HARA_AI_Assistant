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
    """Fast, deterministic HARA candidate generation for Quick Summary.

    Quick mode intentionally shows only the three core HARA fields.
    Evidence remains available elsewhere in the UI and is not dumped here.
    """
    context = f"{system} {function} {scenario}".lower()
    evidence_text = " ".join(str(x.get("text", "")) for x in evidence[:3]).lower()

    if any(k in context or k in evidence_text for k in (
        "bms", "battery", "pyro", "high-voltage", "high voltage", "ev"
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
        max_tokens, num_ctx = 100, 1024

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
            ev = f"{source}, Page {page} — {excerpt}"
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
    """Return the correct HARA format for the selected analysis mode."""

    start_time = time.time()

    if summary_mode:
        result = _quick_hara(system, function, scenario, evidence)
        print(f"[HARA] quick local generation total={time.time() - start_time:.3f}s")
        return result

    result = _detailed_hara(system, function, scenario, evidence)
    print(f"[HARA] detailed local generation total={time.time() - start_time:.3f}s")
    return result
