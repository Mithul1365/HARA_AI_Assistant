from common import *

init_page("HARA AI Assistant — HARA Analysis")
page_header("HARA ANALYSIS", "HARA Analysis", "Engineering document, item definition and AI-assisted hazard identification.")

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
