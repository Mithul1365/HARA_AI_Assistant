from sentence_transformers import SentenceTransformer
import faiss
import re
import streamlit as st


# =========================================================
# EMBEDDING MODEL
# =========================================================

@st.cache_resource(show_spinner=False)
def get_model():
    """
    Load the embedding model once and reuse it
    across Streamlit reruns.
    """
    return SentenceTransformer(
        "all-MiniLM-L6-v2"
    )


# =========================================================
# CREATE VECTOR STORE
# =========================================================

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


# =========================================================
# TEXT NORMALIZATION
# =========================================================

def _normalize_text(text):
    """
    Normalize text for reliable lexical matching.
    """
    text = str(text).lower()

    # Normalize common automotive abbreviations/variants.
    replacements = {
        "bcm": " body control module ",
        "door-lock": " door lock ",
        "doorlocking": " door locking ",
        "central-locking": " central locking ",
        "central-lock": " central lock ",
    }

    for old, new in replacements.items():
        text = text.replace(old, new)

    text = re.sub(r"[^a-z0-9]+", " ", text)

    return re.sub(r"\s+", " ", text).strip()


def _tokens(text):
    """
    Return useful tokens while ignoring very common words.
    """
    stop_words = {
        "the", "and", "for", "with", "that", "this",
        "from", "into", "while", "when", "where",
        "what", "which", "their", "there", "have",
        "has", "are", "was", "were", "been", "being",
        "will", "would", "could", "should", "can",
        "may", "must", "system", "function", "vehicle",
        "operation", "operating", "condition"
    }

    return {
        token
        for token in _normalize_text(text).split()
        if len(token) >= 3 and token not in stop_words
    }


# =========================================================
# AUTOMOTIVE DOMAIN DETECTION
# =========================================================

def detect_category(query):
    """
    Detect the most likely automotive domain
    from the user's query.
    """

    query = _normalize_text(query)

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
            "body electronic",
            "body control",
            "body control module",
            "bcm",
            "lighting",
            "airbag",
            "door",
            "door lock",
            "door locking",
            "central lock",
            "central locking",
            "window",
            "wiper",
            "horn",
            "mirror",
            "seat",
            "occupant"
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

            if keyword in query:
                detected_categories.append(
                    category
                )
                break

    return detected_categories


# =========================================================
# LEXICAL RELEVANCE
# =========================================================

def _lexical_score(query, text):
    """
    Calculate keyword/phrase overlap between the HARA query
    and a document chunk.

    This complements semantic FAISS search so that a chunk
    containing exact engineering terms such as
    'door locking' or 'body control module' can outrank
    semantically similar but unrelated content.
    """

    query_normalized = _normalize_text(query)
    text_normalized = _normalize_text(text)

    query_tokens = _tokens(query_normalized)
    text_tokens = _tokens(text_normalized)

    if not query_tokens or not text_tokens:
        return 0.0

    overlap = query_tokens.intersection(text_tokens)

    token_score = len(overlap) / len(query_tokens)

    # Stronger boost for meaningful engineering phrases.
    phrase_terms = [
        "body control module",
        "central locking",
        "central lock",
        "door locking",
        "door lock",
        "door",
        "lighting",
        "airbag",
        "bcm",
        "wiper",
        "occupant",
        "sensor",
        "radar",
        "camera",
        "steering",
        "braking"
    ]

    phrase_hits = sum(
        1
        for phrase in phrase_terms
        if phrase in query_normalized
        and phrase in text_normalized
    )

    phrase_score = min(
        phrase_hits * 0.20,
        0.60
    )

    return min(
        token_score * 0.60 + phrase_score,
        1.0
    )


# =========================================================
# SEARCH DOCUMENTS
# =========================================================

