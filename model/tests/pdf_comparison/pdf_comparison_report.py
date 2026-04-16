#!/usr/bin/env python3
"""
PDF Extraction Comparison Report Generator

This script demonstrates the generalized PDF comparison framework by comparing
actual PDF content with extracted output from the LegalT pipeline.

Usage:
    python tests/pdf_comparison/pdf_comparison_report.py <pdf_path> <json_path>
    
Example:
    python tests/pdf_comparison/pdf_comparison_report.py tests/input/NDA.pdf logs/nda_output_after_fix.json
"""

import sys
from pathlib import Path

try:
    from tests.pdf_comparison.pdf_metrics import PDFComparator
except ModuleNotFoundError:
    # Allow direct execution from inside tests/pdf_comparison/.
    from pdf_metrics import PDFComparator


def main():
    """Run PDF comparison and generate report"""
    
    # Default to NDA if no args provided
    if len(sys.argv) < 3:
        pdf_path = "tests/input/NDA.pdf"
        json_path = "logs/nda_output_after_fix.json"
        print(f"[INFO] Using default files:")
        print(f"       PDF:  {pdf_path}")
        print(f"       JSON: {json_path}")
    else:
        pdf_path = sys.argv[1]
        json_path = sys.argv[2]
    
    # Verify files exist
    if not Path(pdf_path).exists():
        print(f"ERROR: PDF file not found: {pdf_path}")
        return 1
    
    if not Path(json_path).exists():
        print(f"ERROR: JSON file not found: {json_path}")
        return 1
    
    # Run comparison
    try:
        comparator = PDFComparator()
        
        print("\n" + "=" * 75)
        print("Extracting PDF metrics...")
        print("=" * 75)
        pdf_metrics = comparator.extract_pdf_metrics(pdf_path)
        print(f"✓ Extracted {pdf_metrics.total_pages} pages, {pdf_metrics.total_characters:,} characters")
        
        print("\n" + "=" * 75)
        print("Extracting JSON metrics...")
        print("=" * 75)
        extraction_metrics = comparator.extract_json_metrics(json_path)
        print(f"✓ Parsed {extraction_metrics.total_clauses} clauses")
        
        print("\n" + "=" * 75)
        print("Generating comparison report...")
        print("=" * 75)
        
        # Print summary
        comparator.print_summary()
        
        # Generate and display detailed report
        report = comparator.generate_report(include_clauses=True)
        
        print("\n[DETAILED REPORT]")
        print(f"Coverage: {report['metrics']['text_coverage_percent']}%")
        print(f"Validation Results: {report['validation']['passed']}/{report['validation']['total']} checks passed")
        
        print("\n[CLAUSE EXTRACTION SUMMARY]")
        if 'clauses' in report:
            print(f"Total clauses with text info: {len(report['clauses'])}")
            for i, clause in enumerate(report['clauses'][:5], 1):
                print(f"  {i}. {clause['heading'][:50]}... ({clause['text_length']} chars)")
            if len(report['clauses']) > 5:
                print(f"  ... and {len(report['clauses']) - 5} more clauses")
        
        # Overall assessment
        print("\n" + "=" * 75)
        print("EXTRACTION QUALITY ASSESSMENT")
        print("=" * 75)
        validation = report['validation']
        
        if validation['passed'] == validation['total']:
            print("✓ EXCELLENT: All validation checks passed!")
        elif validation['passed'] >= validation['total'] * 0.75:
            print("✓ GOOD: Most validation checks passed")
        elif validation['passed'] >= validation['total'] * 0.5:
            print("⚠ FAIR: Some validation checks failed")
        else:
            print("✗ POOR: Multiple validation checks failed")
        
        print(f"\nDocument: {Path(pdf_path).name}")
        print(f"Type: {extraction_metrics.document_type}")
        print(f"Subtype: {extraction_metrics.document_subtype}")
        print(f"Clauses Extracted: {extraction_metrics.total_clauses}")
        print(f"Text Coverage: {report['metrics']['text_coverage_percent']}%")
        
        return 0
        
    except Exception as e:
        print(f"ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
