# app/services/ingestion.py
import importlib
import re
from pathlib import Path

import docx
import pdfplumber

def extract_text(file_path: str) -> str:
    """
    Extracts clean text from PDF, DOCX, or TXT files.
    Returns normalized plain text suitable for LLM input.
    """
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf(file_path)
    elif suffix in [".docx", ".doc"]:
        return _extract_docx(file_path)
    elif suffix == ".txt":
        return path.read_text(encoding="utf-8", errors="ignore")
    else:
        raise ValueError(f"Unsupported file type: {suffix}")


def extract_raw_pages(file_path: str) -> list[dict[str, object]]:
    """Extract page-preserving text blocks for stage-by-stage analysis."""
    path = Path(file_path)
    suffix = path.suffix.lower()

    if suffix == ".pdf":
        return _extract_pdf_pages(file_path)
    if suffix in [".docx", ".doc"]:
        text = _extract_docx(file_path)
        return [{"page_num": 1, "text": text}]
    if suffix == ".txt":
        text = path.read_text(encoding="utf-8", errors="replace")
        return [{"page_num": 1, "text": _clean_text(text)}]
    raise ValueError(f"Unsupported file type: {suffix}")

def _extract_pdf(path: str) -> str:
    text_parts = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    cleaned = _clean_text("\n".join(text_parts))
    if cleaned:
        return cleaned

    # Fallback parser for PDFs where pdfplumber cannot read the text layer.
    try:
        pypdf = importlib.import_module("pypdf")
        PdfReader = getattr(pypdf, "PdfReader")

        reader = PdfReader(path)
        fallback_parts = []
        for page in reader.pages:
            page_text = page.extract_text() or ""
            if page_text.strip():
                fallback_parts.append(page_text)
        cleaned_fallback = _clean_text("\n".join(fallback_parts))
        if cleaned_fallback:
            return cleaned_fallback
    except Exception:
        pass

    raise ValueError(
        "No extractable text found in PDF. The file may be image/scanned; "
        "run OCR first or provide a text-based PDF."
    )


def _extract_pdf_pages(path: str) -> list[dict[str, object]]:
    pages: list[dict[str, object]] = []
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append({"page_num": index, "text": _clean_text(page_text)})

    if pages:
        return pages

    try:
        pypdf = importlib.import_module("pypdf")
        PdfReader = getattr(pypdf, "PdfReader")
        reader = PdfReader(path)
        for index, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if page_text.strip():
                pages.append({"page_num": index, "text": _clean_text(page_text)})
    except Exception:
        pass

    if pages:
        return pages

    raise ValueError(
        "No extractable text found in PDF. The file may be image/scanned; "
        "run OCR first or provide a text-based PDF."
    )

def _extract_docx(path: str) -> str:
    doc = docx.Document(path)
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return _clean_text("\n".join(paragraphs))

def _clean_text(text: str) -> str:
    """Normalize whitespace, remove headers/footers artifacts."""
    text = re.sub(r'\n{3,}', '\n\n', text)        # collapse excess newlines
    text = re.sub(r'[ \t]{2,}', ' ', text)         # collapse spaces
    text = re.sub(r'Page \d+ of \d+', '', text)    # remove page numbers
    return text.strip()