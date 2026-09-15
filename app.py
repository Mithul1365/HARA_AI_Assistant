from pathlib import Path
import re
import hashlib
import pickle
import streamlit as st

from backend.llm_engine import analyze_with_qwen
from backend.document_processor import extract_text_from_pdf

from backend.asil_engine import (
    calculate_asil,
    get_asil_rationale
)

from backend.safety_goal_engine import (
    generate_safety_goal,
    get_safety_goal_review_note
)

from backend.fsr_engine import generate_fsr

from rag.chunker import create_chunks

from rag.vector_store import (
    create_vector_store,
    search_documents
)

from rag.knowledge_base_index import (
    build_and_save_knowledge_base_index,
    load_saved_knowledge_base_index
)


# =========================================================
# PAGE CONFIGURATION
# =========================================================

st.set_page_config(
    page_title="HARA AI Assistant",
    page_icon="🚗",
    layout="wide"
)


# =========================================================
# TITLE
# =========================================================

st.title("🚗 HARA AI Assistant")

st.caption(
    "Functional Safety HARA & Safety Requirement Management Assistant"
)

st.info(
    "Engineering Review Required: This system provides "
    "AI-assisted candidate analysis. Final functional-safety "
    "decisions must be reviewed and approved by a qualified "
    "functional-safety engineer."
)


# =========================================================
# LOAD KNOWLEDGE BASE
# =========================================================

if "knowledge_base_chunks" not in st.session_state:

    with st.spinner(
        "Loading automotive engineering knowledge base..."
    ):

        kb_chunks, kb_index = (
            load_saved_knowledge_base_index()
        )

    if kb_index is None:

        with st.spinner(
            "First-time setup: building knowledge base index..."
        ):

            kb_chunks, kb_index = (
                build_and_save_knowledge_base_index()
            )

    st.session_state[
        "knowledge_base_chunks"
    ] = kb_chunks

    st.session_state[
        "knowledge_base_index"
    ] = kb_index


kb_chunks = st.session_state.get(
    "knowledge_base_chunks",
    []
)

kb_index = st.session_state.get(
    "knowledge_base_index"
)


# =========================================================
# 1. ENGINEERING DOCUMENT
# =========================================================

st.header(
    "📄 1. Engineering Document"
)

st.write(
    "Upload an Item Definition, System Architecture, "
    "Operational Scenario, or existing HARA engineering document."
)

uploaded_file = st.file_uploader(
    "Upload Engineering PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    st.write(
        f"📎 **Selected:** {uploaded_file.name}"
    )

    if st.button(
        "📖 Read Document"
    ):

        with st.spinner(
            "Reading engineering PDF..."
        ):

            pages = extract_text_from_pdf(
                uploaded_file
            )

        if not pages:

            st.warning(
                "No readable text was found in this PDF."
            )

        else:

            st.session_state[
                "document_pages"
            ] = pages

            st.session_state[
                "document_name"
            ] = uploaded_file.name

            st.success(
                f"Document processed successfully. "
                f"{len(pages)} pages extracted."
            )

            chunks = create_chunks(
                pages
            )

            for chunk in chunks:

                chunk["source"] = (
                    uploaded_file.name
                )

                chunk["category"] = (
                    "uploaded_document"
                )

            st.session_state[
                "document_chunks"
            ] = chunks

            # -------------------------------------------------
            # PERSISTENT UPLOADED-PDF INDEX CACHE
            # -------------------------------------------------
            # The same PDF should not be embedded again on every
            # Streamlit rerun/session. The cache key is based on
            # the actual PDF bytes, so a changed PDF gets a new index.
            pdf_bytes = uploaded_file.getvalue()

            pdf_hash = hashlib.sha256(
                pdf_bytes
            ).hexdigest()[:16]

            cache_dir = (
                "data/uploaded_index_cache"
            )

            cache_path = (
                Path(cache_dir)
                / f"{pdf_hash}.pkl"
            )

            Path(cache_dir).mkdir(
                parents=True,
                exist_ok=True
            )

            if cache_path.exists():

                with st.spinner(
                    "Loading cached document search index..."
                ):

                    with open(
                        cache_path,
                        "rb"
                    ) as cache_file:

                        cached_data = pickle.load(
                            cache_file
                        )

                    vector_index = cached_data[
                        "index"
                    ]

                st.success(
                    "Cached document search index loaded. "
                    "No embedding rebuild was required."
                )

            else:

                with st.spinner(
                    "First time for this PDF: creating document search index..."
                ):

                    vector_index = create_vector_store(
                        chunks
                    )

                    if vector_index is None:

                        st.error(
                            "Could not create the document search index."
                        )

                    else:

                        with open(
                            cache_path,
                            "wb"
                        ) as cache_file:

                            pickle.dump(
                                {
                                    "index": vector_index,
                                    "document_name": uploaded_file.name,
                                    "pdf_hash": pdf_hash
                                },
                                cache_file
                            )

                if vector_index is not None:

                    st.success(
                        "Search index created and cached. "
                        "Future runs with this PDF will be faster."
                    )

            st.session_state[
                "vector_index"
            ] = vector_index

            st.session_state[
                "document_pdf_hash"
            ] = pdf_hash


