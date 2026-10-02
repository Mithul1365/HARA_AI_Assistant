from pypdf import PdfReader


def extract_text_from_pdf(uploaded_file):
    """
    Extract text from an uploaded PDF.
    """

    reader = PdfReader(uploaded_file)

    pages = []

    for page_number, page in enumerate(reader.pages, start=1):

        text = page.extract_text() or ""

        if text.strip():
            pages.append(
                {
                    "page": page_number,
                    "text": text.strip()
                }
            )

    return pages