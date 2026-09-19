from common import *

init_page("HARA AI Assistant — ASIL Assessment")
page_header("FUNCTIONAL SAFETY", "ASIL Assessment", "S/E/C assessment and candidate ASIL decision support.")

# 5. S / E / C ASSESSMENT
# =========================================================

st.header(
    "5. S / E / C Assessment"
)

st.write(
    "First select the HARA candidate, then assess Severity, "
    "Exposure and Controllability. Candidate ASIL and downstream "
    "Safety Goal become available only after this assessment is completed."
)


# =========================================================
# HARA CANDIDATE EXTRACTION
# =========================================================

def extract_hara_candidates(hara_text):
    """Convert HARA text into structured candidates robustly."""
    candidates = []
    if not hara_text:
        return candidates

    text = str(hara_text).replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("**", "").replace("__", "")
    lines = [line.strip() for line in text.splitlines() if line.strip()]

    # First try the normal labelled format.  Labels may be prefixed by
    # Scenario 1:, bullets, numbering, or markdown.
    current = {"malfunction": "", "hazard": ""}
    label_re = {
        "malfunction": re.compile(r"^(?:[-*•\s\d\.)]+)?(?:potential\s+)?malfunction\s*:\s*(.+)$", re.I),
        "hazard": re.compile(r"^(?:[-*•\s\d\.)]+)?(?:potential\s+)?hazard\s*:\s*(.+)$", re.I),
        "event": re.compile(r"^(?:[-*•\s\d\.)]+)?hazardous\s+event\s*:\s*(.+)$", re.I),
    }

    for raw in lines:
        line = raw.strip()
        # Remove a leading Scenario N: marker but keep the rest of the line.
        line = re.sub(r"^scenario\s*\d+\s*:\s*", "", line, flags=re.I)
        line = re.sub(r"^[\s\d\.\)\-•*]+", "", line).strip()

        m = label_re["malfunction"].match(line)
        if m:
            current = {"malfunction": m.group(1).strip(), "hazard": ""}
            continue
        m = label_re["hazard"].match(line)
        if m:
            current["hazard"] = m.group(1).strip()
            continue
        m = label_re["event"].match(line)
        if m and current.get("hazard"):
            candidates.append({
                "malfunction": current.get("malfunction") or "Identified malfunction",
                "hazard": current["hazard"],
                "hazardous_event": m.group(1).strip(),
            })
            current = {"malfunction": "", "hazard": ""}

    # Support compact one-line chains: M -> H -> HE or M → H → HE.
    if len(candidates) < 3:
        for raw in lines:
            line = re.sub(r"^scenario\s*\d+\s*:\s*", "", raw, flags=re.I)
            line = re.sub(r"^[\s\d\.\)\-•*]+", "", line).strip()
            if "→" in line:
                parts = [p.strip() for p in line.split("→") if p.strip()]
            elif "->" in line:
                parts = [p.strip() for p in line.split("->") if p.strip()]
            else:
                continue
            if len(parts) >= 3:
                candidates.append({"malfunction": parts[0], "hazard": parts[1], "hazardous_event": parts[2]})

    # If Qwen returned fewer than three candidates, preserve what it did return.
    # The quick mode itself now guarantees three structured candidates, so this
    # fallback mainly protects against truncated model output in detailed mode.
    unique = []
    seen = set()
    for c in candidates:
        key = tuple(c[k].strip().lower() for k in ("malfunction", "hazard", "hazardous_event"))
        if key not in seen:
            seen.add(key)
            unique.append(c)
    return unique


# =========================================================
# SELECT HARA CANDIDATE BEFORE S/E/C
# =========================================================

hara_candidates = []

if "hara_answer" in st.session_state:

    hara_candidates = extract_hara_candidates(
        st.session_state["hara_answer"]
    )

if not hara_candidates:

    st.warning(
        "Run HARA Analysis first. A structured HARA candidate "
        "is required before S/E/C assessment."
    )

