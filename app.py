from pathlib import Path
import re
import hashlib
import pickle
import json
import streamlit as st
from io import BytesIO
from backend.llm_engine import analyze_with_qwen
def extract_text_from_pdf(*args, **kwargs):
    from backend.document_processor import extract_text_from_pdf as _extract
    return _extract(*args, **kwargs)

from backend.asil_engine import (
    calculate_asil,
    get_asil_rationale
)

from backend.safety_goal_engine import (
    generate_safety_goal,
    get_safety_goal_review_note
)

from backend.fsr_engine import generate_fsr
from backend.requirement_quality_engine import (
    check_requirements_quality,
    get_requirement_quality_review_note
)
from backend.tsr_engine import generate_tsr, get_tsr_review_note

from backend.traceability_engine import (
    build_traceability_matrix,
    get_traceability_review_note
)

from backend.verification_engine import (
    load_verification_records,
    save_verification_record,
    clear_verification_records,
    get_verification_note,
)

from backend.review_engine import (
    load_review_decisions,
    save_review_decision,
    clear_review_decisions,
    get_latest_review_decision,
    get_review_status,
    get_review_note,
)

from backend.audit_engine import (
    record_audit_event,
    load_audit_history,
    clear_audit_history,
    get_audit_review_note
)

from rag.chunker import create_chunks

# Heavy RAG modules are imported lazily so Streamlit can render the UI
# without loading SentenceTransformer / PyTorch / FAISS at startup.

def create_vector_store(*args, **kwargs):
    from rag.vector_store import create_vector_store as _create_vector_store
    return _create_vector_store(*args, **kwargs)


def search_documents(*args, **kwargs):
    from rag.vector_store import search_documents as _search_documents
    return _search_documents(*args, **kwargs)


def load_saved_knowledge_base_index():
    from rag.knowledge_base_index import load_saved_knowledge_base_index as _load
    return _load()


def build_and_save_knowledge_base_index():
    from rag.knowledge_base_index import build_and_save_knowledge_base_index as _build
    return _build()


@st.cache_resource(show_spinner=False)
def get_knowledge_base():
    """
    Load the persistent automotive KB only when HARA actually needs it.
    Streamlit keeps the loaded resource cached for the running app.
    """
    chunks, index = load_saved_knowledge_base_index()

    if index is None:
        chunks, index = build_and_save_knowledge_base_index()

    return chunks, index

AUDIT_HISTORY_PATH = Path("output") / "audit_history.json"
REVIEW_DECISIONS_PATH = Path("output") / "review_decisions.json"
VERIFICATION_RECORDS_PATH = Path("output") / "verification_records.json"


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
# IMPORTANT:
# Do NOT load SentenceTransformer / FAISS / the automotive KB here.
# The old version loaded these resources before the UI was rendered,
# which increased Streamlit startup time.
#
# The KB is now loaded lazily inside HARA Analysis only when required.

kb_chunks = []
kb_index = None

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
        # The heavy KB is loaded only if the uploaded document
        # did not provide usable evidence.

        if not evidence_results:

            with st.spinner(
                "Loading automotive engineering knowledge base..."
            ):

                kb_chunks, kb_index = get_knowledge_base()

            if kb_index is not None and kb_chunks:

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
                "AI is analyzing the engineering evidence..."
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

    # Render the HARA result as readable scenario blocks instead of
    # one long paragraph. This does not change the generated content.
    answer_text = st.session_state["hara_answer"]

    def render_hara_scenarios(answer, quick=False):
        """Render Quick/Detailed HARA output in structured Markdown."""

        import re

        # Split only at Scenario N headings.
        parts = re.split(r"(?=Scenario\s+\d+\s*:?)", answer.strip())

        for part in parts:
            part = part.strip()
            if not part:
                continue

            lines = [line.strip() for line in part.splitlines() if line.strip()]
            if not lines:
                continue

            # Extract scenario number.
            match = re.match(r"Scenario\s+(\d+)\s*:?", lines[0], re.IGNORECASE)
            if not match:
                continue

            scenario_no = match.group(1)

            fields = {}

            for line in lines[1:]:
                if ":" not in line:
                    continue

                key, value = line.split(":", 1)
                key = key.strip().lower()
                value = value.strip()

                if key in {
                    "malfunction",
                    "potential malfunction",
                    "hazard",
                    "potential hazard",
                    "hazardous event",
                    "event",
                    "rationale",
                    "engineering evidence",
                    "evidence",
                }:
                    fields[key] = value

            if quick:
                malfunction = fields.get(
                    "malfunction",
                    fields.get("potential malfunction", "")
                )
                hazard = fields.get(
                    "hazard",
                    fields.get("potential hazard", "")
                )
                event = fields.get(
                    "hazardous event",
                    fields.get("event", "")
                )

                st.markdown(f"### Scenario {scenario_no}")
                st.markdown(f"- **Malfunction:** {malfunction}")
                st.markdown(f"- **Hazard:** {hazard}")
                st.markdown(f"- **Hazardous Event:** {event}")

            else:
                malfunction = fields.get(
                    "potential malfunction",
                    fields.get("malfunction", "")
                )
                hazard = fields.get(
                    "potential hazard",
                    fields.get("hazard", "")
                )
                event = fields.get(
                    "hazardous event",
                    fields.get("event", "")
                )
                rationale = fields.get("rationale", "")
                evidence_value = fields.get(
                    "engineering evidence",
                    fields.get("evidence", "")
                )

                st.markdown(f"### Scenario {scenario_no}")
                st.markdown(f"- **Potential Malfunction:** {malfunction}")
                st.markdown(f"- **Potential Hazard:** {hazard}")
                st.markdown(f"- **Hazardous Event:** {event}")
                st.markdown(f"- **Rationale:** {rationale}")
                st.markdown(f"- **Engineering Evidence:** {evidence_value}")

            st.divider()

    render_hara_scenarios(
        answer_text,
        quick=summary_mode
    )

    st.info(
        "Engineering Review: This is an AI-assisted candidate analysis. "
        "Final functional-safety decisions require review and approval "
        "by a qualified functional-safety engineer."
    )