# =========================================================
# EXTRACTED ENGINEERING INFORMATION
# =========================================================

if "document_pages" in st.session_state:

    st.header(
        "📑 Extracted Engineering Information"
    )

    pages = st.session_state[
        "document_pages"
    ]

    for page in pages:

        with st.expander(
            f"Page {page['page']}"
        ):

            st.text(
                page["text"]
            )


# =========================================================
# 2. SEARCH UPLOADED DOCUMENT
# =========================================================

if "vector_index" in st.session_state:

    st.header(
        "🔎 2. Search Uploaded Engineering Document"
    )

    search_query = st.text_input(
        "Enter your question",
        placeholder=(
            "Example: What happens if steering assistance is lost?"
        )
    )

    if st.button(
        "🔍 Search Document"
    ):

        if not search_query.strip():

            st.warning(
                "Please enter a question before searching."
            )

        else:

            with st.spinner(
                "Searching engineering document..."
            ):

                results = search_documents(
                    query=search_query,
                    chunks=st.session_state[
                        "document_chunks"
                    ],
                    index=st.session_state[
                        "vector_index"
                    ],
                    top_k=3
                )

            if not results:

                st.warning(
                    "No sufficiently relevant information was found "
                    "in the uploaded engineering document."
                )

            else:

                st.success(
                    f"{len(results)} relevant sections found."
                )

                for i, result in enumerate(
                    results,
                    start=1
                ):

                    st.subheader(
                        f"Evidence {i} — Page {result['page']}"
                    )

                    st.write(
                        result["text"]
                    )

                    st.caption(
                        f"Source: "
                        f"{result.get('source', 'Uploaded Document')} | "
                        f"Relevance: {result['score']:.4f}"
                    )

                    st.divider()


# =========================================================
# 3. ITEM DEFINITION
# =========================================================

st.header(
    "3. Item Definition"
)

st.write(
    "Define the automotive item, its intended function, "
    "and the operational situation for HARA analysis."
)

col1, col2 = st.columns(2)


with col1:

    system = st.text_input(
        "System / Item",
        placeholder=(
            "Example: EPS (Electric Power Steering)"
        )
    )

    function = st.text_area(
        "Intended Function",
        placeholder=(
            "Example: Provide steering assistance to the driver"
        ),
        height=120
    )


with col2:

    scenario = st.text_area(
        "Operational Scenario",
        placeholder=(
            "Example: Highway driving at 100 km/h"
        ),
        height=120
    )

    operating_conditions = st.text_area(
        "Operating Conditions (Optional)",
        placeholder=(
            "Example: Dry road, daylight, normal traffic"
        ),
        height=120
    )


st.caption(
    "Provide enough operational context so the AI can identify "
    "relevant hazards and hazardous events."
)


# =========================================================
# 4. HARA ANALYSIS
# =========================================================

st.header(
    "4. HARA Analysis"
)

analysis_mode = st.radio(
    "Analysis Mode",
    [
        "🔬 Detailed Analysis",
        "⚡ Quick Summary"
    ],
    horizontal=True
)

summary_mode = (
    analysis_mode == "⚡ Quick Summary"
)


