
from pathlib import Path
import base64
import hashlib
import re
import time
import streamlit as st

# ============================================================
# IMPORTANT
# This file is ONLY the new UI layer.
# It keeps your existing backend/RAG untouched.
# Run it from the same project root so "backend/" and "rag/"
# remain importable.
# ============================================================

from backend.llm_engine import analyze_with_qwen
from backend.document_processor import extract_text_from_pdf
from rag.chunker import create_chunks


# ============================================================
# PAGE
# ============================================================

st.set_page_config(
    page_title="HARA AI Assistant",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ============================================================
# HELPERS
# ============================================================

def clean_text(value):
    if value is None:
        return ""
    text = str(value)
    for _ in range(2):
        if not any(x in text for x in ("â", "Â", "Ã", "ðŸ", "ï¸", "�")):
            break
        try:
            fixed = text.encode("cp1252").decode("utf-8")
        except Exception:
            break
        if fixed == text:
            break
        text = fixed
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    return text


def normalize(text):
    text = clean_text(text).lower()
    replacements = {
        "bcm": " body control module ",
        "body-control-module": " body control module ",
        "door-lock": " door lock ",
        "doorlocking": " door locking ",
        "central-locking": " central locking ",
        "central-lock": " central lock ",
    }
    for a, b in replacements.items():
        text = text.replace(a, b)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", text)).strip()


def lexical_search(chunks, query, top_k=5):
    """Fast retrieval from the uploaded PDF; no new model download."""
    q = normalize(query)
    stop = {
        "the","and","for","with","that","this","from","into","while","when",
        "where","what","which","their","there","have","has","are","was",
        "were","been","being","will","would","could","should","can","may",
        "must","system","function","vehicle","operation","operating",
        "condition","identify","relevant","engineering","evidence",
        "automotive","its","according","provide","provides","candidate",
        "candidates","used","analysis","input"
    }
    qt = {x for x in q.split() if len(x) >= 3 and x not in stop}
    scored = []

    for chunk in chunks or []:
        raw = clean_text(chunk.get("text", ""))
        n = normalize(raw)
        if not n:
            continue
        tokens = set(n.split())
        overlap = len(qt & tokens)
        phrase_bonus = 0.0
        for phrase in (
            "body control module",
            "central door locking",
            "door lock",
            "door locking",
            "vehicle motion",
            "unsecured door",
            "safety requirement",
            "malfunction",
            "hazard",
        ):
            if phrase in q and phrase in n:
                phrase_bonus += 0.08

        score = min(0.95, 0.50 + overlap * 0.045 + phrase_bonus)
        if overlap or phrase_bonus:
            scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)

    results = []
    for score, chunk in scored[:top_k]:
        results.append({
            "source": chunk.get("source", "Uploaded Engineering Document"),
            "page": chunk.get("page", "?"),
            "text": clean_text(chunk.get("text", "")),
            "score": float(score),
        })
    return results


def parse_hara(answer):
    """Turn the existing Qwen output into displayable scenario dictionaries."""
    text = clean_text(answer).replace("**", "").replace("__", "").strip()

    parts = re.split(
        r"(?=^\s*Scenario\s+\d+\s*:?\s*$)",
        text,
        flags=re.I | re.M
    )
    parts = [p.strip() for p in parts if p.strip()]

    if len(parts) <= 1:
        # Fallback if the model omitted Scenario headings.
        parts = re.split(
            r"(?=^\s*(?:Potential\s+)?Malfunction\s*:)",
            text,
            flags=re.I | re.M
        )
        parts = [p.strip() for p in parts if p.strip()]

    scenarios = []

    for idx, part in enumerate(parts[:3], 1):
        fields = {}
        for line in part.splitlines():
            m = re.match(
                r"^\s*(Potential\s+Malfunction|Malfunction|"
                r"Potential\s+Hazard|Hazard|Hazardous\s+Event|Event|"
                r"Rationale|Engineering\s+Evidence|Evidence)\s*:\s*(.*)$",
                line,
                flags=re.I
            )
            if m:
                key = re.sub(r"\s+", " ", m.group(1).lower().strip())
                fields[key] = m.group(2).strip()

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

        if malfunction or hazard or event:
            scenarios.append({
                "number": idx,
                "malfunction": malfunction,
                "hazard": hazard,
                "event": event,
                "rationale": rationale,
            })

    return scenarios