def search_documents(
    query,
    chunks,
    index,
    top_k=3,
    min_relevance=0.25
):
    """
    Perform hybrid automotive-domain-aware search.

    Retrieval uses:
      1. FAISS semantic similarity
      2. Exact/keyword engineering-term overlap
      3. Automotive domain matching
      4. Source/category boosts

    This prevents generic but semantically similar PDF pages
    such as disclaimers or unrelated sensor articles from
    dominating the HARA evidence.
    """

    if (
        index is None
        or not chunks
    ):
        return []

    # -----------------------------------------------------
    # GET CACHED EMBEDDING MODEL
    # -----------------------------------------------------

    model = get_model()

    # -----------------------------------------------------
    # CREATE QUERY EMBEDDING
    # -----------------------------------------------------

    query_embedding = model.encode(
        [query],
        convert_to_numpy=True
    )

    # -----------------------------------------------------
    # FAISS CANDIDATE SEARCH
    # -----------------------------------------------------

    candidate_k = min(
        max(top_k * 10, 20),
        len(chunks)
    )

    distances, indices = index.search(
        query_embedding,
        candidate_k
    )

    # -----------------------------------------------------
    # DETECT AUTOMOTIVE DOMAIN
    # -----------------------------------------------------

    detected_categories = detect_category(
        query
    )

    candidates = []

    # -----------------------------------------------------
    # PROCESS SEARCH RESULTS
    # -----------------------------------------------------

    for distance, idx in zip(
        distances[0],
        indices[0]
    ):

        if idx < 0:
            continue

        distance = float(distance)

        # -------------------------------------------------
        # CONVERT FAISS DISTANCE TO RELEVANCE
        # -------------------------------------------------

        relevance = 1 / (
            1 + distance
        )

        if relevance < min_relevance:
            continue

        chunk = chunks[idx]

        text = chunk.get(
            "text",
            ""
        )

        category = chunk.get(
            "category",
            "Unknown"
        )

        source = chunk.get(
            "source",
            "Unknown"
        )

        # -------------------------------------------------
        # LEXICAL ENGINEERING RELEVANCE
        # -------------------------------------------------

        lexical_score = _lexical_score(
            query,
            text
        )

        # -------------------------------------------------
        # DOMAIN MATCH
        # -------------------------------------------------

        category_match = (
            bool(detected_categories)
            and category in detected_categories
        )

        # -------------------------------------------------
        # GENERIC / LOW-VALUE CONTENT PENALTY
        # -------------------------------------------------

        normalized_text = _normalize_text(text)

        disclaimer_penalty = 0.0

        disclaimer_terms = [
            "important notice and disclaimer",
            "disclaims all warranties",
            "terms of sale",
            "copyright",
            "mailing address"
        ]

        disclaimer_hits = sum(
            1
            for term in disclaimer_terms
            if term in normalized_text
        )

        if disclaimer_hits:
            disclaimer_penalty = min(
                0.30,
                disclaimer_hits * 0.15
            )

        # -------------------------------------------------
        # COMBINED SCORE
        # -------------------------------------------------

        score = (
            relevance * 0.45
            + lexical_score * 0.40
        )

        if category_match:
            score += 0.20

        # Source/category naming can provide a small hint,
        # but should not overpower actual document content.
        source_normalized = _normalize_text(source)

        for detected_category in detected_categories:

            category_terms = {
                "body_safety": [
                    "body",
                    "electronics",
                    "lighting"
                ],
                "DMS": [
                    "driver",
                    "monitoring"
                ],
                "steering": [
                    "steering"
                ],
                "braking": [
                    "brake",
                    "braking"
                ],
                "ADAS": [
                    "adas"
                ],
                "perception": [
                    "radar",
                    "sensor",
                    "camera"
                ],
                "EV": [
                    "battery",
                    "bms",
                    "electric"
                ],
                "powertrain": [
                    "powertrain",
                    "engine",
                    "motor"
                ],
                "networks": [
                    "network",
                    "can",
                    "ethernet",
                    "gateway"
                ],
                "automated_driving": [
                    "autonomous",
                    "automated"
                ]
            }.get(
                detected_category,
                []
            )

            if any(
                term in source_normalized
                for term in category_terms
            ):
                score += 0.05
                break

        score -= disclaimer_penalty

        # -------------------------------------------------
        # STORE CANDIDATE
        # -------------------------------------------------

        candidates.append(
            {
                "page": chunk["page"],
                "text": text,
                "distance": distance,
                "relevance": relevance,
                "lexical_score": lexical_score,
                "score": score,
                "source": source,
                "category": category
            }
        )

    # -----------------------------------------------------
    # SORT BY HYBRID SCORE
    # -----------------------------------------------------

    candidates.sort(
        key=lambda x: x["score"],
        reverse=True
    )

    # -----------------------------------------------------
    # RETURN TOP RESULTS
    # -----------------------------------------------------

    return candidates[:top_k]