if st.button(
    "🔍 Analyze HARA",
    type="primary"
):

    if not system.strip():

        st.warning(
            "Please enter a System / Item."
        )

    elif not function.strip():

        st.warning(
            "Please enter an Intended Function."
        )

    elif not scenario.strip():

        st.warning(
            "Please enter an Operational Scenario."
        )

    elif not kb_chunks:

        st.warning(
            "Engineering knowledge base is empty."
        )

    else:

        query = f"""
System / Item:
{system}

Function:
{function}

Operational Scenario:
{scenario}

Operating Conditions:
{operating_conditions}

Identify relevant engineering evidence for this
automotive function, its malfunctions, hazards and
hazardous events.
"""

        uploaded_document_available = (
            "document_chunks" in st.session_state
            and "vector_index" in st.session_state
            and st.session_state[
                "vector_index"
            ] is not None
        )

        evidence_results = []

        evidence_source = ""

        # -------------------------------------------------
        # PRIMARY SOURCE: UPLOADED DOCUMENT
        # -------------------------------------------------

        if uploaded_document_available:

            with st.spinner(
                "Retrieving evidence from uploaded engineering document..."
            ):

                evidence_results = search_documents(
                    query=query,
                    chunks=st.session_state[
                        "document_chunks"
                    ],
                    index=st.session_state[
                        "vector_index"
                    ],
                    top_k=5
                )

            evidence_source = (
                f"Uploaded Engineering Document: "
                f"{st.session_state.get('document_name', 'PDF')}"
            )

        # -------------------------------------------------
        # FALLBACK: KNOWLEDGE BASE
        # -------------------------------------------------

        if not evidence_results:

            with st.spinner(
                "Checking engineering knowledge base..."
            ):

                evidence_results = search_documents(
                    query=query,
                    chunks=kb_chunks,
                    index=kb_index,
                    top_k=5
                )

            evidence_source = (
                "Automotive Engineering Knowledge Base"
            )

        # -------------------------------------------------
        # NO EVIDENCE
        # -------------------------------------------------

        if not evidence_results:

            st.warning(
                "No sufficiently relevant engineering evidence "
                "was found. AI analysis was not generated."
            )

        else:

            evidence = []

            for result in evidence_results:

                evidence.append(
                    {
                        "source": result.get(
                            "source",
                            "Engineering Document"
                        ),
                        "page": result["page"],
                        "text": result["text"]
                    }
                )

            # -------------------------------------------------
            # ENGINEERING EVIDENCE
            # -------------------------------------------------

            with st.expander(
                "📚 Engineering Evidence Used by AI",
                expanded=True
            ):

                st.caption(
                    f"Source: {evidence_source}"
                )

                for i, result in enumerate(
                    evidence_results,
                    start=1
                ):

                    st.markdown(
                        f"**Evidence {i}**"
                    )

                    st.caption(
                        f"{result.get('source', 'Engineering Document')} "
                        f"· Page {result['page']} "
                        f"· Relevance {result['score']:.4f}"
                    )

                    st.write(
                        result["text"]
                    )

                    st.divider()

            # -------------------------------------------------
            # QWEN3 ANALYSIS
            # -------------------------------------------------

            with st.spinner(
                "Qwen3 is analyzing the engineering evidence..."
            ):

                answer = analyze_with_qwen(
                    system=system,
                    function=function,
                    scenario=scenario,
                    evidence=evidence,
                    summary_mode=summary_mode
                )

            # -------------------------------------------------
            # SAVE HARA RESULT
            # -------------------------------------------------

            st.session_state[
                "hara_answer"
            ] = answer

            st.session_state[
                "hara_evidence"
            ] = evidence_results

            st.session_state[
                "hara_system"
            ] = system

            st.session_state[
                "hara_function"
            ] = function

            st.session_state[
                "hara_scenario"
            ] = scenario

            # Clear old downstream results
            st.session_state.pop(
                "candidate_asil",
                None
            )

            st.session_state.pop(
                "asil_assessment_completed",
                None
            )

            st.session_state.pop(
                "safety_goal_result",
                None
            )

            st.session_state.pop(
                "fsr_results",
                None
            )

            st.session_state.pop(
                "safety_goal_hara_key",
                None
            )


# =========================================================
# DISPLAY HARA RESULT
# =========================================================

if "hara_answer" in st.session_state:

    st.success(
        "HARA analysis generated using retrieved engineering evidence."
    )

    if summary_mode:

        st.subheader(
            "⚡ HARA Quick Summary"
        )

    else:

        st.subheader(
            "🤖 AI-Assisted HARA Result"
        )

    st.write(
        st.session_state["hara_answer"]
    )

    st.info(
        "Engineering Review: This is an AI-assisted candidate analysis. "
        "Final functional-safety decisions require review and approval "
        "by a qualified functional-safety engineer."
    )


