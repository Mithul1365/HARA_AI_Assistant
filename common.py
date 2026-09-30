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
        page_icon="ðŸš—",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
            max-width: 1500px;
        }
        [data-testid="stSidebar"] {
            border-right: 1px solid rgba(128,128,128,0.18);
        }
        [data-testid="stSidebarNav"] {
            display: none;
        }
        .app-brand { padding: 0.35rem 0 0.9rem 0; }
        .app-brand-title { font-size: 1.18rem; font-weight: 750; margin-bottom: 0.12rem; }
        .app-brand-subtitle { font-size: 0.72rem; opacity: 0.62; }
        .sidebar-section {
            font-size: 0.68rem;
            font-weight: 750;
            letter-spacing: 0.11em;
            opacity: 0.52;
            margin: 0.85rem 0 0.35rem 0;
        }
        .page-kicker {
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            opacity: 0.55;
            margin-bottom: 0.2rem;
        }
        .page-title {
            font-size: 2.15rem;
            font-weight: 780;
            line-height: 1.15;
            margin-bottom: 0.25rem;
        }
        .page-subtitle { opacity: 0.66; margin-bottom: 1.35rem; }
        div[data-testid="stMetric"] {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 12px;
            padding: 0.72rem 0.85rem;
        }
        div[data-testid="stMetricLabel"] { font-size: 0.75rem; }
        .workflow-step {
            border: 1px solid rgba(128,128,128,0.18);
            border-radius: 10px;
            padding: 0.75rem 0.85rem;
            text-align: center;
            min-height: 82px;
        }
        .workflow-step-title { font-weight: 700; font-size: 0.88rem; }
        .workflow-step-state { font-size: 0.7rem; opacity: 0.6; margin-top: 0.25rem; }
    </style>
    """, unsafe_allow_html=True)

    with st.sidebar:
        st.markdown("""
        <div class="app-brand">
            <div class="app-brand-title">ðŸš— HARA AI Assistant</div>
            <div class="app-brand-subtitle">Functional Safety Engineering Platform</div>
        </div>
        """, unsafe_allow_html=True)
        st.divider()
        st.markdown('<div class="sidebar-section">WORKSPACE</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">ENGINEERING REVIEW</div>', unsafe_allow_html=True)
        st.markdown('<div class="sidebar-section">PROJECT</div>', unsafe_allow_html=True)
        st.divider()
        st.caption("AI outputs are candidate engineering material and require authorized functional-safety review.")

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
        ["HARA", str(latest.get("HARA ID", "â€”"))],
        ["ASIL", str(latest.get("ASIL", "â€”"))],
        ["Safety Goal", str(latest.get("Safety Goal ID", "â€”"))],
        ["FSR", str(latest.get("FSR ID", "â€”"))],
        ["TSRs", str(latest.get("TSR IDs", "â€”"))],
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

