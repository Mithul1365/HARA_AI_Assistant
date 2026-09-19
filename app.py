from common import *

init_page("HARA AI Assistant — Dashboard")

page_header(
    "FUNCTIONAL SAFETY PLATFORM",
    "HARA AI Assistant",
    "AI-assisted HARA and safety requirement management workspace."
)

st.info(
    "Engineering Review Required: AI-generated content is candidate engineering "
    "material. Final functional-safety decisions require review and approval "
    "by an authorized functional-safety engineer."
)

# Current-session metrics
hara_ready = "hara_answer" in st.session_state
asil_ready = bool(st.session_state.get("candidate_asil"))
sg_ready = bool(st.session_state.get("safety_goal_result"))
fsr_count = len(st.session_state.get("fsr_results", []))
tsr_count = len(st.session_state.get("tsr_results", []))

c1, c2, c3, c4 = st.columns(4)
with c1:
    st.metric("HARA Analysis", "Ready" if hara_ready else "Not started")
with c2:
    st.metric("Candidate ASIL", st.session_state.get("candidate_asil", "—"))
with c3:
    st.metric("Safety Goals", "1" if sg_ready else "0")
with c4:
    st.metric("Requirements", fsr_count + tsr_count)

st.markdown("### Engineering Workspace")

p1, p2, p3 = st.columns(3)

with p1:
    with st.container(border=True):
        st.markdown("#### 🔍 HARA Analysis")
        st.caption("Define the item, scenario and identify candidate hazards.")
        st.page_link("pages/1_HARA_Analysis.py", label="Open HARA Analysis →")

with p2:
    with st.container(border=True):
        st.markdown("#### 🛡️ ASIL Assessment")
        st.caption("Assess Severity, Exposure and Controllability.")
        st.page_link("pages/2_ASIL_Assessment.py", label="Open ASIL Assessment →")

with p3:
    with st.container(border=True):
        st.markdown("#### 📋 Requirements")
        st.caption("Generate and review Safety Goals, FSRs and TSRs.")
        st.page_link("pages/3_Requirements.py", label="Open Requirements →")

p4, p5, p6 = st.columns(3)

with p4:
    with st.container(border=True):
        st.markdown("#### 🔗 Traceability")
        st.caption("Follow the selected safety chain end to end.")
        st.page_link("pages/4_Traceability.py", label="Open Traceability →")

with p5:
    with st.container(border=True):
        st.markdown("#### 📝 Review & Audit")
        st.caption("Record engineering review and verification evidence.")
        st.page_link("pages/5_Review_Audit.py", label="Open Review & Audit →")

with p6:
    with st.container(border=True):
        st.markdown("#### ⚙️ Workflow")
        st.caption("View the complete engineering processing flow.")
        st.page_link("pages/6_Workflow.py", label="Open Workflow →")

st.markdown("### Current Project Context")

context_rows = [
    ["System / Item", st.session_state.get("hara_system", "—")],
    ["Function", st.session_state.get("hara_function", "—")],
    ["Scenario", st.session_state.get("hara_scenario", "—")],
    ["Candidate ASIL", st.session_state.get("candidate_asil", "—")],
]
st.dataframe(
    context_rows,
    column_config={"0": "Field", "1": "Current Value"},
    hide_index=True,
    use_container_width=True,
)

st.caption("Use the sidebar to move between engineering stages. Your current workflow state is retained in Streamlit session state.")


