from common import *

# =========================================================
# PAGE CONFIGURATION
# =========================================================

init_page("HARA AI Assistant - HARA Analysis")

page_header(
    "HARA ANALYSIS",
    "HARA Analysis",
    "Engineering document, item definition and AI-assisted hazard identification."
)


# =========================================================
# 1. ENGINEERING DOCUMENT
# =========================================================

st.header("Engineering Document")

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
        f"Selected: {uploaded_file.name}"
    )

    if st.button(
        "Read Document",
        type="primary"
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

            st.session_state["document_pages"] = pages
            st.session_state["document_name"] = uploaded_file.name

            st.success(
                f"Document processed successfully. "
                f"{len(pages)} pages extracted."
            )

            # -------------------------------------------------
            # CREATE CHUNKS
            # -------------------------------------------------

            chunks = create_chunks(
                pages
            )

            for chunk in chunks:

                chunk["source"] = uploaded_file.name
                chunk["category"] = "uploaded_document"

            st.session_state["document_chunks"] = chunks

            # -------------------------------------------------
            # CREATE / LOAD VECTOR INDEX
            # -------------------------------------------------

            pdf_bytes = uploaded_file.getvalue()

            pdf_hash = hashlib.sha256(
                pdf_bytes
            ).hexdigest()[:16]

            cache_dir = "data/uploaded_index_cache"

            cache_path = (
                Path(cache_dir)
                / f"{pdf_hash}.pkl"
            )

            Path(cache_dir).mkdir(
                parents=True,
                exist_ok=True
            )

            vector_index = None

            if cache_path.exists():

                with st.spinner(
                    "Loading cached document search index..."
                ):

                    try:

                        with open(
                            cache_path,
                            "rb"
                        ) as cache_file:

                            cached_data = pickle.load(
                                cache_file
                            )

                        vector_index = cached_data["index"]

                        st.success(
                            "Cached document search index loaded."
                        )

                    except Exception:

                        vector_index = None

            if vector_index is None:

                with st.spinner(
                    "Creating document search index..."
                ):

                    vector_index = create_vector_store(
                        chunks
                    )

                if vector_index is not None:

                    try:

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

                        st.success(
                            "Document search index created and cached."
                        )

                    except Exception:

                        st.info(
                            "Search index created successfully."
                        )

                else:

                    st.error(
                        "Could not create the document search index."
                    )

            st.session_state["vector_index"] = vector_index
            st.session_state["document_pdf_hash"] = pdf_hash


# =========================================================
# EXTRACTED ENGINEERING INFORMATION
# =========================================================

if "document_pages" in st.session_state:

    st.subheader(
        "Extracted Engineering Information"
    )

    pages = st.session_state["document_pages"]

    for page in pages:

        with st.expander(
            f"Page {page['page']}"
        ):

            st.text(
                page["text"]
            )


# =========================================================
# 2. ITEM DEFINITION
# =========================================================

st.divider()

st.header(
    "Item Definition"
)

st.write(
    "Define the automotive item, its intended function, "
    "and the operational situation for HARA analysis."
)


# Initialize session state
if "system" not in st.session_state:
    st.session_state["system"] = ""

if "function" not in st.session_state:
    st.session_state["function"] = ""

if "scenario" not in st.session_state:
    st.session_state["scenario"] = ""

if "operating_conditions" not in st.session_state:
    st.session_state["operating_conditions"] = ""


col1, col2 = st.columns(2)


with col1:

    system = st.text_input(
        "System / Item",
        value=st.session_state["system"],
        placeholder="Example: EPS (Electric Power Steering)"
    )

    function = st.text_area(
        "Intended Function",
        value=st.session_state["function"],
        placeholder="Example: Provide steering assistance to the driver",
        height=120
    )


with col2:

    scenario = st.text_area(
        "Operational Scenario",
        value=st.session_state["scenario"],
        placeholder="Example: Highway driving at 100 km/h",
        height=120
    )

    operating_conditions = st.text_area(
        "Operating Conditions (Optional)",
        value=st.session_state["operating_conditions"],
        placeholder="Example: Dry road, daylight, normal traffic",
        height=120
    )


# Save values
st.session_state["system"] = system
st.session_state["function"] = function
st.session_state["scenario"] = scenario
st.session_state["operating_conditions"] = operating_conditions


# =========================================================
# 3. HARA ANALYSIS
# =========================================================

st.divider()

st.header(
    "HARA Analysis"
)

st.write(
    "Use retrieved engineering evidence to generate "
    "AI-assisted HARA candidates."
)


analysis_mode = st.radio(
    "Analysis Mode",
    [
        "Detailed Analysis",
        "Quick Summary"
    ],
    horizontal=True
)

summary_mode = (
    analysis_mode == "Quick Summary"
)


if st.button(
    "Analyze HARA",
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

        evidence_results = []

        evidence_source = ""

        # -------------------------------------------------
        # PRIMARY SOURCE: UPLOADED DOCUMENT
        # -------------------------------------------------

        uploaded_document_available = (
            "document_chunks" in st.session_state
            and "vector_index" in st.session_state
            and st.session_state["vector_index"] is not None
        )

        if uploaded_document_available:

            with st.spinner(
                "Retrieving evidence from uploaded engineering document..."
            ):

                evidence_results = search_documents(
                    query=query,
                    chunks=st.session_state["document_chunks"],
                    index=st.session_state["vector_index"],
                    top_k=5
                )

            evidence_source = (
                "Uploaded Engineering Document: "
                + st.session_state.get(
                    "document_name",
                    "PDF"
                )
            )


        # -------------------------------------------------
        # FALLBACK: AUTOMOTIVE KNOWLEDGE BASE
        # -------------------------------------------------

        if not evidence_results:

            with st.spinner(
                "Loading automotive engineering knowledge base..."
            ):

                kb_chunks, kb_index = get_knowledge_base()

            if kb_index is not None and kb_chunks:

                with st.spinner(
                    "Searching automotive engineering knowledge base..."
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
                        "page": result.get(
                            "page",
                            "-"
                        ),
                        "text": result.get(
                            "text",
                            ""
                        )
                    }
                )


            # -------------------------------------------------
            # DISPLAY ENGINEERING EVIDENCE
            # -------------------------------------------------

            with st.expander(
                "Engineering Evidence Used by AI",
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
                        f"- Page {result.get('page', '-')} "
                        f"- Relevance {result.get('score', 0):.4f}"
                    )

                    st.write(
                        result.get(
                            "text",
                            ""
                        )
                    )

                    st.divider()


            # -------------------------------------------------
            # QWEN ANALYSIS
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

            st.session_state["hara_answer"] = answer
            st.session_state["hara_evidence"] = evidence_results

            st.session_state["hara_system"] = system
            st.session_state["hara_function"] = function
            st.session_state["hara_scenario"] = scenario


            # Clear downstream results
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
                "traceability_rows",
                None
            )


# =========================================================
# DISPLAY HARA RESULT
# =========================================================

if "hara_answer" in st.session_state:

    st.divider()

    st.success(
        "HARA analysis generated successfully."
    )

    answer = st.session_state["hara_answer"]

    st.subheader(
        "AI-Assisted HARA Result"
    )

    st.write(
        answer
    )


    # -------------------------------------------------
    # CONTINUE TO ASIL
    # -------------------------------------------------

    st.divider()

    st.success(
        "HARA analysis is ready for the next engineering step."
    )

    if st.button(
        "Continue to ASIL Assessment",
        type="primary"
    ):

        st.switch_page(
            "pages/2_ASIL_Assessment.py"
        )
