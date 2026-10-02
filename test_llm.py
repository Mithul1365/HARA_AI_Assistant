import json
import urllib.request

from backend.document_processor import extract_text_from_pdf
from rag.chunker import create_chunks
from rag.vector_store import create_vector_store, search_documents


# =========================================================
# OLLAMA
# =========================================================

OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_ollama(prompt):

    data = {
        "model": "qwen3:8b",
        "prompt": prompt,
        "stream": False
    }

    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST"
    )

    with urllib.request.urlopen(request) as response:

        result = json.loads(
            response.read().decode("utf-8")
        )

    return result["response"]


# =========================================================
# LOAD ENGINEERING PDF
# =========================================================

pdf_path = "data/documents/EPS_HARA_Test_Document.pdf"

print("\nReading engineering document...")

with open(pdf_path, "rb") as pdf_file:

    pages = extract_text_from_pdf(pdf_file)


print(
    f"Extracted {len(pages)} pages."
)


# =========================================================
# CREATE CHUNKS
# =========================================================

chunks = create_chunks(pages)

print(
    f"Created {len(chunks)} chunks."
)


# =========================================================
# CREATE VECTOR STORE
# =========================================================

print("\nCreating FAISS index...")

index = create_vector_store(chunks)

print("FAISS index created.")


# =========================================================
# USER QUERY
# =========================================================

query = """
What can happen if steering assistance is lost
during highway driving?
"""


# =========================================================
# RETRIEVE ENGINEERING EVIDENCE
# =========================================================

print("\nSearching engineering document...")

results = search_documents(
    query=query,
    chunks=chunks,
    index=index,
    top_k=3
)


print(
    f"Retrieved {len(results)} relevant evidence sections."
)


# =========================================================
# BUILD EVIDENCE FOR LLM
# =========================================================

evidence_text = ""

for i, result in enumerate(results, start=1):

    evidence_text += f"""
--- Evidence {i} ---
Source: EPS_HARA_Test_Document.pdf
Page: {result["page"]}

{result["text"]}
"""


# =========================================================
# HARA PROMPT
# =========================================================

prompt = f"""
You are an automotive functional safety HARA assistant.

Your task is to analyze the engineering evidence provided below.

IMPORTANT RULES:

1. Use the provided engineering evidence as the primary source.
2. Do not invent facts that are not supported by the evidence.
3. Identify a potential malfunction.
4. Identify the potential hazard caused by the malfunction.
5. Identify the hazardous event considering the operational scenario.
6. Explain the rationale clearly.
7. Mention the source page used for the analysis.
8. This is an AI-assisted engineering analysis and must be reviewed
   by a qualified functional safety engineer.

Engineering Evidence:
{evidence_text}

User Query:
{query}

Provide the result using exactly this structure:

Potential Malfunction:
<malfunction>

Potential Hazard:
<hazard>

Hazardous Event:
<hazardous event>

Rationale:
<rationale>

Evidence:
<source file and page>
"""


# =========================================================
# ASK QWEN
# =========================================================

print("\nSending retrieved evidence to Qwen3...\n")

answer = ask_ollama(prompt)


# =========================================================
# FINAL RESULT
# =========================================================

print("=" * 60)

print("QWEN3 RAG-BASED HARA RESULT")

print("=" * 60)

print(answer)

print("=" * 60)