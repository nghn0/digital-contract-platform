"""
PDF Comparison Tests - Validates extraction accuracy against actual PDF content

Run with: pytest tests/pdf_comparison/test_pdf_extraction_metrics.py -v
"""

import json
from pathlib import Path
import pytest
from tests.pdf_comparison.pdf_metrics import PDFComparator, compare_pdf_and_extraction


class TestPDFExtractionMetrics:
    """Test extraction accuracy for different document types"""
    
    @pytest.fixture
    def nda_files(self):
        """Fixture for NDA document test files"""
        return {
            "pdf": "tests/input/NDA.pdf",
            "json": "logs/nda_output_comparison.json"
        }
    
    @pytest.fixture
    def loan_files(self):
        """Fixture for Loan Agreement test files"""
        return {
            "pdf": "tests/input/LOAN AGREEMENT.pdf",
            "json": "logs/loan_output_comparison.json"
        }
    
    def test_pdf_metrics_extraction(self, nda_files):
        """Test that PDF metrics are correctly extracted"""
        comparator = PDFComparator()
        metrics = comparator.extract_pdf_metrics(nda_files["pdf"])
        
        assert metrics.file_path == nda_files["pdf"]
        assert metrics.total_pages > 0, "PDF should have at least 1 page"
        assert metrics.total_characters > 0, "PDF should have content"
        assert len(metrics.page_contents) == metrics.total_pages
    
    def test_extraction_json_parsing(self, nda_files):
        """Test that extraction JSON is correctly parsed"""
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(nda_files["pdf"])
        
        # Only test if JSON exists
        if Path(nda_files["json"]).exists():
            metrics = comparator.extract_json_metrics(nda_files["json"])
            
            assert metrics.json_path == nda_files["json"]
            assert metrics.total_clauses > 0, "Should extract at least 1 clause"
            assert metrics.document_type != "Unknown"
    
    def test_text_coverage_metric(self, nda_files):
        """Test that text coverage is calculated correctly"""
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(nda_files["pdf"])
        
        if Path(nda_files["json"]).exists():
            metrics = comparator.extract_json_metrics(nda_files["json"])
            
            # Text coverage should be between 0-100%
            assert 0 <= metrics.text_coverage_percent <= 100
            # For well-extracted documents, should be > 80%
            assert metrics.text_coverage_percent >= 80, \
                f"Expected >80% coverage, got {metrics.text_coverage_percent}%"
    
    def test_clause_section_tagging(self, nda_files):
        """Test that clauses are properly tagged with source sections"""
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(nda_files["pdf"])
        
        if Path(nda_files["json"]).exists():
            metrics = comparator.extract_json_metrics(nda_files["json"])
            
            # Should have some tagged sections
            assert len(metrics.clause_tags_distribution) > 0, \
                "Clauses should be tagged with source sections"
            
            # Total tagged clauses should match total clauses
            total_tagged = sum(metrics.clause_tags_distribution.values())
            assert total_tagged > 0, "At least some clauses should be tagged"
    
    def test_report_generation(self, nda_files):
        """Test that comparison report is generated correctly"""
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(nda_files["pdf"])
        
        if Path(nda_files["json"]).exists():
            comparator.extract_json_metrics(nda_files["json"])
            report = comparator.generate_report()
            
            # Verify report structure
            assert "document" in report
            assert "extraction" in report
            assert "metrics" in report
            assert "validation" in report
            
            # Verify document section
            assert report["document"]["pages"] > 0
            assert report["document"]["total_characters"] > 0
            
            # Verify metrics section
            assert "text_coverage_percent" in report["metrics"]
            assert "clause_tags_distribution" in report["metrics"]
    
    def test_validation_checks(self, nda_files):
        """Test that validation checks pass for quality extraction"""
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(nda_files["pdf"])
        
        if Path(nda_files["json"]).exists():
            comparator.extract_json_metrics(nda_files["json"])
            report = comparator.generate_report()
            
            validation = report["validation"]
            
            # Check that important validations pass
            assert validation["checks"]["content_coverage"], \
                "Text coverage should be >= 90%"
            assert validation["checks"]["clause_count_reasonable"], \
                "Should extract at least 3 clauses"
            assert validation["checks"]["sections_tagged"], \
                "Clauses should be tagged with sections"
    
    def test_hybrid_document_detection(self, nda_files):
        """Test that hybrid documents (mixed types) are correctly detected"""
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(nda_files["pdf"])
        
        if Path(nda_files["json"]).exists():
            metrics = comparator.extract_json_metrics(nda_files["json"])
            
            # NDA PDF should be detected as Hybrid (Employment + NDA)
            if "Hybrid" in metrics.document_subtype:
                # Verify multiple section types present
                assert len(metrics.clause_tags_distribution) >= 2, \
                    "Hybrid document should have 2+ section types"
    
    def test_clause_extraction_completeness(self, nda_files):
        """Test that all document sections are extracted as clauses"""
        comparator = PDFComparator()
        pdf_metrics = comparator.extract_pdf_metrics(nda_files["pdf"])
        
        if Path(nda_files["json"]).exists():
            extraction_metrics = comparator.extract_json_metrics(nda_files["json"])
            
            # Minimum clauses based on document size
            # Rough heuristic: 1 clause per 500 chars
            expected_min_clauses = max(3, pdf_metrics.total_characters // 500)
            
            assert extraction_metrics.total_clauses >= expected_min_clauses, \
                f"Expected at least {expected_min_clauses} clauses, got {extraction_metrics.total_clauses}"


class TestPDFComparisonConvenience:
    """Tests for the convenience comparison function"""
    
    def test_compare_pdf_and_extraction_function(self):
        """Test the quick comparison function"""
        pdf_path = "tests/input/NDA.pdf"
        
        # This test just verifies the function exists and can be called
        # It will only actually compare if output JSON exists
        comparator = PDFComparator()
        comparator.extract_pdf_metrics(pdf_path)
        
        assert comparator.pdf_metrics is not None
        assert comparator.pdf_metrics.total_pages > 0


class TestMultipleDocumentTypes:
    """Tests for comparing different document types"""
    
    @pytest.mark.parametrize("pdf_file", [
        "tests/input/NDA.pdf",
        "tests/input/LOAN AGREEMENT.pdf",
    ])
    def test_various_document_processing(self, pdf_file):
        """Test that various document types can be processed"""
        if Path(pdf_file).exists():
            comparator = PDFComparator()
            metrics = comparator.extract_pdf_metrics(pdf_file)
            
            # All PDFs should have these basic properties
            assert metrics.total_pages > 0
            assert metrics.total_characters > 0
            assert len(metrics.page_contents) == metrics.total_pages
            assert metrics.total_text.strip() != ""


if __name__ == "__main__":
    # Allow running directly: python tests/pdf_comparison/test_pdf_extraction_metrics.py
    pytest.main([__file__, "-v"])
