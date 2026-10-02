from pathlib import Path

from backend.document_processor import extract_text_from_pdf
from rag.chunker import create_chunks


KNOWLEDGE_BASE_DIR = Path(
    "data/knowledge_base"
)


def load_knowledge_base():
    """
    Read all PDF files from the knowledge base
    and convert them into chunks.

    Each chunk keeps:
    - source document
    - category
    - page number
    - text
    """

    all_chunks = []

    pdf_files = list(
        KNOWLEDGE_BASE_DIR.rglob("*.pdf")
    )

    for pdf_path in pdf_files:

        category = pdf_path.parent.name

        try:

            with open(
                pdf_path,
                "rb"
            ) as pdf_file:

                pages = extract_text_from_pdf(
                    pdf_file
                )

            chunks = create_chunks(
                pages
            )

            for chunk in chunks:

                chunk["source"] = (
                    pdf_path.name
                )

                chunk["category"] = (
                    category
                )

                all_chunks.append(
                    chunk
                )

        except Exception as e:

            print(
                f"Could not read "
                f"{pdf_path}: {e}"
            )

    return all_chunks