# =========================================================
# DOWNSTREAM RESULT VALIDATION
# =========================================================

def log_audit_event(
    event,
    details,
    hara_id="HARA-001",
    asil=None,
    safety_goal_id=None,
    fsr_id=None,
    tsr_ids=None,
):
    """Record an engineering action in the local audit history."""
    try:
        record_audit_event(
            history_path=AUDIT_HISTORY_PATH,
            event=event,
            details=details,
            hara_id=hara_id,
            asil=asil,
            safety_goal_id=safety_goal_id,
            fsr_id=fsr_id,
            tsr_ids=tsr_ids,
        )
    except OSError:
        # Audit logging must not prevent the engineering workflow from running.
        pass


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
    st.session_state.pop("tsr_results", None)
    st.session_state.pop("tsr_fsr_id", None)
    st.session_state.pop("traceability_rows", None)


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

            log_audit_event(
                event="Functional Safety Requirements generated",
                details=(
                    f"{len(fsr_results)} candidate FSR(s) generated "
                    f"from Safety Goal {safety_goal_data.get('id', 'SG-001')}."
                ),
                asil=safety_goal_data.get("candidate_asil"),
                safety_goal_id=safety_goal_data.get("id", "SG-001"),
            )

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
# 8. TECHNICAL SAFETY REQUIREMENTS (TSR)
# =========================================================

st.header(
    "8. Technical Safety Requirements (TSR)"
)

st.write(
    "Generate candidate Technical Safety Requirements from the "
    "selected Functional Safety Requirement."
)

tsr_context_ready = (
    "safety_goal_result" in st.session_state
    and st.session_state.get("asil_assessment_completed", False)
    and st.session_state.get("safety_goal_hara_key")
    == st.session_state.get("active_hara_key")
    and "fsr_results" in st.session_state
    and bool(st.session_state.get("fsr_results"))
)

if not tsr_context_ready:
    st.warning(
        "Complete S/E/C → Candidate ASIL → Safety Goal → FSR first. "
        "TSRs will then be available."
    )