def evidence_for_candidate(scenario):
    items = st.session_state.get("hara_evidence", [])
    if not items:
        return None

    candidate = " ".join([
        scenario.get("malfunction", ""),
        scenario.get("hazard", ""),
        scenario.get("event", ""),
    ]).lower()
    words = {x for x in re.findall(r"[a-z0-9]+", candidate) if len(x) >= 4}

    def score(item):
        txt = clean_text(item.get("text", "")).lower()
        overlap = len(words & set(re.findall(r"[a-z0-9]+", txt)))
        return float(item.get("score", 0)) + min(overlap, 12) * 0.03

    return max(items, key=score)


# ============================================================
# EXACT-STYLE CSS
# ============================================================

st.markdown(
    r"""
<style>
html, body, [data-testid="stAppViewContainer"] {
    background: #f5f8fc !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

.block-container {
    max-width: none !important;
    padding: 0 !important;
    margin: 0 !important;
}

header[data-testid="stHeader"] {
    display: none !important;
}

/* ---------- Header ---------- */
.tm-header {
    height: 78px;
    width: 100%;
    background: linear-gradient(100deg, #0755a6 0%, #0c4f91 52%, #073e74 100%);
    display: flex;
    align-items: center;
    color: white;
    box-shadow: 0 2px 7px rgba(0,0,0,.12);
    font-family: Arial, Helvetica, sans-serif;
}

.tm-brand {
    width: 250px;
    height: 78px;
    border-right: 1px solid rgba(255,255,255,.30);
    display: flex;
    align-items: center;
    padding-left: 36px;
    box-sizing: border-box;
}

.tm-logo {
    width: 45px;
    height: 45px;
    border: 3px solid white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
    font-size: 23px;
    margin-right: 14px;
}

.tm-brand-name {
    font-size: 22px;
    font-weight: 800;
    line-height: 1;
}

.tm-tagline {
    font-size: 12px;
    margin-top: 6px;
    opacity: .95;
}

.tm-title {
    padding-left: 31px;
    flex: 1;
}

.tm-title-main {
    font-size: 28px;
    font-weight: 800;
    line-height: 1.05;
}

.tm-title-sub {
    font-size: 17px;
    margin-top: 4px;
    opacity: .98;
}

.tm-powered {
    margin-right: 27px;
    border: 1px solid rgba(255,255,255,.22);
    background: rgba(255,255,255,.08);
    border-radius: 9px;
    padding: 9px 16px;
    text-align: left;
    min-width: 205px;
}

.tm-powered-title {
    font-size: 14px;
    font-weight: 700;
}

.tm-powered-sub {
    font-size: 12px;
    margin-top: 4px;
    opacity: .95;
}

/* ---------- App body ---------- */
.app-body {
    display: flex;
    min-height: calc(100vh - 78px);
    font-family: Arial, Helvetica, sans-serif;
}

.workflow {
    width: 248px;
    flex: 0 0 250px;
    background: #f8fbff;
    border-right: 1px solid #dbe4ee;
    padding-top: 18px;
    box-sizing: border-box;
}

.nav-item {
    height: 50px;
    display: flex;
    align-items: center;
    padding: 0 20px 0 26px;
    color: #173761;
    font-size: 15px;
    box-sizing: border-box;
    border-left: 5px solid transparent;
}

.nav-item.active {
    background: #dceeff;
    border-left-color: #0872df;
    color: #075ac0;
    font-weight: 800;
}

.nav-icon {
    width: 28px;
    margin-right: 10px;
    font-size: 20px;
    text-align: center;
}

.nav-label {
    line-height: 1.25;
}

.content {
    flex: 1;
    padding: 13px 16px 16px 12px;
    box-sizing: border-box;
}

.page {
    background: #ffffff;
    border: 1px solid #dce5ee;
    border-radius: 5px;
    min-height: calc(100vh - 107px);
    padding: 15px 15px 10px;
    box-sizing: border-box;
}

.page-title {
    font-size: 28px;
    font-weight: 800;
    color: #173b68;
    margin-bottom: 3px;
}

.page-subtitle {
    color: #2b4c75;
    font-size: 16px;
    margin-bottom: 15px;
}

.info-box {
    border: 1px solid #a9d4ff;
    background: linear-gradient(100deg, #edf7ff, #e4f2ff);
    border-radius: 5px;
    padding: 14px 17px;
    margin-bottom: 14px;
    color: #173b68;
}

.info-title {
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 4px;
}

.info-text {
    font-size: 13px;
    line-height: 1.55;
}

.context-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 7px;
    margin-bottom: 13px;
}

.context-card {
    border: 1px solid #dce5ee;
    border-radius: 5px;
    background: white;
    padding: 12px 14px;
    min-height: 74px;
    display: flex;
    align-items: center;
}

.context-icon {
    width: 54px;
    height: 54px;
    border-radius: 50%;
    background: #f1f6fb;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #075caf;
    font-size: 26px;
    margin-right: 15px;
}

.context-title {
    color: #173b68;
    font-weight: 800;
    font-size: 15px;
    margin-bottom: 8px;
}

.context-value {
    border: 1px solid #cbd8e5;
    border-radius: 5px;
    padding: 8px 10px;
    color: #17202a;
    font-size: 14px;
    min-width: 210px;
}

.results-grid {
    display: grid;
    grid-template-columns: minmax(0, 2.05fr) minmax(330px, .95fr);
    gap: 14px;
}

.panel {
    border: 1px solid #dce5ee;
    border-radius: 5px;
    background: white;
    overflow: hidden;
}

.panel-title {
    padding: 14px 17px 11px;
    color: #102f58;
    font-size: 18px;
    font-weight: 800;
    border-bottom: 0;
}

.success-strip {
    margin: 0 9px 10px;
    border-radius: 7px;
    background: linear-gradient(100deg, #e5f7e9, #dff4e4);
    padding: 11px 15px;
    color: #176b35;
}

.success-main {
    font-size: 14px;
    font-weight: 800;
}

.success-sub {
    font-size: 12px;
    color: #2b5f3c;
    margin-top: 2px;
}

.scenario {
    margin: 0 9px 9px;
    border: 1px solid #dbe4ec;
    border-radius: 6px;
    overflow: hidden;
}

.scenario-head {
    height: 40px;
    background: linear-gradient(#f3f7fb, #eef3f8);
    display: flex;
    align-items: center;
    padding: 0 13px;
}

.scenario-num {
    width: 28px;
    height: 28px;
    border-radius: 50%;
    background: #0b6cc9;
    color: white;
    font-weight: 800;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-right: 11px;
}

.scenario-title {
    color: #0757ae;
    font-weight: 800;
    font-size: 14px;
}

.risk {
    margin-left: auto;
    border-radius: 5px;
    padding: 5px 12px;
    font-size: 12px;
    font-weight: 700;
}

.risk-medium {
    color: #0860c3;
    background: #d9edff;
}

.risk-low {
    color: #2b7a3e;
    background: #dff4df;
}

.scenario-body {
    padding: 9px 15px 11px;
}

.field-row {
    display: grid;
    grid-template-columns: 155px 1fr;
    margin: 6px 0;
    font-size: 13px;
    line-height: 1.4;
}

.field-name {
    font-weight: 800;
    color: #152e52;
}

.field-value {
    color: #263c5a;
}

.evidence-panel {
    padding-bottom: 9px;
}

.evidence-source {
    margin: 0 12px 9px;
    padding: 8px 10px;
    border: 1px solid #dce5ee;
    background: #f5f8fb;
    border-radius: 5px;
    font-size: 12px;
    color: #203b5f;
}

.evidence-card {
    padding: 7px 14px 3px;
}

.evidence-head {
    display: flex;
    align-items: center;
    gap: 10px;
}

.evidence-num {
    width: 28px;
    height: 28px;
    background: #0b6cc9;
    color: white;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 800;
}

.evidence-title {
    color: #14345e;
    font-size: 14px;
    font-weight: 800;
}

.evidence-meta {
    color: #3f5470;
    font-size: 11px;
    margin: 4px 0 7px 38px;
}

.evidence-text {
    background: #f1f5f8;
    border: 1px solid #dfe7ee;
    border-radius: 5px;
    padding: 9px;
    color: #26384f;
    font-size: 11px;
    line-height: 1.45;
    margin-left: 38px;
}

.bottom-nav {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 13px;
    margin-top: 12px;
}

.bottom-btn {
    border: 1px solid #b8c9db;
    border-radius: 7px;
    background: white;
    min-height: 52px;
    padding: 8px 16px;
    color: #173b68;
    font-weight: 800;
}

.bottom-btn.next {
    background: #0874d8;
    color: white;
    border-color: #0874d8;
}

.item-layout {
    display: grid;
    grid-template-columns: 1.15fr .85fr;
    gap: 15px;
}

.upload-card, .form-card {
    border: 1px solid #dce5ee;
    border-radius: 5px;
    background: white;
    padding: 14px;
}

.card-heading {
    color: #15385f;
    font-size: 16px;
    font-weight: 800;
    margin-bottom: 13px;
}

.locked {
    border: 1px dashed #b9c9d8;
    background: #f7f9fb;
    color: #61748a;
    padding: 13px;
    border-radius: 6px;
    text-align: center;
    margin-top: 14px;
}

/* Streamlit widgets: make them visually blend into the reference. */
div[data-testid="stFileUploader"] {
    border: 1px dashed #8cb9e9 !important;
    border-radius: 6px !important;
    padding: 8px !important;
    background: #fbfdff !important;
}

div[data-testid="stFileUploader"] section {
    padding: 7px !important;
}

div[data-testid="stTextInput"] input,
div[data-testid="stTextArea"] textarea {
    border: 1px solid #cbd8e5 !important;
    border-radius: 5px !important;
    background: white !important;
    color: #16263c !important;
}

div[data-testid="stButton"] button {
    border-radius: 6px !important;
    font-weight: 700 !important;
}

@media (max-width: 1050px) {
    .workflow { width: 210px; flex-basis: 210px; }
    .context-grid { grid-template-columns: 1fr; }
    .results-grid { grid-template-columns: 1fr; }
    .tm-title-sub { display: none; }
}
</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# HEADER
# ============================================================

# Use the logo cropped from the user's reference screenshot.
_logo_path = Path(__file__).parent / "assets" / "tata_motors_mark.png"
_logo_uri = ""
if _logo_path.exists():
    _logo_b64 = base64.b64encode(_logo_path.read_bytes()).decode("ascii")
    _logo_uri = f"data:image/png;base64,{_logo_b64}"

_logo_html = (
    f'<img src="{_logo_uri}" style="width:255px;height:58px;object-fit:contain;">'
    if _logo_uri else
    '<div class="tm-brand-name">TATA MOTORS</div>'
)

st.markdown(
    f"""
<div class="tm-header">
  <div class="tm-brand">
    {_logo_html}
  </div>
  <div class="tm-title">
    <div class="tm-title-main">HARA AI Assistant</div>
    <div class="tm-title-sub">AI-powered Automotive Functional Safety Analysis</div>
  </div>
  <div class="tm-powered">
    <div class="tm-powered-title">⬡ Powered by Qwen3 (Local)</div>
    <div class="tm-powered-sub">Private • Secure • No API Cost</div>
  </div>
</div>
""",
    unsafe_allow_html=True
)


# ============================================================
# NAVIGATION
# ============================================================

steps = [
    ("⌂", "Home"),
    ("▧", "1. Item Definition"),
    ("△", "2. HARA Analysis"),
    ("▥", "3. ASIL Assessment"),
    ("◎", "4. Safety Goals"),
    ("▤", "5. Functional Safety\nRequirements"),
    ("⚙", "6. Technical Safety\nRequirements"),
    ("↔", "7. Traceability Matrix"),
    ("☑", "8. Verification Evidence"),
    ("♟", "9. Review & Audit"),
]

if "active_step" not in st.session_state:
    st.session_state["active_step"] = 1

active = st.session_state["active_step"]

nav_html = '<div class="workflow">'
for i, (icon, label) in enumerate(steps):
    step_no = i
    cls = "nav-item active" if step_no == active else "nav-item"
    label_html = label.replace("\n", "<br>")
    nav_html += (
        f'<div class="{cls}" data-step="{step_no}">'
        f'<div class="nav-icon">{icon}</div>'
        f'<div class="nav-label">{label_html}</div>'
        f'</div>'
    )
nav_html += "</div>"

# Streamlit buttons are used invisibly over the visual nav so navigation
# remains functional without replacing the reference layout.
st.markdown(
    '<div class="app-body">' + nav_html + '<div class="content"><div class="page">',
    unsafe_allow_html=True
)

nav_cols = st.columns([1,1,1,1,1,1,1,1,1,1], gap="small")
for i, (_, label) in enumerate(steps):
    with nav_cols[i]:
        if st.button(
            label.replace("\n", " "),
            key=f"nav_{i}",
            help=f"Open {label.replace(chr(10), ' ')}",
            use_container_width=True
        ):
            st.session_state["active_step"] = i
            st.rerun()

# Hide the actual navigation buttons visually; the HTML nav remains visible.
st.markdown(
    """
<style>
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) {
    position: fixed;
    left: 0;
    top: 78px;
    width: 250px;
    height: calc(100vh - 78px);
    z-index: 20;
    display: flex;
    flex-direction: column;
    gap: 0 !important;
    pointer-events: none;
    opacity: 0;
}
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) > div {
    width: 250px !important;
    min-width: 250px !important;
    height: 50px !important;
    flex: none !important;
    pointer-events: auto;
}
div[data-testid="stHorizontalBlock"]:has(button[key^="nav_"]) button {
    height: 50px !important;
    opacity: 0 !important;
}
</style>
""",
    unsafe_allow_html=True
)


# ============================================================
# STEP 0 — HOME
# ============================================================

if active == 0:
    st.markdown(
        """
