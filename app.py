import streamlit as st

from backend.hara_engine import analyze_malfunctions
from backend.document_processor import extract_text_from_pdf

from rag.chunker import create_chunks
from rag.vector_store import create_vector_store, search_documents


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
    "Prototype: AI-assisted hazard analysis. Final safety decisions "
    "must be reviewed and approved by a qualified functional-safety engineer."
)


# =========================================================
# 1. ENGINEERING DOCUMENT
# =========================================================

st.header("📄 1. Engineering Document")

uploaded_file = st.file_uploader(
    "Upload an Item Definition / Architecture / HARA PDF",
    type=["pdf"]
)


if uploaded_file is not None:

    st.success(
        f"Uploaded: {uploaded_file.name}"
    )

    if st.button("📖 Read Document"):

        with st.spinner("Reading PDF..."):

            pages = extract_text_from_pdf(uploaded_file)

        if not pages:

            st.warning(
                "No readable text was found in this PDF."
            )

        else:

            # Store extracted pages
            st.session_state["document_pages"] = pages

            # Store document name
            st.session_state["document_name"] = uploaded_file.name

            st.success(
                f"Successfully read {len(pages)} pages."
            )

            # -------------------------------------------------
            # CREATE DOCUMENT CHUNKS
            # -------------------------------------------------

            chunks = create_chunks(pages)

            st.session_state["document_chunks"] = chunks

            st.success(
                f"Created {len(chunks)} document chunks."
            )

            # -------------------------------------------------
            # CREATE VECTOR STORE
            # -------------------------------------------------

            with st.spinner(
                "Creating semantic search index..."
            ):

                vector_index = create_vector_store(
                    chunks
                )

            st.session_state["vector_index"] = vector_index

            st.success(
                "Semantic search index created successfully."
            )


# =========================================================
# SHOW EXTRACTED DOCUMENT
# =========================================================

if "document_pages" in st.session_state:

    st.header("📑 Extracted Engineering Information")

    pages = st.session_state["document_pages"]

    for page in pages:

        with st.expander(
            f"Page {page['page']}"
        ):

            st.text(
                page["text"]
            )


# =========================================================
# 2. SEMANTIC DOCUMENT SEARCH
# =========================================================

if "vector_index" in st.session_state:

    st.header("🔎 2. Search Engineering Document")

    st.write(
        "Ask a question about the uploaded engineering document. "
        "The system will retrieve the most relevant document evidence."
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
                "Please enter a question."
            )

        else:

            with st.spinner(
                "Searching engineering document..."
            ):

                results = search_documents(
                    query=search_query,
                    chunks=st.session_state["document_chunks"],
                    index=st.session_state["vector_index"],
                    top_k=3
                )

            if not results:

                st.warning(
                    "No relevant information was found."
                )

            else:

                st.success(
                    f"Found {len(results)} relevant document sections."
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
                        f"Search distance: {result['distance']:.4f}"
                    )

                    st.divider()


# =========================================================
# 3. ITEM DEFINITION
# =========================================================

st.header("3. Item Definition")

col1, col2 = st.columns(2)


with col1:

    system = st.text_input(
        "System",
        "EPS (Electric Power Steering)"
    )

    function = st.text_area(
        "Function",
        "Provide steering assistance to the driver"
    )


with col2:

    scenario = st.text_area(
        "Operational Scenario",
        "Highway driving at 100 km/h"
    )


# =========================================================
# 4. HARA ANALYSIS
# =========================================================

st.header("4. HARA Analysis")


if st.button(
    "🔍 Analyze HARA",
    type="primary"
):

    if not system.strip():

        st.error(
            "Please enter a system."
        )

    elif not function.strip():

        st.error(
            "Please enter a function."
        )

    elif not scenario.strip():

        st.error(
            "Please enter an operational scenario."
        )

    else:

        results = analyze_malfunctions(
            system,
            function,
            scenario
        )

        st.success(
            f"Identified {len(results)} candidate malfunction scenarios."
        )

        for i, item in enumerate(
            results,
            start=1
        ):

            st.subheader(
                f"Scenario {i}: {item['malfunction']}"
            )

            col1, col2 = st.columns(2)

            with col1:

                st.markdown(
                    "### ⚠️ Potential Hazard"
                )

                st.write(
                    item["hazard"]
                )

            with col2:

                st.markdown(
                    "### 🚨 Hazardous Event"
                )

                st.write(
                    item["hazardous_event"]
                )

            st.markdown(
                "### 💡 Rationale"
            )

            st.write(
                item["rationale"]
            )

            st.divider()


# =========================================================
# 5. HARA WORKFLOW
# =========================================================

st.header("5. HARA Workflow")

st.write(
    "Document Upload → "
    "Information Extraction → "
    "Document Chunking → "
    "Semantic Embeddings → "
    "Evidence Retrieval → "
    "Function Identification → "
    "Malfunction Identification → "
    "Hazard Identification → "
    "S/E/C Assessment → "
    "ASIL Recommendation → "
    "Safety Goals → "
    "FSR/TSR → "
    "Traceability"
)