else:
    safety_goal_data = st.session_state["safety_goal_result"]
    fsr_results = st.session_state["fsr_results"]

    st.markdown("### Select FSR for Technical Decomposition")

    fsr_labels = [
        f"{fsr['id']} — {fsr['requirement']}"
        for fsr in fsr_results
    ]

    selected_fsr_label = st.selectbox(
        "Select Functional Safety Requirement",
        ["-- Select an FSR --"] + fsr_labels,
        index=0,
        key="tsr_fsr_selection"
    )

    if selected_fsr_label == "-- Select an FSR --":
        st.info(
            "Select an FSR to generate its candidate technical requirements."
        )
    else:
        selected_fsr_position = fsr_labels.index(selected_fsr_label)
        selected_fsr = fsr_results[selected_fsr_position]

        with st.container(border=True):
            st.markdown("### Selected FSR")
            st.write(
                f"**{selected_fsr['id']}:** "
                f"{selected_fsr['requirement']}"
            )
            st.write(
                f"**Candidate ASIL:** {selected_fsr['candidate_asil']}"
            )
            st.write(
                f"**Linked Safety Goal:** "
                f"{selected_fsr['safety_goal']}"
            )

        if st.button(
            "⚙️ Generate Technical Safety Requirements",
            type="primary",
            key="generate_tsr_button"
        ):
            with st.spinner(
                "Generating candidate Technical Safety Requirements..."
            ):
                tsr_results = generate_tsr(
                    system=selected_fsr["system"],
                    function=selected_fsr["function"],
                    malfunction=selected_fsr["malfunction"],
                    hazard=selected_fsr["hazard"],
                    hazardous_event=selected_fsr["hazardous_event"],
                    safety_goal=selected_fsr["safety_goal"],
                    fsr=selected_fsr["requirement"],
                    candidate_asil=selected_fsr["candidate_asil"]
                )

            st.session_state["tsr_results"] = tsr_results
            st.session_state["tsr_fsr_id"] = selected_fsr["id"]

            log_audit_event(
                event="Technical Safety Requirements generated",
                details=(
                    f"{len(tsr_results)} candidate TSR(s) generated "
                    f"from selected {selected_fsr['id']}."
                ),
                asil=selected_fsr.get("candidate_asil"),
                safety_goal_id=safety_goal_data.get("id", "SG-001"),
                fsr_id=selected_fsr.get("id"),
                tsr_ids=[
                    tsr.get("id", "")
                    for tsr in tsr_results
                ],
            )

        tsr_is_current = (
            "tsr_results" in st.session_state
            and st.session_state.get("tsr_fsr_id")
            == selected_fsr["id"]
        )

        if tsr_is_current:
            tsr_results = st.session_state["tsr_results"]

            st.success(
                f"{len(tsr_results)} candidate Technical Safety "
                "Requirement(s) generated."
            )

            for tsr in tsr_results:
                with st.container(border=True):
                    st.markdown(f"### {tsr['id']}")

                    st.write(
                        f"**Technical Requirement:** "
                        f"{tsr['requirement']}"
                    )

                    st.write(
                        f"**Rationale:** {tsr['rationale']}"
                    )

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(
                            f"**ASIL:** {tsr['candidate_asil']}"
                        )

                    with col2:
                        st.write(
                            f"**Review Status:** "
                            f"{tsr['review_status']}"
                        )

                    with col3:
                        st.write(
                            f"**Linked FSR:** {selected_fsr['id']}"
                        )

                    with st.expander("🔗 Traceability Details"):
                        st.write(
                            f"**System:** {tsr['system']}"
                        )
                        st.write(
                            f"**Function:** {tsr['function']}"
                        )
                        st.write(
                            f"**Malfunction:** {tsr['malfunction']}"
                        )
                        st.write(
                            f"**Hazard:** {tsr['hazard']}"
                        )
                        st.write(
                            f"**Hazardous Event:** "
                            f"{tsr['hazardous_event']}"
                        )
                        st.write(
                            f"**Safety Goal:** {tsr['safety_goal']}"
                        )
                        st.write(
                            f"**FSR:** {tsr['fsr']}"
                        )

            st.info(get_tsr_review_note())


# =========================================================
# 9. REQUIREMENT QUALITY CHECKS
# =========================================================

st.header(
    "9. Requirement Quality Checks"
)

st.write(
    "Deterministic checks for candidate Functional Safety Requirements "
    "and Technical Safety Requirements."
)

quality_fsr_results = st.session_state.get("fsr_results", [])
quality_tsr_results = st.session_state.get("tsr_results", [])
quality_tsr_fsr_id = st.session_state.get("tsr_fsr_id")

quality_tsr_results = (
    quality_tsr_results
    if quality_tsr_fsr_id is not None
    else []
)

quality_context_ready = bool(quality_fsr_results) or bool(quality_tsr_results)

if not quality_context_ready:

    st.caption(
        "Requirement quality checks will be available after candidate "
        "FSR or TSR requirements are generated."
    )

else:

    quality_scope = st.radio(
        "Requirement set",
        ["Selected FSR", "Generated TSRs"],
        horizontal=True,
        key="requirement_quality_scope"
    )

    if quality_scope == "Selected FSR":

        selected_quality_fsr_id = st.session_state.get("tsr_fsr_id")
        selected_quality_fsr = next(
            (
                fsr for fsr in quality_fsr_results
                if fsr.get("id") == selected_quality_fsr_id
            ),
            None
        )

        if selected_quality_fsr is None:
            selected_quality_fsr = quality_fsr_results[0]

        quality_requirements = [selected_quality_fsr]
        st.caption(
            f"Checking selected FSR: {selected_quality_fsr.get('id', 'FSR-001')}"
        )

    else:

        quality_requirements = quality_tsr_results

        if not quality_requirements:
            st.caption(
                "Generate TSRs first to run quality checks on the technical requirements."
            )

    if quality_requirements:

        quality_results = check_requirements_quality(quality_requirements)

        total_pass = sum(item["passed"] for item in quality_results)
        total_review = sum(item["review"] for item in quality_results)
        total_fail = sum(item["failed"] for item in quality_results)

        qcol1, qcol2, qcol3, qcol4 = st.columns(4)

        with qcol1:
            st.metric("Requirements", len(quality_results))

        with qcol2:
            st.metric("PASS Checks", total_pass)

        with qcol3:
            st.metric("Review Checks", total_review)

        with qcol4:
            st.metric("Failed Checks", total_fail)

        st.divider()

        for result in quality_results:

            with st.container(border=True):

                st.markdown(
                    f"### {result['id']} — {result['overall']}"
                )

                st.write(
                    f"**Requirement:** {result['requirement']}"
                )

                check_rows = [
                    {
                        "Quality Check": check["Check"],
                        "Status": check["Status"],
                        "Details": check["Details"]
                    }
                    for check in result["checks"]
                ]

                st.dataframe(
                    check_rows,
                    use_container_width=True,
                    hide_index=True
                )

        if st.button(
            "🧾 Record Quality Check in Audit History",
            key="record_quality_audit_button"
        ):
            log_audit_event(
                event="Requirement quality check recorded",
                details=(
                    f"Checked {len(quality_results)} requirement(s) in "
                    f"scope '{quality_scope}'. PASS={total_pass}, "
                    f"REVIEW={total_review}, FAIL={total_fail}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=st.session_state.get(
                    "safety_goal_result", {}
                ).get("id", "SG-001"),
                fsr_id=(
                    st.session_state.get("tsr_fsr_id")
                    if quality_scope == "Selected FSR"
                    else None
                ),
                tsr_ids=(
                    [
                        item.get("id", "")
                        for item in quality_tsr_results
                    ]
                    if quality_scope == "Generated TSRs"
                    else []
                ),
            )
            st.success("Quality-check event recorded in audit history.")

        st.info(get_requirement_quality_review_note())


