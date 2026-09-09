"""
Text extraction from uploaded resume files.

Phase 1 of the pipeline: turn a PDF or DOCX file into plain text.
No chunking or embedding happens here — that comes in later phases.
Keeping this isolated makes it easy to test extraction quality on its own,
since bad extraction here would silently wreck every phase downstream.
"""

import io

from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Pull the text layer out of a PDF, page by page.

    Note: this only works for PDFs that have a real text layer (i.e. the
    text was typed, not scanned as an image). A scanned resume would need
    OCR, which is out of scope for this version — if extraction comes back
    empty or garbled, that's the most likely reason.
    """
    reader = PdfReader(io.BytesIO(file_bytes))
    pages_text = []
    for page in reader.pages:
        pages_text.append(page.extract_text() or "")
    return "\n".join(pages_text)


def extract_text_from_docx(file_bytes: bytes) -> str:
    """
    Pull text out of a DOCX file, paragraph by paragraph.

    We join paragraphs with newlines (rather than spaces) because in the
    next phase we split resume text into chunks largely by line — so
    preserving line boundaries here matters even though it doesn't matter
    for this phase's output.
    """
    document = Document(io.BytesIO(file_bytes))
    paragraphs = [p.text for p in document.paragraphs]
    return "\n".join(paragraphs)


def extract_text(filename: str, file_bytes: bytes) -> str:
    """
    Dispatch to the right extractor based on file extension.

    Raises ValueError for unsupported file types so the API layer can
    turn that into a clean 400 response instead of a confusing crash.
    """
    lowercase_name = filename.lower()
    if lowercase_name.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    elif lowercase_name.endswith(".docx"):
        return extract_text_from_docx(file_bytes)
    else:
        raise ValueError(
            f"Unsupported file type for '{filename}'. Only .pdf and .docx are supported."
        )