else:

    st.success(
        f"{len(hara_candidates)} HARA candidate(s) detected automatically."
    )

    # -----------------------------------------------------
    # HARA CANDIDATE PRIORITIZATION
    # -----------------------------------------------------
    # Do not silently select the first AI-generated candidate.
    # Rank candidates using transparent engineering heuristics,
    # then require the user/engineer to explicitly choose one.
    #
    # This is NOT an ASIL calculation and does not replace
    # functional-safety engineering judgement.

    def calculate_hara_priority(candidate):

        text = " ".join(
            [
                candidate.get("malfunction", ""),
                candidate.get("hazard", ""),
                candidate.get("hazardous_event", "")
            ]
        ).lower()

        high_risk_terms = [
            "loss of control",
            "uncontrolled",
            "unintended",
            "loss of steering",
            "loss of braking",
            "braking failure",
            "steering failure",
            "collision",
            "crash",
            "critical",
            "high speed",
            "loss of assistance"
        ]

        medium_risk_terms = [
            "shutdown",
            "communication failure",
            "communication loss",
            "diagnostic",
            "degraded",
            "delayed",
            "malfunction"
        ]

        high_hits = sum(
            1
            for term in high_risk_terms
            if term in text
        )

        medium_hits = sum(
            1
            for term in medium_risk_terms
            if term in text
        )

        score = (
            high_hits * 3
            + medium_hits
        )

        if high_hits >= 2:
            priority = "High"
        elif high_hits >= 1 or medium_hits >= 2:
            priority = "Medium"
        else:
            priority = "Normal"

        return score, priority


    ranked_candidates = []

    for original_index, candidate in enumerate(
        hara_candidates
    ):

        score, priority = calculate_hara_priority(
            candidate
        )

        ranked_candidates.append(
            {
                "original_index": original_index,
                "candidate": candidate,
                "score": score,
                "priority": priority
            }
        )

    ranked_candidates.sort(
        key=lambda item: (
            -item["score"],
            item["original_index"]
        )
    )

    st.info(
        "Multiple HARA candidates were identified. Select the candidate "
        "you want to assess for S/E/C. The selection does not change the AI result."
    )

    candidate_labels = []

    for rank, item in enumerate(
        ranked_candidates,
        start=1
    ):

        candidate = item["candidate"]

        candidate_labels.append(
            f"{rank}. [{item['priority']}] "
            f"{candidate['malfunction']} → "
            f"{candidate['hazard']} → "
            f"{candidate['hazardous_event']}"
        )

    selected_rank = st.selectbox(
        "Select HARA Candidate for S/E/C Assessment",
        ["-- Select a HARA candidate --"]
        + candidate_labels,
        index=0,
        key="hara_candidate_selection"
    )

    if selected_rank == "-- Select a HARA candidate --":

        st.warning(
            "Select a HARA candidate above to continue "
            "to S/E/C assessment."
        )

        st.stop()

    selected_position = candidate_labels.index(
        selected_rank
    )

    selected_candidate = ranked_candidates[
        selected_position
    ]["candidate"]

    current_hara_key = (
        selected_candidate["malfunction"].strip().lower(),
        selected_candidate["hazard"].strip().lower(),
        selected_candidate["hazardous_event"].strip().lower()
    )

    previous_hara_key = st.session_state.get(
        "active_hara_key"
    )

    if (
        previous_hara_key is not None
        and current_hara_key != previous_hara_key
    ):

        st.session_state.pop("candidate_asil", None)
        st.session_state.pop("asil_rationale", None)
        st.session_state.pop("asil_severity", None)
        st.session_state.pop("asil_exposure", None)
        st.session_state.pop("asil_controllability", None)
        st.session_state.pop("asil_input_tuple", None)
        st.session_state.pop("asil_assessment_completed", None)
        st.session_state.pop("safety_goal_result", None)
        st.session_state.pop("safety_goal_hara_key", None)
        st.session_state.pop("fsr_results", None)
        st.session_state.pop("tsr_results", None)
        st.session_state.pop("tsr_fsr_id", None)
        st.session_state.pop("traceability_rows", None)

    st.session_state["active_hara_key"] = current_hara_key

    with st.container(border=True):

        st.markdown(
            "### Selected HARA Candidate"
        )

        st.write(
            f"**Malfunction:** "
            f"{selected_candidate['malfunction']}"
        )

        st.write(
            f"**Hazard:** "
            f"{selected_candidate['hazard']}"
        )

        st.write(
            f"**Hazardous Event:** "
            f"{selected_candidate['hazardous_event']}"
        )