# =========================================================
# 10. TRACEABILITY MATRIX
# =========================================================

st.header(
    "10. Traceability Matrix"
)

st.write(
    "End-to-end traceability for the selected HARA candidate, "
    "candidate ASIL, Safety Goal, selected FSR and its generated TSRs."
)

traceability_context_ready = (
    st.session_state.get("active_hara_key") is not None
    and st.session_state.get("asil_assessment_completed", False)
    and st.session_state.get("safety_goal_result") is not None
    and bool(st.session_state.get("fsr_results"))
    and st.session_state.get("tsr_fsr_id") is not None
)

if not traceability_context_ready:

    st.caption(
        "Traceability Matrix will be available after "
        "HARA → ASIL → Safety Goal → FSR → TSR generation."
    )

else:

    safety_goal_data = st.session_state["safety_goal_result"]
    all_fsr_results = st.session_state["fsr_results"]

    active_hara_key = st.session_state.get("active_hara_key")
    traceability_candidate = None

    for candidate in hara_candidates:

        candidate_key = (
            candidate.get("malfunction", "").strip().lower(),
            candidate.get("hazard", "").strip().lower(),
            candidate.get("hazardous_event", "").strip().lower()
        )

        if candidate_key == active_hara_key:
            traceability_candidate = candidate
            break

    selected_fsr_id = st.session_state.get("tsr_fsr_id")
    selected_fsr = next(
        (
            fsr for fsr in all_fsr_results
            if fsr.get("id") == selected_fsr_id
        ),
        None
    )

    if traceability_candidate is None:

        st.warning(
            "The current HARA candidate could not be resolved. "
            "Please reselect the HARA candidate."
        )

    elif selected_fsr is None:

        st.warning(
            "The selected FSR could not be resolved. "
            "Please select an FSR and generate its TSRs again."
        )

    else:

        tsr_results = st.session_state.get(
            "tsr_results",
            []
        )

        # Only the FSR selected for TSR decomposition is shown.
        selected_fsr_results = [selected_fsr]

        traceability_rows = build_traceability_matrix(
            hara_candidate=traceability_candidate,
            candidate_asil=st.session_state.get(
                "candidate_asil",
                safety_goal_data.get("candidate_asil", "")
            ),
            safety_goal=safety_goal_data,
            fsr_results=selected_fsr_results,
            tsr_results=tsr_results
        )

        st.session_state["traceability_rows"] = traceability_rows

        summary_col1, summary_col2, summary_col3, summary_col4 = (
            st.columns(4)
        )

        with summary_col1:
            st.metric("HARA", "HARA-001")

        with summary_col2:
            st.metric(
                "ASIL",
                safety_goal_data.get(
                    "candidate_asil",
                    st.session_state.get("candidate_asil", "—")
                )
            )

        with summary_col3:
            st.metric("Selected FSR", selected_fsr.get("id", "—"))

        with summary_col4:
            st.metric("TSR Links", len(tsr_results))

        st.divider()

        # Parent-to-child traceability view.
        st.markdown("### Selected Safety Chain")

        st.markdown(
            f"""
            **HARA-001** — {traceability_candidate['malfunction']}

            ↓

            **ASIL {safety_goal_data.get('candidate_asil', '—')}**

            ↓

            **{safety_goal_data.get('id', 'SG-001')}** — "
            f"{safety_goal_data.get('safety_goal', '')}

            ↓

            **{selected_fsr.get('id', 'FSR-001')}** — "
            f"{selected_fsr.get('requirement', '')}

            ↓

            **Derived Technical Safety Requirements**
            """
        )

        if tsr_results:

            tsr_rows = [
                {
                    "TSR ID": tsr.get("id", "TSR-001"),
                    "Technical Safety Requirement": tsr.get(
                        "requirement",
                        ""
                    )
                }
                for tsr in tsr_results
            ]

            st.dataframe(
                tsr_rows,
                use_container_width=True,
                hide_index=True
            )

            st.caption(
                f"{len(tsr_results)} TSR(s) linked to "
                f"{selected_fsr.get('id', 'the selected FSR')}."
            )

        else:

            st.caption(
                "No TSR links are currently available."
            )

        with st.expander(
            "🔗 Engineering Traceability Details",
            expanded=False
        ):

            st.write(
                f"**Selected Malfunction:** "
                f"{traceability_candidate['malfunction']}"
            )

            st.write(
                f"**Selected Hazard:** "
                f"{traceability_candidate['hazard']}"
            )

            st.write(
                f"**Selected Hazardous Event:** "
                f"{traceability_candidate['hazardous_event']}"
            )

            st.write(
                f"**Candidate ASIL:** "
                f"{safety_goal_data.get('candidate_asil', '—')}"
            )

            st.write(
                f"**Safety Goal ID:** "
                f"{safety_goal_data.get('id', 'SG-001')}"
            )

            st.write(
                f"**Selected FSR ID:** "
                f"{selected_fsr.get('id', '—')}"
            )

            st.write(
                f"**TSR Count:** {len(tsr_results)}"
            )

        st.info(
            get_traceability_review_note()
        )




