"""
PDF Comparison Test Suite

This package provides generalized metrics and comparison tools for validating
LegalT extraction accuracy against actual PDF content.

Usage:
    from tests.pdf_comparison.pdf_metrics import PDFComparator
    
    comparator = PDFComparator()
    comparator.extract_pdf_metrics('path/to/document.pdf')
    comparator.extract_json_metrics('path/to/output.json')
    comparator.print_summary()

See test_pdf_extraction_metrics.py for detailed test cases.
"""

from tests.pdf_comparison.pdf_metrics import (
    PDFComparator,
    PDFMetrics,
    ExtractionMetrics,
    compare_pdf_and_extraction,
)

__all__ = [
    "PDFComparator",
    "PDFMetrics",
    "ExtractionMetrics",
    "compare_pdf_and_extraction",
]
