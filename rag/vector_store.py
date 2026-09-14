from sentence_transformers import SentenceTransformer
import faiss


# =========================================================
# EMBEDDING MODEL
# =========================================================

model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


# =========================================================
# CREATE VECTOR STORE
# =========================================================

def create_vector_store(chunks):
    """
    Convert document chunks into embeddings
    and store them in a FAISS vector index.
    """

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    if not texts:
        return None

    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(
        embeddings
    )

    return index


# =========================================================
# SEARCH DOCUMENT
# =========================================================

def search_documents(
    query,
    chunks,
    index,
    top_k=3
):
    """
    Search the most relevant document chunks
    for a user query.
    """

    if index is None or not chunks:
        return []

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    distances, indices = index.search(
        query_embedding,
        min(top_k, len(chunks))
    )

    results = []

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx < 0:
            continue

        results.append(
            {
                "page": chunks[idx]["page"],
                "text": chunks[idx]["text"],
                "distance": float(distance)
            }
        )

    return results