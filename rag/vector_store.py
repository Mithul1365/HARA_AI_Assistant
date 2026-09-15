from sentence_transformers import SentenceTransformer
import faiss
import re


_model = None


def get_model():
    """
    Load the embedding model only when needed.
    """

    global _model

    if _model is None:
        _model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )

    return _model


def create_vector_store(chunks):
    """
    Create a FAISS semantic search index
    from document chunks.
    """

    texts = [
        chunk["text"]
        for chunk in chunks
    ]

    if not texts:
        return None

    model = get_model()

    embeddings = model.encode(
        texts,
        convert_to_numpy=True
    )

    dimension = embeddings.shape[1]

    index = faiss.IndexFlatL2(
        dimension
    )

    index.add(embeddings)

    return index


def detect_category(query):
    """
    Detect the most likely automotive domain
    from the user's query.
    """

    query = query.lower()

    category_keywords = {

        "DMS": [
            "driver monitoring",
            "driver attention",
            "driver distraction",
            "drowsiness",
            "driver fatigue",
            "driver monitoring system",
            "driver state"
        ],

        "steering": [
            "steering",
            "electric power steering",
            "eps",
            "steering assistance",
            "steering assist"
        ],

        "braking": [
            "brake",
            "braking",
            "electronic braking",
            "brake system",
            "emergency braking"
        ],

        "ADAS": [
            "adas",
            "adaptive cruise",
            "lane keeping",
            "lane departure",
            "automatic emergency braking"
        ],

        "perception": [
            "radar",
            "camera",
            "lidar",
            "sensor",
            "object detection",
            "environment perception"
        ],

        "EV": [
            "battery",
            "bms",
            "battery management",
            "pyrofuse",
            "electric vehicle",
            "high voltage"
        ],

        "powertrain": [
            "powertrain",
            "engine",
            "motor control",
            "traction",
            "inverter"
        ],

        "body_safety": [
            "body electronics",
            "lighting",
            "airbag",
            "body control"
        ],

        "networks": [
            "gateway",
            "can",
            "can bus",
            "automotive network",
            "ethernet",
            "communication"
        ],

        "automated_driving": [
            "autonomous driving",
            "automated driving",
            "sensor fusion",
            "self driving",
            "autonomous vehicle"
        ]
    }

    detected_categories = []

    for category, keywords in category_keywords.items():

        for keyword in keywords:

            if f" {keyword} " in f" {query} ":
                detected_categories.append(
                    category
                )
                break

    return detected_categories


def search_documents(
    query,
    chunks,
    index,
    top_k=3,
    min_relevance=0.25
):
    """
    Perform semantic search and automotive
    domain-aware filtering.

    The system first retrieves semantic candidates
    using FAISS and then filters them according
    to the detected automotive domain.
    """

    if (
        index is None
        or not chunks
    ):
        return []

    model = get_model()

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    # Retrieve more candidates first so that
    # domain filtering has enough candidates to work with.
    candidate_k = min(
        max(top_k * 5, 10),
        len(chunks)
    )

    distances, indices = index.search(
        query_embedding,
        candidate_k
    )

    detected_categories = detect_category(
        query
    )

    candidates = []

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx < 0:
            continue

        distance = float(distance)

        # Convert FAISS distance into a simple
        # relevance score.
        relevance = 1 / (
            1 + distance
        )

        if relevance < min_relevance:
            continue

        category = chunks[idx].get(
            "category",
            "Unknown"
        )

        # -------------------------------------------------
        # DOMAIN FILTER
        # -------------------------------------------------
        #
        # If the query clearly identifies an automotive
        # domain, only retrieve evidence from that domain.
        #
        # Example:
        #
        # DMS query -> DMS evidence
        # Steering query -> steering evidence
        # Braking query -> braking evidence
        #
        if detected_categories:

            if category not in detected_categories:
                continue

        score = relevance

        # -------------------------------------------------
        # CATEGORY BOOST
        # -------------------------------------------------

        if category in detected_categories:
            score += 0.30

        # -------------------------------------------------
        # SOURCE BOOST
        # -------------------------------------------------

        source = chunks[idx].get(
            "source",
            ""
        ).lower()

        for detected_category in detected_categories:

            if detected_category.lower() in source:
                score += 0.10

        candidates.append(
            {
                "page": chunks[idx]["page"],
                "text": chunks[idx]["text"],
                "distance": distance,
                "relevance": relevance,
                "score": score,
                "source": chunks[idx].get(
                    "source",
                    "Unknown"
                ),
                "category": category
            }
        )

    # Sort by combined relevance score.
    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    return candidates[:top_k]