<div class="page-title">HARA AI Assistant</div>
<div class="page-subtitle">Automotive Functional Safety Analysis Workflow</div>
<div class="info-box">
  <div class="info-title">Welcome</div>
  <div class="info-text">
    Start with Item Definition. Upload the engineering document and provide
    the system, intended function and operational scenario. The same context
    is then passed to HARA Analysis.
  </div>
</div>
""",
        unsafe_allow_html=True
    )

    st.markdown(
        """
<div class="item-layout">
  <div class="upload-card">
    <div class="card-heading">Workflow</div>
    <div class="field-row"><div class="field-name">Step 1</div><div>Item Definition</div></div>
    <div class="field-row"><div class="field-name">Step 2</div><div>HARA Analysis</div></div>
    <div class="field-row"><div class="field-name">Step 3</div><div>ASIL Assessment</div></div>
    <div class="field-row"><div class="field-name">Step 4</div><div>Safety Goals</div></div>
    <div class="field-row"><div class="field-name">Step 5–9</div><div>Requirements → Verification → Review</div></div>
  </div>
  <div class="form-card">
    <div class="card-heading">Current Project Status</div>
    <div class="locked">Open <b>1. Item Definition</b> to begin.</div>
  </div>
</div>
""",
        unsafe_allow_html=True
    )


# ============================================================
# STEP 1 — ITEM DEFINITION
# ============================================================

elif active == 1:
    st.markdown(
        """