def create_audit_report_pdf(history):
    """Generate a human-readable PDF audit report."""

    # ReportLab is only needed when the user views/downloads
    # the audit report, so import it lazily.
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import (
        getSampleStyleSheet,
        ParagraphStyle,
    )
    from reportlab.lib.enums import TA_CENTER
    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    buffer = BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
        title="HARA AI Assistant - Audit Report",
        author="HARA AI Assistant",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "AuditTitle",
        parent=styles["Title"],
        alignment=TA_CENTER,
        fontSize=18,
        leading=22,
        spaceAfter=6,
    )

    subtitle_style = ParagraphStyle(
        "AuditSubtitle",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=9,
        leading=12,
        textColor=colors.grey,
        spaceAfter=18,
    )

    heading_style = ParagraphStyle(
        "AuditHeading",
        parent=styles["Heading2"],
        fontSize=12,
        leading=15,
        spaceBefore=10,
        spaceAfter=8,
    )

    body_style = ParagraphStyle(
        "AuditBody",
        parent=styles["BodyText"],
        fontSize=9,
        leading=12,
    )

    small_style = ParagraphStyle(
        "AuditSmall",
        parent=styles["BodyText"],
        fontSize=7,
        leading=9,
    )

    story = [
        Paragraph("HARA AI Assistant", title_style),
        Paragraph(
            "Decision History / Audit Evidence Report",
            subtitle_style,
        ),
        Paragraph(
            "Human-readable record of AI-assisted engineering actions "
            "and decision context.",
            body_style,
        ),
        Spacer(1, 12),
        Paragraph("Report Summary", heading_style),
    ]

    event_types = len({
        str(item.get("event", ""))
        for item in history
        if item.get("event")
    })

    latest = history[0] if history else {}

    summary_data = [
        ["Recorded Events", str(len(history))],
        ["Event Types", str(event_types)],
        ["HARA", str(latest.get("HARA ID", "—"))],
        ["ASIL", str(latest.get("ASIL", "—"))],
        ["Safety Goal", str(latest.get("Safety Goal ID", "—"))],
        ["FSR", str(latest.get("FSR ID", "—"))],
        ["TSRs", str(latest.get("TSR IDs", "—"))],
    ]

    summary_table = Table(
        summary_data,
        colWidths=[150, 330],
    )

    summary_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.4, colors.grey),
            ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#E9EEF5")),
            ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 6),
        ])
    )

    story += [summary_table, Spacer(1, 14)]
    story.append(
        Paragraph("Recorded Engineering Actions", heading_style)
    )

    table_data = [[
        "Timestamp (UTC)",
        "Event",
        "Details",
        "HARA",
        "ASIL",
        "SG",
        "FSR",
        "TSRs",
    ]]

    for item in history:
        table_data.append([
            Paragraph(str(item.get("timestamp_utc", "")), small_style),
            Paragraph(str(item.get("event", "")), small_style),
            Paragraph(str(item.get("details", "")), small_style),
            Paragraph(str(item.get("HARA ID", "")), small_style),
            Paragraph(str(item.get("ASIL", "")), small_style),
            Paragraph(str(item.get("Safety Goal ID", "")), small_style),
            Paragraph(str(item.get("FSR ID", "")), small_style),
            Paragraph(str(item.get("TSR IDs", "")), small_style),
        ])

    action_table = Table(
        table_data,
        colWidths=[62, 70, 155, 42, 32, 32, 38, 49],
        repeatRows=1,
    )

    action_table.setStyle(
        TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#20242C")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 7),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 4),
        ])
    )

    story += [action_table, Spacer(1, 14)]

    story.append(
        Paragraph(
            "<b>Engineering Review Notice:</b> This report records "
            "AI-assisted engineering actions and decision context. "
            "It is not an approval record and does not replace review "
            "or sign-off by an authorized functional-safety engineer.",
            body_style,
        )
    )

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