# =========================================================
# DOWNSTREAM RESULT VALIDATION
# =========================================================

def clear_downstream_results():
    """Clear results that depend on the current HARA/S/E/C inputs."""
    st.session_state.pop("candidate_asil", None)
    st.session_state.pop("asil_assessment_completed", None)
    st.session_state.pop("asil_rationale", None)
    st.session_state.pop("asil_severity", None)
    st.session_state.pop("asil_exposure", None)
    st.session_state.pop("asil_controllability", None)
    st.session_state.pop("asil_input_tuple", None)
    st.session_state.pop("asil_assessment_completed", None)
    st.session_state.pop("safety_goal_result", None)
    st.session_state.pop("safety_goal_hara_key", None)
    st.session_state.pop("fsr_results", None)


# =========================================================
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

    candidates = []

    if not hara_text:
        return candidates

    hara_text = str(hara_text)

    lines = [
        line.strip()
        for line in hara_text.splitlines()
        if line.strip()
    ]

    current_malfunction = ""
    current_hazard = ""

    for line in lines:

        clean_line = line.strip()

        clean_line = re.sub(
            r"^[\-\*\d\.\)\s]+",
            "",
            clean_line
        )

        clean_line = clean_line.replace("**", "")
        clean_line = clean_line.replace("__", "")

        lower_line = clean_line.lower()

        if re.match(
            r"^malfunction\s*:",
            lower_line
        ):

            current_malfunction = re.split(
                r":",
                clean_line,
                maxsplit=1
            )[1].strip()

            continue

        if re.match(
            r"^hazard\s*:",
            lower_line
        ):

            current_hazard = re.split(
                r":",
                clean_line,
                maxsplit=1
            )[1].strip()

            continue

        if re.match(
            r"^hazardous\s+event\s*:",
            lower_line
        ):

            hazardous_event = re.split(
                r":",
                clean_line,
                maxsplit=1
            )[1].strip()

            if current_hazard:

                candidates.append(
                    {
                        "malfunction": (
                            current_malfunction
                            if current_malfunction
                            else "Identified malfunction"
                        ),
                        "hazard": current_hazard,
                        "hazardous_event": hazardous_event
                    }
                )

            current_malfunction = ""
            current_hazard = ""

    # Arrow format: Malfunction → Hazard → Hazardous Event
    if not candidates:

        for line in lines:

            if "→" in line:

                parts = [
                    part.strip()
                    for part in line.split("→")
                    if part.strip()
                ]

                if len(parts) >= 3:

                    candidates.append(
                        {
                            "malfunction": parts[0],
                            "hazard": parts[1],
                            "hazardous_event": parts[2]
                        }
                    )

    # ASCII arrow format
    if not candidates:

        for line in lines:

            if "->" in line:

                parts = [
                    part.strip()
                    for part in line.split("->")
                    if part.strip()
                ]

                if len(parts) >= 3:

                    candidates.append(
                        {
                            "malfunction": parts[0],
                            "hazard": parts[1],
                            "hazardous_event": parts[2]
                        }
                    )

    unique_candidates = []
    seen = set()

    for candidate in candidates:

        key = (
            candidate["malfunction"].lower(),
            candidate["hazard"].lower(),
            candidate["hazardous_event"].lower()
        )

        if key not in seen:

            seen.add(key)
            unique_candidates.append(candidate)

    return unique_candidates


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
        "Candidates are prioritized using transparent keyword-based "
        "risk indicators. This ranking is decision-support only; "
        "the engineer must select the HARA candidate for assessment."
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
            f"{candidate['hazard']}"
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
# 7. FUNCTIONAL SAFETY REQUIREMENTS (FSR)
# =========================================================

st.header(
    "7. Functional Safety Requirements (FSR)"
)

st.write(
    "Generate candidate Functional Safety Requirements "
    "automatically from the selected Safety Goal, HARA "
    "information and Candidate ASIL."
)

fsr_context_ready = (
    "safety_goal_result" in st.session_state
    and st.session_state.get("asil_assessment_completed", False)
    and st.session_state.get("safety_goal_hara_key")
    == st.session_state.get("active_hara_key")
)

if not fsr_context_ready:

    st.warning(
        "Complete S/E/C → Candidate ASIL → Safety Goal first. "
        "FSRs will then be available."
    )

