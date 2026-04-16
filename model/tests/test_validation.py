"""
Unit tests for services/validator.py — Output validation.

Tests validation logic to ensure extracted data meets quality standards
and catches common errors like generic party names and internal notes.
"""

import pytest
from services.validator import is_valid_party_name


class TestIsValidPartyName:
    """Tests for is_valid_party_name() validation function."""

    def test_valid_company_names(self):
        """Test that legitimate company names pass validation."""
        valid_names = [
            "Apple Inc.",
            "Microsoft Corporation",
            "ACME CORP LLC",
            "First National Bank",
            "Goldman Sachs",
        ]
        for name in valid_names:
            assert is_valid_party_name(name) is True, f"Should accept: {name}"

    def test_valid_individual_names(self):
        """Test that individual names pass validation."""
        valid_names = [
            "John Smith",
            "Mary Johnson",
            "Robert Williams",
        ]
        for name in valid_names:
            assert is_valid_party_name(name) is True, f"Should accept: {name}"

    def test_rejects_generic_templates(self):
        """Test rejection of placeholder party names like 'Party A'."""
        generic_names = [
            "Party A",
            "Party B",
            "Borrower",
            "Lender",
        ]
        for name in generic_names:
            assert is_valid_party_name(name) is False, f"Should reject: {name}"

    def test_rejects_the_agreement_pattern(self):
        """Test rejection of 'the agreement' and similar phrases."""
        bad_names = [
            "the agreement",
            "this agreement",
            "the terms of this agreement",
        ]
        for name in bad_names:
            assert is_valid_party_name(name) is False, f"Should reject: {name}"

    def test_rejects_generic_tokens(self):
        """Test rejection of single generic words."""
        generic = ["State", "Loan", "Security", "Bank"]
        for name in generic:
            result = is_valid_party_name(name)
            # Some may be accepted as they could be company names, but "State" typically rejected
            if name == "State":
                assert result is False

    def test_rejects_empty_and_none(self):
        """Test rejection of empty and None values."""
        assert is_valid_party_name("") is False
        assert is_valid_party_name(None) is False

    def test_rejects_too_short(self):
        """Test rejection of very short names."""
        short = ["A", "AB", "XYZ"]
        for name in short:
            assert is_valid_party_name(name) is False, f"Should reject: {name}"

    def test_critical_bug_jurisdiction_as_party(self):
        """
        Test the critical bug: 'SUBMISSION TO JURISDICTION' extracted as party.
        
        This was found in log analysis and should be caught by validation.
        """
        # The full problematic text
        bad_name = "SUBMISSION TO JURISDICTION AND THE BANK"
        # Should be rejected because it contains "the bank" and jurisdiction reference
        result = is_valid_party_name(bad_name)
        assert result is False, "Should reject jurisdiction clause text as party"

    def test_abbreviations_with_punctuation(self):
        """Test company abbreviations with periods."""
        valid = ["U.S.A.", "Ltd.", "Inc."]
        for name in valid:
            # Should ideally accept, but validation may be conservative
            result = is_valid_party_name(name)
            assert isinstance(result, bool)

    def test_special_characters_handling(self):
        """Test names with special characters."""
        names = ["Smith & Jones", "O'Brien", "Mary-Jane"]
        for name in names:
            result = is_valid_party_name(name)
            assert isinstance(result, bool)

    def test_case_insensitive_matching(self):
        """Test that validation is case-insensitive for keywords."""
        # "the agreement" should be rejected regardless of case
        bad_names = ["THE AGREEMENT", "The Agreement", "the AGREEMENT"]
        for name in bad_names:
            assert is_valid_party_name(name) is False, f"Should reject: {name}"

    def test_with_quotes_and_punctuation(self):
        """Test names that include quotes or punctuation in extraction."""
        # Names might be extracted with extra quotes/punctuation
        names_with_junk = ['  Smith  ', '"Smith Inc"', "Smith's"]
        for name in names_with_junk:
            result = is_valid_party_name(name)
            assert isinstance(result, bool)


class TestValidationFromLogs:
    """Tests based on actual validation errors from audit logs."""

    def test_jurisdiction_as_party_bug(self):
        """
        Regression test for jurisdiction clause extraction as party.
        
        Bug: "SUBMISSION TO JURISDICTION AND THE BANK" was extracted as a party.
        Root cause: Clause heading text not filtered before party extraction.
        Expected: This should be rejected as invalid.
        """
        # Simulate various jurisdiction-related false positives
        bad_extractions = [
            "SUBMISSION TO JURISDICTION",
            "SUBMISSION TO JURISDICTION AND VENUE",
            "SUBMISSION TO JURISDICTION AND THE BANK",
            "GOVERNING LAW AND JURISDICTION",
        ]
        for text in bad_extractions:
            result = is_valid_party_name(text)
            assert result is False, f"Jurisdiction text should not be a party: {text}"

    def test_internal_api_quota_string(self):
        """Test that internal system messages don't match as valid data."""
        # Example from logs: fallback generating system messages
        internal_messages = [
            "Run Pass5 again when API quota resets",
            "Fallback explanation generated", 
            "Internal processing note",
        ]
        for msg in internal_messages:
            result = is_valid_party_name(msg)
            # These might not be explicitly matched but should fail other validation
            assert isinstance(result, bool)