# =========================================================
# 11. DECISION HISTORY / AUDIT EVIDENCE
# =========================================================

st.header(
    "11. Decision History / Audit Evidence"
)

st.write(
    "Reviewable history of AI-assisted engineering actions and "
    "decision context recorded during the current project workflow."
)

audit_history = load_audit_history(AUDIT_HISTORY_PATH)

if not audit_history:

    st.caption(
        "No audit events have been recorded yet. Complete HARA, ASIL, "
        "Safety Goal, FSR or TSR actions to build the decision history."
    )

else:

    audit_col1, audit_col2, audit_col3 = st.columns(3)

    with audit_col1:
        st.metric("Recorded Events", len(audit_history))

    with audit_col2:
        unique_events = len(
            {
                item.get("event", "")
                for item in audit_history
            }
        )
        st.metric("Event Types", unique_events)

    with audit_col3:
        latest_event = audit_history[0].get(
            "event",
            "—"
        )
        st.metric("Latest Action", latest_event)

    st.divider()

    audit_rows = []

    for item in audit_history:

        audit_rows.append(
            {
                "Timestamp (UTC)": item.get(
                    "timestamp_utc",
                    ""
                ),
                "Event": item.get(
                    "event",
                    ""
                ),
                "Details": item.get(
                    "details",
                    ""
                ),
                "HARA": item.get(
                    "HARA ID",
                    ""
                ),
                "ASIL": item.get(
                    "ASIL",
                    ""
                ),
                "Safety Goal": item.get(
                    "Safety Goal ID",
                    ""
                ),
                "FSR": item.get(
                    "FSR ID",
                    ""
                ),
                "TSRs": item.get(
                    "TSR IDs",
                    ""
                ),
            }
        )

    st.dataframe(
        audit_rows,
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Audit Report")

    st.caption(
        "Human-readable project report for documentation and engineering review."
    )

    audit_report_pdf = create_audit_report_pdf(audit_history)

    st.download_button(
        "📄 Download Audit Report (PDF)",
        data=audit_report_pdf,
        file_name="HARA_AI_Assistant_Audit_Report.pdf",
        mime="application/pdf",
    )

    with st.expander(
        "Advanced: Export Raw Audit Data (JSON)",
        expanded=False
    ):
        st.download_button(
            "Download audit_history.json",
            data=json.dumps(
                list(reversed(audit_history)),
                indent=2,
                ensure_ascii=False
            ),
            file_name="hara_audit_history.json",
            mime="application/json",
        )

    if st.button(
        "🗑️ Clear Audit History",
        key="clear_audit_history_button"
    ):
        clear_audit_history(AUDIT_HISTORY_PATH)
        st.success("Audit history cleared.")
        st.rerun()

st.info(
    get_audit_review_note()
)



# =========================================================
# 12. ENGINEERING REVIEW / APPROVAL WORKFLOW
# =========================================================

st.header(
    "12. Engineering Review / Approval Workflow"
)

st.write(
    "Review and record an authorized functional-safety engineer's decision "
    "for generated safety artifacts."
)

st.caption(
    "The application does not autonomously approve safety artifacts. "
    "Only the authorized engineer can record the review decision."
)

review_decisions = load_review_decisions(REVIEW_DECISIONS_PATH)

review_fsr_results = st.session_state.get("fsr_results", [])
review_tsr_results = st.session_state.get("tsr_results", [])
review_safety_goal = st.session_state.get("safety_goal_result")

review_artifacts = []

if review_safety_goal:
    review_artifacts.append(
        (
            "Safety Goal",
            review_safety_goal.get("id", "SG-001"),
            review_safety_goal.get("safety_goal", ""),
        )
    )

for fsr in review_fsr_results:
    review_artifacts.append(
        (
            "FSR",
            fsr.get("id", "FSR-001"),
            fsr.get("requirement", ""),
        )
    )

for tsr in review_tsr_results:
    review_artifacts.append(
        (
            "TSR",
            tsr.get("id", "TSR-001"),
            tsr.get("requirement", ""),
        )
    )

if not review_artifacts:

    st.caption(
        "Generate a Safety Goal, FSR or TSR first. Review decisions will "
        "then be available for each generated artifact."
    )

else:

    review_labels = [
        f"{artifact_type} — {artifact_id}"
        for artifact_type, artifact_id, _ in review_artifacts
    ]

    selected_review_label = st.selectbox(
        "Select artifact to review",
        review_labels,
        key="review_artifact_selection",
    )

    selected_review_index = review_labels.index(selected_review_label)
    selected_review_type, selected_review_id, selected_review_text = (
        review_artifacts[selected_review_index]
    )

    latest_review = get_latest_review_decision(
        review_decisions,
        selected_review_type,
        selected_review_id,
    )

    st.markdown(
        f"### {selected_review_type} — {selected_review_id}"
    )

    st.write(
        f"**Candidate text:** {selected_review_text}"
    )

    if latest_review:
        st.write(
            f"**Current recorded decision:** "
            f"{latest_review.get('decision', 'Pending Review')}"
        )
        st.caption(
            f"Last reviewed by {latest_review.get('reviewer_name', '—')} "
            f"at {latest_review.get('timestamp_utc', '—')}"
        )
        if latest_review.get("comment"):
            st.caption(
                f"Last review comment: {latest_review['comment']}"
            )
    else:
        st.write("**Current recorded decision:** Pending Review")

    reviewer_name = st.text_input(
        "Authorized reviewer name",
        key="reviewer_name_input",
        placeholder="Enter functional-safety engineer name",
    )

    reviewer_confirmed = st.checkbox(
        "I confirm that I am an authorized functional-safety engineer "
        "performing this review.",
        key="reviewer_authorization_confirmed",
    )

    review_decision = st.radio(
        "Engineering review decision",
        [
            "Reviewed — Accept for engineering use",
            "Reviewed — Return for revision",
            "Reviewed — Reject",
        ],
        horizontal=True,
        key="review_decision_input",
    )

    review_comment = st.text_area(
        "Review comment",
        key="review_comment_input",
        placeholder="Record the review rationale, changes requested, or acceptance note.",
    )

    if st.button(
        "📝 Record Engineering Review Decision",
        type="primary",
        key="record_engineering_review_button",
    ):

        if not reviewer_name.strip():
            st.warning(
                "Enter the authorized reviewer's name before recording the decision."
            )

        elif not reviewer_confirmed:
            st.warning(
                "Confirm authorized functional-safety engineer status before "
                "recording the review decision."
            )

        else:

            saved_decision = save_review_decision(
                path=REVIEW_DECISIONS_PATH,
                artifact_type=selected_review_type,
                artifact_id=selected_review_id,
                decision=review_decision,
                reviewer_name=reviewer_name,
                comment=review_comment,
            )

            log_audit_event(
                event="Engineering review decision recorded",
                details=(
                    f"{selected_review_type} {selected_review_id}: "
                    f"{review_decision}. Reviewer={reviewer_name.strip()}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=(
                    review_safety_goal.get("id", "SG-001")
                    if review_safety_goal
                    else None
                ),
                fsr_id=(
                    selected_review_id
                    if selected_review_type == "FSR"
                    else st.session_state.get("tsr_fsr_id")
                ),
                tsr_ids=(
                    [
                        item.get("id", "")
                        for item in review_tsr_results
                    ]
                    if selected_review_type == "TSR"
                    else []
                ),
            )

            st.success(
                f"Review decision recorded for "
                f"{selected_review_type} {selected_review_id}."
            )
            st.rerun()

    st.divider()

    st.markdown("### Review Status Overview")

    overview_rows = []

    for artifact_type, artifact_id, _ in review_artifacts:

        latest = get_latest_review_decision(
            review_decisions,
            artifact_type,
            artifact_id,
        )

        overview_rows.append(
            {
                "Artifact": f"{artifact_type} — {artifact_id}",
                "Status": (
                    latest.get("decision", "Pending Review")
                    if latest
                    else "Pending Review"
                ),
                "Reviewer": (
                    latest.get("reviewer_name", "")
                    if latest
                    else ""
                ),
                "Last Updated (UTC)": (
                    latest.get("timestamp_utc", "")
                    if latest
                    else ""
                ),
            }
        )

    st.dataframe(
        overview_rows,
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "📄 Export Review Decisions (JSON)",
        data=json.dumps(
            review_decisions,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="review_decisions.json",
        mime="application/json",
    )

    if st.button(
        "🗑️ Clear Review Decisions",
        key="clear_review_decisions_button",
    ):
        clear_review_decisions(REVIEW_DECISIONS_PATH)
        st.rerun()

    st.info(get_review_note())



# =========================================================
# 13. VERIFICATION EVIDENCE MAPPING
# =========================================================

st.header("13. Verification Evidence Mapping")

st.write(
    "Record verification evidence and link it to a generated safety "
    "requirement for end-to-end engineering traceability."
)

st.caption(
    "This is a traceability aid. Recorded verification results do not "
    "establish ISO 26262 compliance or replace formal verification and validation."
)

verification_records = load_verification_records(
    VERIFICATION_RECORDS_PATH
)

verification_options = []

if st.session_state.get("safety_goal_result"):
    verification_options.append(
        (
            "Safety Goal",
            st.session_state["safety_goal_result"].get("id", "SG-001"),
        )
    )

for fsr in st.session_state.get("fsr_results", []):
    verification_options.append(
        ("FSR", fsr.get("id", "FSR-001"))
    )

for tsr in st.session_state.get("tsr_results", []):
    verification_options.append(
        ("TSR", tsr.get("id", "TSR-001"))
    )

if not verification_options:
    st.caption(
        "Generate a Safety Goal, FSR or TSR first to create a verification link."
    )
else:
    requirement_labels = [
        f"{kind} — {artifact_id}"
        for kind, artifact_id in verification_options
    ]

    selected_requirement_label = st.selectbox(
        "Requirement to verify",
        requirement_labels,
        key="verification_requirement_selection",
    )

    artifact_id = st.text_input(
        "Verification artifact ID",
        key="verification_artifact_id",
        placeholder="Example: VER-001",
    )

    artifact_name = st.text_input(
        "Verification artifact / test name",
        key="verification_artifact_name",
        placeholder="Example: Brake fault detection test",
    )

    verification_method = st.selectbox(
        "Verification method",
        [
            "Test",
            "Simulation",
            "Inspection",
            "Analysis",
            "Review",
        ],
        key="verification_method_selection",
    )

    verification_result = st.selectbox(
        "Verification result",
        [
            "Pass",
            "Fail",
            "Pending Review",
        ],
        key="verification_result_selection",
    )

    evidence_reference = st.text_input(
        "Evidence reference",
        key="verification_evidence_reference",
        placeholder="Example: Test report / log / simulation result reference",
    )

    verification_notes = st.text_area(
        "Verification notes",
        key="verification_notes",
        placeholder="Briefly describe what was verified.",
    )

    if st.button(
        "🔗 Record Verification Evidence",
        type="primary",
        key="record_verification_evidence",
    ):
        selected_kind, selected_id = verification_options[
            requirement_labels.index(selected_requirement_label)
        ]

        if not artifact_id.strip():
            st.warning("Enter a verification artifact ID.")
        elif not artifact_name.strip():
            st.warning("Enter a verification artifact/test name.")
        elif not evidence_reference.strip():
            st.warning("Enter an evidence reference.")
        else:
            save_verification_record(
                path=VERIFICATION_RECORDS_PATH,
                artifact_id=artifact_id,
                artifact_name=artifact_name,
                verification_method=verification_method,
                result=verification_result,
                linked_requirement=f"{selected_kind} — {selected_id}",
                evidence_reference=evidence_reference,
                notes=verification_notes,
            )

            log_audit_event(
                event="Verification evidence mapping recorded",
                details=(
                    f"{artifact_id.strip()} linked to "
                    f"{selected_kind} {selected_id}; result={verification_result}."
                ),
                asil=st.session_state.get("candidate_asil"),
                safety_goal_id=(
                    st.session_state.get("safety_goal_result", {}).get(
                        "id", "SG-001"
                    )
                    if st.session_state.get("safety_goal_result")
                    else None
                ),
                fsr_id=(
                    selected_id
                    if selected_kind == "FSR"
                    else st.session_state.get("tsr_fsr_id")
                ),
                tsr_ids=(
                    [selected_id]
                    if selected_kind == "TSR"
                    else []
                ),
            )

            st.success(
                f"Verification evidence {artifact_id.strip()} recorded "
                f"against {selected_kind} {selected_id}."
            )
            st.rerun()

st.divider()

st.markdown("### Verification Evidence Register")

if verification_records:
    st.dataframe(
        [
            {
                "Artifact ID": item.get("artifact_id", ""),
                "Artifact / Test": item.get("artifact_name", ""),
                "Method": item.get("verification_method", ""),
                "Result": item.get("result", ""),
                "Linked Requirement": item.get("linked_requirement", ""),
                "Evidence": item.get("evidence_reference", ""),
                "Timestamp (UTC)": item.get("timestamp_utc", ""),
            }
            for item in verification_records
        ],
        use_container_width=True,
        hide_index=True,
    )

    st.download_button(
        "📄 Export Verification Register (JSON)",
        data=json.dumps(
            verification_records,
            indent=2,
            ensure_ascii=False,
        ),
        file_name="verification_records.json",
        mime="application/json",
    )

    if st.button(
        "🗑️ Clear Verification Register",
        key="clear_verification_register",
    ):
        clear_verification_records(VERIFICATION_RECORDS_PATH)
        st.rerun()
else:
    st.caption("No verification evidence records have been added yet.")

st.info(get_verification_note())


# =========================================================
# 14. HARA WORKFLOW
# =========================================================

st.header(
    "13. HARA Workflow"
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