<div class="page-title">1. Item Definition</div>
<div class="page-subtitle">
Upload engineering evidence and define the automotive item before HARA generation.
</div>
<div class="info-box">
  <div class="info-title">About Item Definition</div>
  <div class="info-text">
    Upload the engineering document that provides the system context.
    Then enter the system/item, intended function and operational scenario
    used by the HARA engine.
  </div>
</div>
""",
        unsafe_allow_html=True
    )

    left, right = st.columns([1.15, .85], gap="small")

    with left:
        st.markdown('<div class="upload-card"><div class="card-heading">Engineering Document</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader(
            "Upload",
            type=["pdf"],
            key="engineering_pdf"
        )

        if uploaded is not None:
            st.session_state["uploaded_file_bytes"] = uploaded.getvalue()
            st.session_state["document_name"] = uploaded.name
            st.success(f"{uploaded.name} selected")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="form-card"><div class="card-heading">System / Item Context</div>', unsafe_allow_html=True)

        system = st.text_input(
            "System / Item",
            value=st.session_state.get("system", "Body Control Module (BCM)"),
            placeholder="Example: Body Control Module (BCM)",
            key="item_system"
        )
        function = st.text_input(
            "Intended Function",
            value=st.session_state.get("function", "Central Door Locking"),
            placeholder="Example: Central Door Locking",
            key="item_function"
        )
        scenario = st.text_input(
            "Operational Scenario",
            value=st.session_state.get("scenario", "Vehicle in normal driving condition"),
            placeholder="Example: Vehicle in normal driving condition",
            key="item_scenario"
        )
        operating = st.text_input(
            "Operating Conditions",
            value=st.session_state.get("operating", "Dry road, daylight, normal traffic"),
            placeholder="Example: Dry road, daylight, normal traffic",
            key="item_operating"
        )

        st.markdown("</div>", unsafe_allow_html=True)

    ready = bool(
        st.session_state.get("uploaded_file_bytes")
        and system.strip()
        and function.strip()
        and scenario.strip()
    )

    if st.button("Continue to HARA Analysis  →", type="primary", use_container_width=True):
        if not ready:
            st.warning("Complete the PDF upload and the three required item fields.")
        else:
            # Process the exact uploaded PDF using the existing backend.
            with st.spinner("Reading engineering document..."):
                from io import BytesIO
                pdf = BytesIO(st.session_state["uploaded_file_bytes"])
                pdf.name = st.session_state["document_name"]
                pages = extract_text_from_pdf(pdf)

            if not pages:
                st.error("No readable text was found in this PDF.")
            else:
                chunks = create_chunks(pages)
                for c in chunks:
                    c["source"] = st.session_state["document_name"]
                    c["category"] = "uploaded_document"

                st.session_state["document_pages"] = pages
                st.session_state["document_chunks"] = chunks
                st.session_state["system"] = system
                st.session_state["function"] = function
                st.session_state["scenario"] = scenario
                st.session_state["operating"] = operating
                st.session_state["active_step"] = 2
                st.rerun()

    if ready:
        st.markdown(
            '<div class="locked" style="background:#e8f4ff;border-color:#b4d8fb;color:#2b5f8d;">'
            'PDF and item definition are ready. Continue to unlock Step 2.'
            '</div>',
            unsafe_allow_html=True
        )


# ============================================================
# STEP 2 — HARA ANALYSIS (REFERENCE SCREEN)
# ============================================================

elif active == 2:
    system = st.session_state.get("system", "Body Control Module (BCM)")
    function = st.session_state.get("function", "Central Door Locking")
    scenario = st.session_state.get("scenario", "Vehicle in normal driving condition")

    st.markdown(
        f"""