else:

    safety_goal_data = st.session_state[
        "safety_goal_result"
    ]

    if (
        "candidate_asil" not in st.session_state
        or "asil_severity" not in st.session_state
        or "asil_exposure" not in st.session_state
        or "asil_controllability" not in st.session_state
    ):

        st.warning(
            "Complete the S/E/C assessment and Candidate ASIL "
            "calculation before generating FSRs."
        )

    else:

        with st.container(border=True):

            st.markdown(
                "### FSR Traceability Context"
            )

            st.write(
                f"**Safety Goal:** "
                f"{safety_goal_data['safety_goal']}"
            )

            st.write(
                f"**Candidate ASIL:** "
                f"{safety_goal_data['candidate_asil']}"
            )

            st.write(
                f"**S/E/C:** "
                f"{st.session_state['asil_severity']} / "
                f"{st.session_state['asil_exposure']} / "
                f"{st.session_state['asil_controllability']}"
            )

            st.write(
                f"**Hazard:** "
                f"{safety_goal_data['hazard']}"
            )

            st.write(
                f"**Hazardous Event:** "
                f"{safety_goal_data['hazardous_event']}"
            )

        if st.button(
            "🛡️ Generate Functional Safety Requirements",
            type="primary"
        ):

            with st.spinner(
                "Generating candidate Functional Safety Requirements..."
            ):

                fsr_results = generate_fsr(
                    system=safety_goal_data["system"],
                    function=safety_goal_data["function"],
                    malfunction=safety_goal_data.get(
                        "malfunction",
                        "Identified malfunction"
                    ),
                    hazard=safety_goal_data["hazard"],
                    hazardous_event=safety_goal_data[
                        "hazardous_event"
                    ],
                    safety_goal=safety_goal_data[
                        "safety_goal"
                    ],
                    candidate_asil=safety_goal_data[
                        "candidate_asil"
                    ]
                )

            st.session_state[
                "fsr_results"
            ] = fsr_results

        if "fsr_results" in st.session_state:

            fsr_results = st.session_state[
                "fsr_results"
            ]

            st.success(
                f"{len(fsr_results)} candidate Functional "
                "Safety Requirement(s) generated."
            )

            for fsr in fsr_results:

                with st.container(border=True):

                    st.markdown(
                        f"### {fsr['id']}"
                    )

                    st.write(
                        f"**Requirement:** "
                        f"{fsr['requirement']}"
                    )

                    st.write(
                        f"**Rationale:** "
                        f"{fsr['rationale']}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:

                        st.write(
                            f"**ASIL:** "
                            f"{fsr['candidate_asil']}"
                        )

                    with col2:

                        st.write(
                            "**Review Status:** "
                            f"{fsr['review_status']}"
                        )

                    with col3:

                        st.write(
                            f"**Source Hazard:** "
                            f"{fsr['hazard']}"
                        )

                    with st.expander(
                        "🔗 Traceability Details"
                    ):

                        st.write(
                            f"**System:** "
                            f"{fsr['system']}"
                        )

                        st.write(
                            f"**Function:** "
                            f"{fsr['function']}"
                        )

                        st.write(
                            f"**Malfunction:** "
                            f"{fsr['malfunction']}"
                        )

                        st.write(
                            f"**Hazardous Event:** "
                            f"{fsr['hazardous_event']}"
                        )

                        st.write(
                            f"**Linked Safety Goal:** "
                            f"{fsr['safety_goal']}"
                        )

            st.info(
                "These FSRs are AI-assisted candidate drafts. "
                "They must be reviewed, refined and approved "
                "by an authorized functional-safety engineer "
                "before being used as official safety requirements."
            )


# =========================================================
# 8. HARA WORKFLOW
# =========================================================

st.header(
    "7. HARA Workflow"
)

st.markdown(
    """
    **Engineering Document**
    →
    **Document Extraction**
    →
    **Chunking**
    →
    **Semantic Embeddings**
    →
    **Domain-Aware Retrieval**
    →
    **Evidence Validation**
    →
    **Local Qwen3 Analysis**
    →
    **Malfunction Identification**
    →
    **Hazard Identification**
    →
    **Hazardous Event**
    →
    **S/E/C Assessment**
    →
    **Candidate ASIL**
    →
    **Safety Goal**
    →
    **FSR**
    →
    **TSR**
    →
    **Traceability**
    """
)