def create_chunks(pages, chunk_size=800):
    """
    Split extracted PDF text into smaller chunks.

    Each chunk keeps its source page number so that
    retrieved information can later be traced back
    to the original engineering document.
    """

    chunks = []

    for page in pages:

        text = page["text"]
        page_number = page["page"]

        words = text.split()

        for i in range(0, len(words), chunk_size):

            chunk_text = " ".join(
                words[i:i + chunk_size]
            )

            if chunk_text.strip():

                chunks.append(
                    {
                        "page": page_number,
                        "text": chunk_text
                    }
                )

    return chunks