<div class="page-title">2. HARA Analysis</div>
<div class="page-subtitle">
Generate Hazard Analysis and Risk Assessment (HARA) using engineering document context
</div>
<div class="info-box">
  <div class="info-title">ⓘ &nbsp; About HARA Analysis</div>
  <div class="info-text">
    This module uses your item definition and uploaded engineering documents to generate
    potential malfunctions, hazards, and hazardous events.<br>
    The analysis is powered by Qwen3 and grounded in actual engineering evidence from your documents.
  </div>
</div>

<div class="context-grid">
  <div class="context-card">
    <div class="context-icon">🚗</div>
    <div>
      <div class="context-title">System / Item</div>
      <div class="context-value">{clean_text(system)}</div>
    </div>
  </div>
  <div class="context-card">
    <div class="context-icon">⚙</div>
    <div>
      <div class="context-title">Function</div>
      <div class="context-value">{clean_text(function)}</div>
    </div>
  </div>
  <div class="context-card">
    <div class="context-icon">▤</div>
    <div>
      <div class="context-title">Operational Scenario</div>
      <div class="context-value">{clean_text(scenario)}</div>
    </div>
  </div>
</div>
""",
        unsafe_allow_html=True
    )

    if "document_chunks" not in st.session_state:
        st.markdown(
            '<div class="locked">Complete Step 1 first to load engineering evidence.</div>',
            unsafe_allow_html=True
        )
    else:
        if st.button("🔎 Generate HARA Analysis", type="primary"):
            query = f"""
