"""
Unit tests for services/ingestion.py — Document text extraction.

Tests text extraction from various file types and text cleaning functions.
"""

import pytest
from services.ingestion import extract_text, _clean_text


class TestCleanText:
    """Tests for _clean_text() function."""

    def test_removes_excess_newlines(self):
        """Test that 3+ consecutive newlines are reduced to 2."""
        dirty = "text\n\n\n\nmore"
        clean = _clean_text(dirty)
        assert "\n\n\n" not in clean
        assert "text\n\nmore" in clean

    def test_removes_page_number_artifacts(self):
        """Test that 'Page X of Y' patterns are removed."""
        text = "Some text\nPage 1 of 5\nMore text"
        clean = _clean_text(text)
        assert "Page 1 of 5" not in clean

    def test_collapses_excess_whitespace(self):
        """Test that multiple spaces/tabs are collapsed to single space."""
        text = "word1  word2    word3\tword4"
        clean = _clean_text(text)
        assert "  " not in clean  # No double spaces
        # Note: tabs may still exist as single char, but multi-space collapsed

    def test_preserves_meaningful_newlines(self):
        """Test that single newlines are preserved."""
        text = "Line 1\nLine 2\nLine 3"
        clean = _clean_text(text)
        assert "Line 1\nLine 2" in clean

    def test_strips_leading_trailing_whitespace(self):
        """Test that result is stripped."""
        text = "  \n  content  \n  "
        clean = _clean_text(text)
        assert clean == clean.strip()

    def test_empty_string_returns_empty(self):
        """Test that empty string returns empty."""
        assert _clean_text("") == ""

    def test_only_whitespace_returns_empty(self):
        """Test that whitespace-only input returns empty."""
        assert _clean_text("   \n\n  \t  ") == ""

    def test_typical_contract_text_preserved(self):
        """Test that typical contract text is preserved correctly."""
        text = """
        Section 1. DEFINITIONS

        "Loan" means the credit facility.
        "Borrower" means the party receiving credit.
        """
        clean = _clean_text(text)
        assert "Section 1" in clean
        assert "Loan" in clean
        assert "DEFINITIONS" in clean


class TestExtractText:
    """Tests for extract_text() - file format handling."""

    def test_txt_file_extraction(self, tmp_path):
        """Test extraction from .txt file."""
        txt_file = tmp_path / "contract.txt"
        txt_file.write_text("This is contract text\nWith multiple lines")
        
        result = extract_text(str(txt_file))
        assert isinstance(result, str)
        assert len(result) > 0
        assert "contract text" in result

    def test_unsupported_file_type_raises_error(self, tmp_path):
        """Test that unsupported extensions raise ValueError."""
        bad_file = tmp_path / "document.xyz"
        bad_file.write_text("content")
        
        with pytest.raises(ValueError) as exc_info:
            extract_text(str(bad_file))
        assert "Unsupported file type" in str(exc_info.value.args)

    def test_missing_file_raises_error(self):
        """Test that missing files raise appropriate error."""
        with pytest.raises((FileNotFoundError, ValueError)):
            extract_text("/nonexistent/path/file.pdf")

    def test_empty_txt_file(self, tmp_path):
        """Test extraction from empty .txt file."""
        empty_file = tmp_path / "empty.txt"
        empty_file.write_text("")
        
        result = extract_text(str(empty_file))
        assert result == ""

    def test_txt_with_encoding_errors_handled(self, tmp_path):
        """Test that encoding errors are gracefully handled."""
        txt_file = tmp_path / "contract_encoded.txt"
        # Write with default encoding
        txt_file.write_text("Valid text with symbols: © ™")
        
        result = extract_text(str(txt_file))
        assert isinstance(result, str)
        assert len(result) > 0


class TestExtractRawPages:
    """Tests for extract_raw_pages() - page-preserving extraction."""

    def test_returns_list_of_dicts(self, tmp_path):
        """Test that page extraction returns list of page dicts."""
        from services.ingestion import extract_raw_pages
        
        txt_file = tmp_path / "contract.txt"
        txt_file.write_text("Page content here")
        
        result = extract_raw_pages(str(txt_file))
        assert isinstance(result, list)
        assert len(result) > 0
        assert isinstance(result[0], dict)
        assert "page_num" in result[0]
        assert "text" in result[0]

    def test_page_dicts_have_required_keys(self, tmp_path):
        """Test that returned dicts have page_num and text."""
        from services.ingestion import extract_raw_pages
        
        txt_file = tmp_path / "contract.txt"
        txt_file.write_text("Content")
        
        pages = extract_raw_pages(str(txt_file))
        for page in pages:
            assert "page_num" in page
            assert "text" in page
            assert isinstance(page["page_num"], int)
            assert page["page_num"] >= 1
