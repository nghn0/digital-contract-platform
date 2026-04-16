"""
Generalized PDF Extraction Metrics and Comparison Module

This module provides reusable metrics for comparing actual PDF content
with extracted output from the LegalT pipeline. Works with any document type.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class PDFMetrics:
    """Metrics for a PDF document"""
    file_path: str
    total_pages: int
    total_characters: int
    total_text: str
    page_contents: List[str]


@dataclass
class ExtractionMetrics:
    """Metrics for extracted document output"""
    json_path: str
    total_clauses: int
    document_type: str
    document_subtype: str
    clause_tags_distribution: Dict[str, int]
    text_coverage_percent: float
    average_clause_length: int
    clauses: List[Dict[str, Any]]


class PDFComparator:
    """Generic PDF and extraction comparison tool"""
    
    def __init__(self):
        self.pdf_metrics: Optional[PDFMetrics] = None
        self.extraction_metrics: Optional[ExtractionMetrics] = None
    
    def extract_pdf_metrics(self, pdf_path: str) -> PDFMetrics:
        """Extract metrics from a PDF file"""
        try:
            import pdfplumber
        except ImportError:
            raise ImportError("pdfplumber required. Install with: pip install pdfplumber")
        
        with pdfplumber.open(pdf_path) as pdf:
            pages = pdf.pages
            page_contents = []
            all_text = ""
            
            for page in pages:
                text = page.extract_text()
                page_contents.append(text)
                all_text += text + "\n"
            
            self.pdf_metrics = PDFMetrics(
                file_path=pdf_path,
                total_pages=len(pages),
                total_characters=len(all_text),
                total_text=all_text,
                page_contents=page_contents
            )
            return self.pdf_metrics
    
    def extract_json_metrics(self, json_path: str) -> ExtractionMetrics:
        """Extract metrics from LegalT JSON output"""
        with open(json_path) as f:
            data = json.load(f)
        
        clauses = data.get('clauses', [])
        total_chars = sum(len(c.get('text', '')) for c in clauses)
        
        # Count clause tags
        tag_counts: Dict[str, int] = {}
        for clause in clauses:
            tags = clause.get('tags', [])
            for tag in tags:
                if 'source_section:' in tag:
                    section = tag.replace('source_section:', '')
                    tag_counts[section] = tag_counts.get(section, 0) + 1
        
        # Calculate text coverage
        pdf_chars = len(self.pdf_metrics.total_text) if self.pdf_metrics else 0
        text_coverage = (total_chars / pdf_chars * 100) if pdf_chars > 0 else 0
        
        avg_length = total_chars // len(clauses) if clauses else 0
        
        self.extraction_metrics = ExtractionMetrics(
            json_path=json_path,
            total_clauses=len(clauses),
            document_type=data.get('document_profile', {}).get('document_type', 'Unknown'),
            document_subtype=data.get('document_profile', {}).get('subtype', 'Unknown'),
            clause_tags_distribution=tag_counts,
            text_coverage_percent=text_coverage,
            average_clause_length=avg_length,
            clauses=clauses
        )
        return self.extraction_metrics
    
    def generate_report(self, include_clauses: bool = False) -> Dict[str, Any]:
        """Generate comprehensive comparison report"""
        if not self.pdf_metrics or not self.extraction_metrics:
            raise ValueError("Must extract PDF and JSON metrics first")
        
        pdf_m = self.pdf_metrics
        ext_m = self.extraction_metrics
        
        # Identify document content areas
        pdf_content_preview = pdf_m.total_text[:500]
        
        # Build report
        report = {
            "document": {
                "file": pdf_m.file_path,
                "pages": pdf_m.total_pages,
                "total_characters": pdf_m.total_characters,
                "preview": pdf_content_preview
            },
            "extraction": {
                "json_file": ext_m.json_path,
                "total_clauses": ext_m.total_clauses,
                "document_type": ext_m.document_type,
                "document_subtype": ext_m.document_subtype,
            },
            "metrics": {
                "text_coverage_percent": round(ext_m.text_coverage_percent, 1),
                "average_clause_length": ext_m.average_clause_length,
                "clause_tags_distribution": ext_m.clause_tags_distribution,
            },
            "validation": self._validate_extraction(pdf_m, ext_m)
        }
        
        if include_clauses:
            report["clauses"] = [
                {
                    "heading": c.get('heading', 'N/A'),
                    "tags": c.get('tags', []),
                    "text_length": len(c.get('text', ''))
                }
                for c in ext_m.clauses
            ]
        
        return report
    
    def _validate_extraction(self, pdf_m: PDFMetrics, ext_m: ExtractionMetrics) -> Dict[str, Any]:
        """Validate extraction quality"""
        validations = {
            "content_coverage": ext_m.text_coverage_percent >= 90,  # 90% threshold
            "clause_count_reasonable": ext_m.total_clauses >= 3,  # At least 3 clauses
            "sections_tagged": len(ext_m.clause_tags_distribution) > 0,
            "document_classified": ext_m.document_type != "Unknown",
        }
        
        # Check for content-specific validations
        validations["hybrid_detected"] = "Hybrid" in ext_m.document_subtype if ext_m.document_subtype else False
        
        return {
            "checks": validations,
            "passed": sum(1 for v in validations.values() if v),
            "total": len(validations)
        }
    
    def print_summary(self) -> None:
        """Print a human-readable comparison summary"""
        if not self.pdf_metrics or not self.extraction_metrics:
            raise ValueError("Must extract PDF and JSON metrics first")
        
        pdf_m = self.pdf_metrics
        ext_m = self.extraction_metrics
        
        print("\n" + "=" * 75)
        print(f"PDF EXTRACTION COMPARISON: {Path(pdf_m.file_path).name}")
        print("=" * 75)
        
        print(f"\n[ACTUAL PDF]")
        print(f"  Pages:             {pdf_m.total_pages}")
        print(f"  Total Characters:  {pdf_m.total_characters:,}")
        
        print(f"\n[EXTRACTION RESULTS]")
        print(f"  Total Clauses:     {ext_m.total_clauses}")
        print(f"  Document Type:     {ext_m.document_type}")
        print(f"  Subtype:           {ext_m.document_subtype}")
        
        print(f"\n[METRICS]")
        print(f"  Text Coverage:     {ext_m.text_coverage_percent:.1f}%")
        print(f"  Avg Clause Length: {ext_m.average_clause_length} chars")
        
        if ext_m.clause_tags_distribution:
            print(f"\n[SECTION BREAKDOWN]")
            for section, count in sorted(ext_m.clause_tags_distribution.items()):
                print(f"  {section:20s}: {count:2d} clauses")
        
        # Validation summary
        val = self.extract_json_metrics(ext_m.json_path).clause_tags_distribution
        report = self.generate_report()
        checks = report['validation']['checks']
        
        print(f"\n[VALIDATION CHECKS]")
        for check_name, passed in checks.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            clean_name = check_name.replace('_', ' ').title()
            print(f"  {status}: {clean_name}")
        
        print("\n" + "=" * 75 + "\n")


def compare_pdf_and_extraction(
    pdf_path: str, 
    json_path: str,
    include_clauses: bool = False
) -> Dict[str, Any]:
    """
    Convenience function for quick PDF vs extraction comparison
    
    Args:
        pdf_path: Path to the PDF file
        json_path: Path to the extracted JSON output
        include_clauses: Whether to include detailed clause info in report
        
    Returns:
        Comparison report dictionary
    """
    comparator = PDFComparator()
    comparator.extract_pdf_metrics(pdf_path)
    comparator.extract_json_metrics(json_path)
    comparator.print_summary()
    return comparator.generate_report(include_clauses=include_clauses)