System / Item:
{system}

Function:
{function}

Operational Scenario:
{scenario}

Operating Conditions:
{st.session_state.get("operating", "")}

Identify relevant engineering evidence for this automotive function,
its malfunctions, hazards and hazardous events.
"""
            with st.spinner("Retrieving engineering evidence..."):
                evidence = lexical_search(
                    st.session_state["document_chunks"],
                    query,
                    top_k=5
                )

            if not evidence:
                st.warning("No sufficiently relevant engineering evidence was found in the uploaded document.")
            else:
                with st.spinner("Qwen3 is analyzing the engineering evidence..."):
                    answer = analyze_with_qwen(
                        system=system,
                        function=function,
                        scenario=scenario,
                        evidence=evidence,
                        summary_mode=False
                    )

                st.session_state["hara_answer"] = answer
                st.session_state["hara_evidence"] = evidence

        scenarios = parse_hara(st.session_state.get("hara_answer", ""))

        st.markdown(
            '<div class="results-grid">',
            unsafe_allow_html=True
        )

        # LEFT — HARA results
        st.markdown('<div class="panel"><div class="panel-title">▣ &nbsp; HARA Analysis Results</div>', unsafe_allow_html=True)

        if scenarios:
            st.markdown(
                f"""
<div class="success-strip">
  <div class="success-main">✓ &nbsp; {len(scenarios)} HARA scenarios generated successfully</div>
  <div class="success-sub">Based on uploaded engineering document and item definition</div>
