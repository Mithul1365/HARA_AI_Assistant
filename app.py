import re
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

            with st.spinner(
                "Creating uploaded document search index..."
            ):

                vector_index = create_vector_store(
                    chunks
                )

            st.session_state[
                "vector_index"
            ] = vector_index

            st.success(
                "Search index ready. Uploaded document "
                "can now be used for HARA analysis."
            )


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
                "safety_goal_result",
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
# 5. S / E / C ASSESSMENT
# =========================================================

st.header(
    "5. S / E / C Assessment"
)

st.write(
    "Assess Severity, Exposure and Controllability "
    "for the selected hazardous event."
)

col1, col2, col3 = st.columns(3)


with col1:

    severity = st.selectbox(
        "Severity (S)",
        [
            "S0",
            "S1",
            "S2",
            "S3"
        ]
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
        ]
    )


with col3:

    controllability = st.selectbox(
        "Controllability (C)",
        [
            "C0",
            "C1",
            "C2",
            "C3"
        ]
    )


st.caption(
    "S/E/C values are engineering inputs. "
    "Candidate ASIL requires functional-safety engineer review."
)


# =========================================================
# CALCULATE ASIL
# =========================================================

if st.button(
    "🧮 Calculate Candidate ASIL"
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

    st.session_state[
        "candidate_asil"
    ] = candidate_asil

    st.session_state[
        "asil_rationale"
    ] = asil_rationale

    st.session_state[
        "asil_severity"
    ] = severity

    st.session_state[
        "asil_exposure"
    ] = exposure

    st.session_state[
        "asil_controllability"
    ] = controllability

    # Clear old Safety Goal
    st.session_state.pop(
        "safety_goal_result",
        None
    )


# =========================================================
# DISPLAY ASIL
# =========================================================

if "candidate_asil" in st.session_state:

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


# =========================================================
# HARA RESULT PARSER
# =========================================================

def extract_hara_candidates(hara_text):

    candidates = []

    if not hara_text:
        return candidates

    # Convert to string in case the model returns another type
    hara_text = str(hara_text)

    lines = [
        line.strip()
        for line in hara_text.splitlines()
        if line.strip()
    ]

    # =====================================================
    # METHOD 1
    # Explicit Hazard / Hazardous Event labels
    # =====================================================

    current_malfunction = ""
    current_hazard = ""

    for line in lines:

        clean_line = line.strip()

        # Remove markdown symbols
        clean_line = re.sub(
            r"^[\-\*\d\.\)\s]+",
            "",
            clean_line
        )

        clean_line = clean_line.replace(
            "**",
            ""
        )

        clean_line = clean_line.replace(
            "__",
            ""
        )

        lower_line = clean_line.lower()

        # -------------------------------------------------
        # MALFUNCTION
        # -------------------------------------------------

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

        # -------------------------------------------------
        # HAZARD
        # -------------------------------------------------

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

        # -------------------------------------------------
        # HAZARDOUS EVENT
        # -------------------------------------------------

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

    # =====================================================
    # METHOD 2
    # Arrow format
    #
    # Malfunction → Hazard → Hazardous Event
    # =====================================================

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

    # =====================================================
    # METHOD 3
    # ASCII arrow format
    #
    # Malfunction -> Hazard -> Hazardous Event
    # =====================================================

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

    # =====================================================
    # REMOVE DUPLICATES
    # =====================================================

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

            unique_candidates.append(
                candidate
            )

    return unique_candidates


# =========================================================
# 6. SAFETY GOAL
# =========================================================

st.header(
    "6. Safety Goal"
)

st.write(
    "Generate a candidate Safety Goal automatically "
    "from the HARA result and Candidate ASIL."
)


# =========================================================
# GET HARA CANDIDATES
# =========================================================

hara_candidates = []

if "hara_answer" in st.session_state:

    hara_candidates = extract_hara_candidates(
        st.session_state["hara_answer"]
    )


# =========================================================
# DISPLAY AUTOMATIC HARA DATA
# =========================================================

if hara_candidates:

    st.success(
        f"{len(hara_candidates)} HARA candidate(s) "
        "detected automatically."
    )

    candidate_labels = []

    for candidate in hara_candidates:

        candidate_labels.append(
            f"{candidate['malfunction']} → "
            f"{candidate['hazard']}"
        )

    selected_index = st.selectbox(
        "Select HARA Candidate",
        range(len(candidate_labels)),
        format_func=lambda i: candidate_labels[i]
    )

    selected_candidate = hara_candidates[
        selected_index
    ]

    hazard_input = selected_candidate[
        "hazard"
    ]

    hazardous_event_input = selected_candidate[
        "hazardous_event"
    ]

    with st.container(border=True):

        st.markdown(
            "### Automatically Selected HARA Data"
        )

        st.write(
            f"**Malfunction:** "
            f"{selected_candidate['malfunction']}"
        )

        st.write(
            f"**Hazard:** "
            f"{hazard_input}"
        )

        st.write(
            f"**Hazardous Event:** "
            f"{hazardous_event_input}"
        )


else:

    hazard_input = ""
    hazardous_event_input = ""

    if "hara_answer" not in st.session_state:

        st.warning(
            "Run HARA Analysis first. "
            "Hazard and Hazardous Event will then be "
            "taken automatically from the HARA result."
        )

    else:

        st.warning(
            "The HARA result could not be converted into "
            "structured Hazard/Hazardous Event data."
        )

        with st.expander(
            "View HARA output used for extraction"
        ):

            st.write(
                st.session_state["hara_answer"]
            )


# =========================================================
# GENERATE SAFETY GOAL
# =========================================================

if st.button(
    "🎯 Generate Safety Goal",
    type="primary"
):

    if not hara_candidates:

        st.warning(
            "Please run HARA Analysis first."
        )

    elif "candidate_asil" not in st.session_state:

        st.warning(
            "Please calculate the Candidate ASIL first."
        )

    else:

        safety_goal_result = generate_safety_goal(
            system=system,
            function=function,
            hazard=hazard_input,
            hazardous_event=hazardous_event_input,
            candidate_asil=st.session_state[
                "candidate_asil"
            ]
        )

        st.session_state[
            "safety_goal_result"
        ] = safety_goal_result


# =========================================================
# DISPLAY SAFETY GOAL
# =========================================================

if "safety_goal_result" in st.session_state:

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


# =========================================================
# 7. HARA WORKFLOW
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
    **FSR/TSR**
    →
    **Traceability**
    """
)