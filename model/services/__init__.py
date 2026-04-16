# services/__init__.py
"""
Services module for LegalT - contains extraction, ingestion, segmentation, and validation
"""
from .ingestion import extract_text
from .segmentation import segment_clauses, chunk_for_context
from .extractor import run_full_extraction
from .validator import validate_and_clean

__all__ = [
    "extract_text",
    "segment_clauses",
    "chunk_for_context",
    "run_full_extraction",
    "validate_and_clean",
]