# =========================================================
# S / E / C INPUTS
# =========================================================

if hara_candidates:

    col1, col2, col3 = st.columns(3)

    with col1:

        severity = st.selectbox(
            "Severity (S)",
            [
                "S0",
                "S1",
                "S2",
                "S3"
            ],
            index=None,
            placeholder="Select Severity (S)",
            key="severity_selection"
        )

    with col2:

        exposure = st.selectbox(
            "Exposure (E)",
            [
                "E0",
                "E1",
                "E2",
                "E3",
                "E4"
            ],
            index=None,
            placeholder="Select Exposure (E)",
            key="exposure_selection"
        )

    with col3:

        controllability = st.selectbox(
            "Controllability (C)",
            [
                "C0",
                "C1",
                "C2",
                "C3"
            ],
            index=None,
            placeholder="Select Controllability (C)",
            key="controllability_selection"
        )

    se_assessment_complete = all(
        value is not None
        for value in (
            severity,
            exposure,
            controllability
        )
    )

    st.caption(
        "S/E/C values are engineering inputs. "
        "Candidate ASIL requires functional-safety engineer review."
    )

    if not se_assessment_complete:

        st.info(
            "Select Severity (S), Exposure (E), and "
            "Controllability (C) to enable Candidate ASIL calculation."
        )

    current_asil_inputs = (
        severity,
        exposure,
        controllability
    )

    stored_asil_inputs = st.session_state.get(
        "asil_input_tuple"
    )

    if (
        stored_asil_inputs is not None
        and current_asil_inputs != stored_asil_inputs
    ):

        st.session_state.pop("candidate_asil", None)
        st.session_state.pop("asil_rationale", None)
        st.session_state.pop("asil_severity", None)
        st.session_state.pop("asil_exposure", None)
        st.session_state.pop("asil_controllability", None)
        st.session_state.pop("asil_input_tuple", None)
        st.session_state.pop("asil_assessment_completed", None)
        st.session_state.pop("safety_goal_result", None)
        st.session_state.pop("safety_goal_hara_key", None)
        st.session_state.pop("fsr_results", None)
        st.session_state.pop("tsr_results", None)
        st.session_state.pop("tsr_fsr_id", None)
        st.session_state.pop("traceability_rows", None)

    # =====================================================
    # CALCULATE ASIL
    # =====================================================

    if st.button(
        "🧮 Calculate Candidate ASIL",
        disabled=not se_assessment_complete
    ):

        candidate_asil = calculate_asil(
            severity=severity,
            exposure=exposure,
            controllability=controllability
        )

        asil_rationale = get_asil_rationale(
            severity=severity,
            exposure=exposure,
            controllability=controllability,
            asil=candidate_asil
        )

        st.session_state["candidate_asil"] = candidate_asil
        st.session_state["asil_rationale"] = asil_rationale
        st.session_state["asil_severity"] = severity
        st.session_state["asil_exposure"] = exposure
        st.session_state["asil_controllability"] = controllability
        st.session_state["asil_input_tuple"] = (
            severity,
            exposure,
            controllability
        )
        st.session_state["asil_assessment_completed"] = True

        st.session_state.pop(
            "safety_goal_result",
            None
        )

        st.session_state.pop(
            "safety_goal_hara_key",
            None
        )

        st.session_state.pop(
            "fsr_results",
            None
        )

        st.session_state.pop(
            "tsr_results",
            None
        )

        st.session_state.pop(
            "tsr_fsr_id",
            None
        )

        st.session_state.pop(
            "traceability_rows",
            None
        )

        log_audit_event(
            event="Candidate ASIL calculated",
            details=(
                f"Severity={severity}, Exposure={exposure}, "
                f"Controllability={controllability}. "
                f"Candidate ASIL={candidate_asil}."
            ),
            asil=candidate_asil,
        )

    # =====================================================
    # DISPLAY ASIL
    # =====================================================

    asil_is_current = (
        st.session_state.get("asil_assessment_completed", False)
        and st.session_state.get("asil_input_tuple")
        == (
            severity,
            exposure,
            controllability
        )
        and st.session_state.get("active_hara_key")
        == current_hara_key
    )

    if asil_is_current:

        st.subheader(
            "🎯 Candidate ASIL Recommendation"
        )

        asil_col1, asil_col2 = st.columns(
            [1, 2]
        )

        with asil_col1:

            with st.container(border=True):

                st.caption(
                    "Candidate ASIL"
                )

                st.markdown(
                    f"# {st.session_state['candidate_asil']}"
                )

                st.caption(
                    f"{st.session_state['asil_severity']} · "
                    f"{st.session_state['asil_exposure']} · "
                    f"{st.session_state['asil_controllability']}"
                )

        with asil_col2:

            st.markdown(
                "#### Assessment"
            )

            st.write(
                f"**Severity:** "
                f"{st.session_state['asil_severity']}"
            )

            st.write(
                f"**Exposure:** "
                f"{st.session_state['asil_exposure']}"
            )

            st.write(
                f"**Controllability:** "
                f"{st.session_state['asil_controllability']}"
            )

            st.write(
                st.session_state["asil_rationale"]
            )

        st.caption(
            "Candidate ASIL is decision-support output only. "
            "Final classification must be reviewed and approved "
            "by an authorized functional-safety engineer."
        )

        # =================================================
        # 6. SAFETY GOAL
        # =================================================

        st.header(
            "6. Safety Goal"
        )

        st.write(
            "Safety Goal generation is unlocked only after "
            "the current HARA candidate and current S/E/C "
            "assessment have been completed."
        )

        with st.container(border=True):

            st.markdown(
                "### Safety Goal Traceability Context"
            )

            st.write(
                f"**Malfunction:** "
                f"{selected_candidate['malfunction']}"
            )

            st.write(
                f"**Hazard:** "
                f"{selected_candidate['hazard']}"
            )

            st.write(
                f"**Hazardous Event:** "
                f"{selected_candidate['hazardous_event']}"
            )

            st.write(
                f"**S/E/C:** "
                f"{severity} / {exposure} / {controllability}"
            )

            st.write(
                f"**Candidate ASIL:** "
                f"{st.session_state['candidate_asil']}"
            )

        if st.button(
            "🎯 Generate Safety Goal",
            type="primary"
        ):

            safety_goal_result = generate_safety_goal(
                system=system,
                function=function,
                hazard=selected_candidate["hazard"],
                hazardous_event=selected_candidate["hazardous_event"],
                candidate_asil=st.session_state[
                    "candidate_asil"
                ]
            )

            # Preserve the selected malfunction for downstream traceability.
            safety_goal_result["malfunction"] = (
                selected_candidate["malfunction"]
            )

            st.session_state[
                "safety_goal_result"
            ] = safety_goal_result

            st.session_state[
                "safety_goal_hara_key"
            ] = current_hara_key

            log_audit_event(
                event="Safety Goal generated",
                details=(
                    f"Safety Goal generated for malfunction="
                    f"{selected_candidate['malfunction']}, "
                    f"hazard={selected_candidate['hazard']}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=safety_goal_result.get("id", "SG-001"),
            )

        # =============================================
        # DISPLAY SAFETY GOAL ONLY AFTER GENERATION
        # =============================================

        safety_goal_is_current = (
            "safety_goal_result" in st.session_state
            and st.session_state.get("safety_goal_hara_key")
            == current_hara_key
            and st.session_state.get("asil_input_tuple")
            == (
                severity,
                exposure,
                controllability
            )
            and st.session_state.get(
                "asil_assessment_completed",
                False
            )
        )

        if safety_goal_is_current:

            result = st.session_state[
                "safety_goal_result"
            ]

            st.subheader(
                "🎯 Candidate Safety Goal"
            )

            with st.container(border=True):

                st.markdown(
                    "**Safety Goal**"
                )

                st.write(
                    result["safety_goal"]
                )

            st.write(
                f"**Candidate ASIL:** "
                f"{result['candidate_asil']}"
            )

            st.write(
                f"**S/E/C:** "
                f"{severity} / {exposure} / {controllability}"
            )

            st.write(
                f"**Hazard:** "
                f"{result['hazard']}"
            )

            st.write(
                f"**Hazardous Event:** "
                f"{result['hazardous_event']}"
            )

            st.info(
                get_safety_goal_review_note()
            )

    else:

        st.info(
            "Complete and calculate the current S/E/C assessment "
            "to unlock the ASIL result and Safety Goal section."
        )


# =========================================================
