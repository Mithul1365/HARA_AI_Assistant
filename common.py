from pathlib import Path
import re
import hashlib
import pickle
import json
import streamlit as st
import pyttsx3
import subprocess
import sys
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


# =========================================================
# SHARED UI HELPERS
# =========================================================

def init_page(page_title="HARA AI Assistant"):
    st.set_page_config(
        page_title=page_title,
        page_icon="🛡️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
        .block-container {
            padding-top: 2rem;
            padding-bottom: 2rem;
            max-width: 1450px;
        }

        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128,128,128,0.18);
        }

        .app-brand {
            padding: 0.4rem 0 1rem 0;
        }

        .app-brand-title {
            font-size: 1.25rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }

        .app-brand-subtitle {
            font-size: 0.75rem;
            opacity: 0.68;
        }

        .page-kicker {
            font-size: 0.78rem;
            font-weight: 650;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            opacity: 0.65;
            margin-bottom: 0.25rem;
        }

        .page-title {
            font-size: 2rem;
            font-weight: 750;
            margin-bottom: 0.15rem;
        }

        .page-subtitle {
            opacity: 0.68;
            margin-bottom: 1.5rem;
        }

        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 12px;
            padding: 0.75rem;
        }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div class="app-brand">
            <div class="app-brand-title">🛡️ HARA AI Assistant</div>
            <div class="app-brand-subtitle">Functional Safety Engineering Platform</div>
        </div>
        """, unsafe_allow_html=True)

        st.divider()

        st.caption("WORKSPACE")
        st.caption("Automotive Functional Safety")

        st.divider()

        st.caption("ENGINEERING REVIEW")
        st.caption("AI outputs are candidate engineering content and require authorized functional-safety review.")

def page_header(kicker, title, subtitle=""):
    st.markdown(f'<div class="page-kicker">{kicker}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="page-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="page-subtitle">{subtitle}</div>', unsafe_allow_html=True)

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
        pass