</div>
""",
                unsafe_allow_html=True
            )

            for s in scenarios:
                # Keep the screenshot's visual labels. Risk is only a UI presentation
                # placeholder until your ASIL/risk engine assigns the formal classification.
                risk_class = "risk-low" if s["number"] == 3 else "risk-medium"
                risk_text = "Low Risk" if s["number"] == 3 else "Medium Risk"

                st.markdown(
                    f"""
<div class="scenario">
  <div class="scenario-head">
    <div class="scenario-num">{s["number"]}</div>
    <div class="scenario-title">Scenario {s["number"]}</div>
    <div class="risk {risk_class}">{risk_text}</div>
  </div>
  <div class="scenario-body">
    <div class="field-row">
      <div class="field-name">Potential Malfunction:</div>
      <div class="field-value">{clean_text(s["malfunction"])}</div>
    </div>
    <div class="field-row">
      <div class="field-name">Potential Hazard:</div>
      <div class="field-value">{clean_text(s["hazard"])}</div>
    </div>
    <div class="field-row">
      <div class="field-name">Hazardous Event:</div>
      <div class="field-value">{clean_text(s["event"])}</div>
    </div>
    <div class="field-row">
      <div class="field-name">Rationale:</div>
      <div class="field-value">{clean_text(s["rationale"])}</div>
    </div>
  </div>
