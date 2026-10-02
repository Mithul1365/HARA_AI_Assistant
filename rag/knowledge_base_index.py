from pathlib import Path
import pickle

from rag.knowledge_base_loader import load_knowledge_base
from rag.vector_store import create_vector_store


INDEX_FILE = Path(
    "data/knowledge_base/faiss_index.pkl"
)


def build_and_save_knowledge_base_index():
    """
    Build the knowledge-base chunks and FAISS index,
    then save them to disk for reuse.
    """

    print("Loading knowledge base...")

    chunks = load_knowledge_base()

    if not chunks:
        raise RuntimeError(
            "No knowledge-base documents were found."
        )

    print(
        f"Loaded {len(chunks)} chunks."
    )

    print(
        "Creating FAISS index..."
    )

    index = create_vector_store(
        chunks
    )

    if index is None:
        raise RuntimeError(
            "Could not create FAISS index."
        )

    INDEX_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    data = {
        "chunks": chunks,
        "index": index
    }

    with open(
        INDEX_FILE,
        "wb"
    ) as file:

        pickle.dump(
            data,
            file
        )

    print(
        f"Knowledge-base index saved to: "
        f"{INDEX_FILE}"
    )

    return chunks, index


def load_saved_knowledge_base_index():
    """
    Load the previously saved knowledge-base
    chunks and FAISS index.
    """

    if not INDEX_FILE.exists():
        return None, None

    with open(
        INDEX_FILE,
        "rb"
    ) as file:

        data = pickle.load(
            file
        )

    chunks = data.get(
        "chunks",
        []
    )

    index = data.get(
        "index"
    )

    return chunks, index