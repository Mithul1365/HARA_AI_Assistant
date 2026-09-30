from common import *

init_page("HARA AI Assistant â€” Workflow")
page_header("REFERENCE", "Workflow", "Reference view of the complete HARA engineering workflow.")

# 14. HARA WORKFLOW
# =========================================================

st.header(
    "HARA Workflow"
)

st.markdown(
    """
    **Engineering Document**
    â†’
    **Document Extraction**
    â†’
    **Chunking**
    â†’
    **Semantic Embeddings**
    â†’
    **Domain-Aware Retrieval**
    â†’
    **Evidence Validation**
    â†’
    **Local Qwen3 Analysis**
    â†’
    **Malfunction Identification**
    â†’
    **Hazard Identification**
    â†’
    **Hazardous Event**
    â†’
    **S/E/C Assessment**
    â†’
    **Candidate ASIL**
    â†’
    **Safety Goal**
    â†’
    **FSR**
    â†’
    **TSR**
    â†’
    **Traceability**
    """
)