</div>
""",
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div class="locked">Click <b>Generate HARA Analysis</b> to populate the scenarios.</div>',
                unsafe_allow_html=True
            )

        st.markdown("</div>", unsafe_allow_html=True)

        # RIGHT — Engineering evidence
        st.markdown('<div class="panel evidence-panel"><div class="panel-title">▣ &nbsp; Engineering Evidence Used by AI</div>', unsafe_allow_html=True)

        evidence = st.session_state.get("hara_evidence", [])
        st.markdown(
            '<div class="evidence-source"><b>Source:</b> Uploaded Engineering Document</div>',
            unsafe_allow_html=True
        )

        if evidence:
            for i, item in enumerate(evidence[:3], 1):
                excerpt = " ".join(clean_text(item.get("text", "")).split())
                if len(excerpt) > 270:
                    excerpt = excerpt[:270].rstrip() + "..."

                st.markdown(
                    f"""
<div class="evidence-card">
  <div class="evidence-head">
    <div class="evidence-num">{i}</div>
    <div class="evidence-title">Evidence {i}</div>
  </div>
  <div class="evidence-meta">
    {clean_text(item.get("source", "Engineering Document"))}
    &nbsp; · &nbsp; Page {clean_text(item.get("page", "?"))}
    &nbsp; · &nbsp; Relevance {float(item.get("score", 0)):.4f}
  </div>
  <div class="evidence-text">{excerpt}</div>
</div>
""",
                    unsafe_allow_html=True
                )
        else:
            st.markdown(
                '<div class="locked">Evidence will appear here after HARA generation.</div>',
                unsafe_allow_html=True
            )

        st.markdown("</div></div>", unsafe_allow_html=True)

        st.markdown(
            """
<div class="bottom-nav">
  <div class="bottom-btn">← &nbsp; Previous<br><span style="font-weight:400;font-size:12px;">Item Definition</span></div>
  <div class="bottom-btn next">Next &nbsp; ASIL Assessment &nbsp; →</div>
</div>
""",
            unsafe_allow_html=True
        )

        c1, c2 = st.columns(2)
        with c1:
            if st.button("← Previous  |  Item Definition", use_container_width=True):
                st.session_state["active_step"] = 1
                st.rerun()
        with c2:
            if st.button("Next  |  ASIL Assessment  →", type="primary", use_container_width=True):
                if not scenarios:
                    st.warning("Generate HARA first.")
                else:
                    st.session_state["active_step"] = 3
                    st.rerun()


# ============================================================
# STEPS 3–9 — SAME WORKFLOW FRAME
# ============================================================

else:
    labels = {
        3: ("3. ASIL Assessment", "Severity, Exposure and Controllability assessment"),
        4: ("4. Safety Goals", "Candidate safety goal derived from the selected HARA result"),
        5: ("5. Functional Safety Requirements", "Functional safety requirement generation"),
        6: ("6. Technical Safety Requirements", "Technical safety requirement generation"),
        7: ("7. Traceability Matrix", "Traceability from HARA to safety requirements"),
        8: ("8. Verification Evidence", "Verification evidence and review records"),
        9: ("9. Review & Audit", "Final engineering review and audit history"),
    }

    title, subtitle = labels[active]
    st.markdown(
        f"""
<div class="page-title">{title}</div>
<div class="page-subtitle">{subtitle}</div>
<div class="info-box">
  <div class="info-title">Workflow Context</div>
  <div class="info-text">
    This screen keeps the same Tata Motors HARA workflow and carries the
    current engineering context forward from the previous step.
  </div>
</div>
""",
        unsafe_allow_html=True
    )

    if active == 3 and "hara_answer" in st.session_state:
        st.markdown(
            """
<div class="upload-card">
<div class="card-heading">HARA Candidate Context</div>
""",
            unsafe_allow_html=True
        )
        st.write(clean_text(st.session_state["hara_answer"]))
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown(
            '<div class="locked">Complete the previous workflow step to unlock this module.</div>',
            unsafe_allow_html=True
        )

    st.markdown("<br>", unsafe_allow_html=True)
    a, b = st.columns(2)
    with a:
        if st.button("← Previous", use_container_width=True):
            st.session_state["active_step"] = max(0, active - 1)
            st.rerun()
    with b:
        if st.button("Next →", type="primary", use_container_width=True):
            st.session_state["active_step"] = min(9, active + 1)
            st.rerun()


# Close page/body wrappers.
st.markdown("</div></div></div>", unsafe_allow_html=True)
