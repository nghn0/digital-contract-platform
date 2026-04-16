"""
Unit tests for services/segmentation.py — Clause segmentation.

Tests clause segmentation logic to ensure proper splitting of documents
into clause-like blocks for extraction.
"""

import pytest
from services.segmentation import segment_clauses


class TestSegmentClauses:
    """Tests for segment_clauses() function."""

    def test_returns_list_of_tuples(self):
        """Test that segmentation returns list of (heading, text) tuples."""
        text = "Section 1. DEFINITIONS\nTerms used in this..."
        result = segment_clauses(text)
        assert isinstance(result, list)
        assert all(isinstance(item, tuple) and len(item) == 2 for item in result)

    def test_each_item_is_tuple_of_strings(self):
        """Test that each segment is (str, str)."""
        text = "Section 1\nContent here"
        result = segment_clauses(text)
        if result:
            for heading, text_content in result:
                assert isinstance(heading, str)
                assert isinstance(text_content, str)

    def test_empty_text_returns_empty_list(self):
        """Test segmentation of empty text."""
        result = segment_clauses("")
        assert result == [] or isinstance(result, list)

    def test_single_line_text_handled(self):
        """Test that single-line text is handled gracefully."""
        text = "This is a single line of text."
        result = segment_clauses(text)
        assert isinstance(result, list)

    def test_text_with_section_headers(self):
        """Test segmentation of text with clear section headers."""
        text = """
        Section 1. DEFINITIONS
        Definition text here.

        Section 2. PAYMENT TERMS
        Payment terms text here.

        Section 3. TERMINATION
        Termination text here.
        """
        result = segment_clauses(text)
        assert isinstance(result, list)
        assert len(result) > 0

    def test_heading_and_content_paired(self):
        """Test that headings are properly paired with their content."""
        text = "Section 1. TEST\nContent for section 1"
        result = segment_clauses(text)
        if result:
            # At least the first segment should have non-empty text
            assert any(len(text_part) > 0 for _, text_part in result)

    def test_realistic_contract_segmentation(self, sample_contract_text):
        """Test segmentation of realistic contract."""
        result = segment_clauses(sample_contract_text)
        assert isinstance(result, list)
        assert len(result) > 0
        # Should find at least the main sections
        all_text = " ".join([h + " " + t for h, t in result])
        assert "DEFINITIONS" in all_text or "definitions" in all_text.lower()

    def test_numbered_list_patterns(self):
        """Test handling of numbered clause patterns."""
        text = """
        1. First clause
        Content of first clause.

        2. Second clause
        Content of second clause.

        3. Third clause
        Content of third clause.
        """
        result = segment_clauses(text)
        assert isinstance(result, list)
        if result:
            assert len(result) > 0

    def test_parenthetical_list_patterns(self):
        """Test handling of (a), (b), (c) style clauses."""
        text = """
        (a) First item content here.
        (b) Second item content here.
        (c) Third item content here.
        """
        result = segment_clauses(text)
        assert isinstance(result, list)

    def test_returns_consistent_format(self):
        """Test that return format is always list of 2-tuples."""
        for text in ["", "Simple text", "Section 1\nContent"]:
            result = segment_clauses(text)
            assert isinstance(result, list)
            for item in result:
                assert isinstance(item, tuple)
                assert len(item) == 2

    def test_noisy_numbered_lines_without_blank_paragraphs(self):
        """Should split OCR-like numbered lines even without double-newline paragraphs."""
        text = "\n".join(
            [
                "1. Scope This section defines institutional scope and applicability for placements and internships across schools and programmes.",
                "This line continues the scope section with more details about eligibility and process controls.",
                "2. Governance Career and alumni relations coordinates recruiters, scheduling, and student communication standards.",
                "This line continues governance with process ownership and escalation routes.",
                "3. Documentation The office maintains offer letters, acceptance records, and compliance artifacts for audits.",
                "This line continues documentation with retention and verification details.",
            ]
        )

        result = segment_clauses(text)
        assert len(result) >= 3

    def test_long_unstructured_text_chunks_into_sections(self):
        """Long text with no headings should still be chunked into multiple sections."""
        text = " ".join(["policy obligations timelines recruiters students compliance process"] * 700)
        result = segment_clauses(text)
        assert len(result) >= 3

    def test_extremely_short_noisy_text_returns_no_sections(self):
        """Very short extraction noise should not become a synthetic clause."""
        text = "\n\n \t"
        result = segment_clauses(text)
        assert result == []

    def test_mixed_employment_and_nda_sections_are_split(self):
        """Embedded NDA sections should be split as explicit clauses, not merged into one block."""
        text = """
        1. Internship Details
        Internship starts on 01-Jan-2026 for 10 weeks.

        2. Roles and Responsibilities
        The intern shall work under supervision and follow company policy.

        Neutrinos Non-Disclosure Agreement
        This Agreement is made on 01-Jan-2026 between Company and Intern.
        Confidential Information:
        (a) Trade secrets and proprietary code.
        (b) Customer and pricing data.
        Obligations of Confidentiality
        Receiving Party shall not disclose Confidential Information.
        Return or Destruction of Information
        Upon termination, all confidential material must be returned or destroyed.
        IN WITNESS WHEREOF
        Parties execute this Non-Disclosure Agreement.
        """

        result = segment_clauses(text)
        combined = "\n".join(f"{heading} {body}" for heading, body in result).lower()

        assert len(result) >= 5
        assert "non-disclosure" in combined or "confidential information" in combined

    def test_large_clause_is_recursively_split(self):
        """Oversized clauses should be broken into smaller sub-clauses for LLM extraction."""
        large_nda_block = "\n".join(
            [
                "5. Separation",
                "Either party may terminate internship with notice.",
                "Non-Disclosure Agreement",
                "Confidential Information",
                "(a) Product designs and source code are confidential.",
                "(b) Financial forecasts and customer lists are confidential.",
                "Obligations of Confidentiality",
                "Receiving Party shall protect and not disclose information.",
                "Exceptions",
                "Information already public is excluded.",
                "Return or Destruction of Information",
                "All copies shall be returned at termination.",
            ]
            + ["Additional NDA terms apply and survive for three years."] * 180
        )

        result = segment_clauses(large_nda_block)
        assert len(result) >= 3
        assert any("Part" in heading or "Confidential" in heading for heading, _ in result)
        assert all(len(body) <= 2500 for _, body in result)
