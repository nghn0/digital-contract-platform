"""
Unit tests for models/schema.py — Pydantic schema validation and constraints.

Tests the LegalDocumentAnalysis schema, enum values, and field constraints
to ensure data quality validation is working correctly.
"""

import pytest
from pydantic import ValidationError

from models.schema import (
    Clause, RiskLevel, ClauseCategory, DocumentMetadata, Party,
    LegalDocumentAnalysis, Obligation
)


class TestRiskLevelEnum:
    """Tests for RiskLevel enumeration."""
    
    def test_all_valid_risk_levels_exist(self):
        """Verify all expected risk level values are defined."""
        assert RiskLevel.LOW.value == "LOW"
        assert RiskLevel.MEDIUM.value == "MEDIUM"
        assert RiskLevel.HIGH.value == "HIGH"
        assert RiskLevel.CRITICAL.value == "CRITICAL"
    
    def test_risk_level_has_four_values(self):
        """Ensure no unexpected risk levels were added or removed."""
        levels = list(RiskLevel)
        assert len(levels) == 4


class TestClauseCategoryEnum:
    """Tests for ClauseCategory enumeration."""
    
    def test_valid_categories_exist(self):
        """Verify primary clause categories are defined."""
        assert ClauseCategory.OBLIGATION.value == "Obligation"
        assert ClauseCategory.RIGHT.value == "Right"
        assert ClauseCategory.DEFINITION.value == "Definition"
        assert ClauseCategory.PROHIBITION.value == "Prohibition"


class TestClauseSchema:
    """Tests for Clause model validation."""

    def test_valid_clause_creation(self, minimal_clause_dict):
        """Test creating a valid clause with all required fields."""
        clause = Clause(**minimal_clause_dict)
        assert clause.clause_id == "seg_001"
        assert clause.risk_score == 10
        assert clause.risk_level == RiskLevel.LOW
        assert clause.category == ClauseCategory.DEFINITION

    def test_risk_score_above_100_rejected(self, minimal_clause_dict):
        """Test that risk_score > 100 is rejected by Pydantic validator."""
        minimal_clause_dict["risk_score"] = 150
        with pytest.raises(ValidationError) as exc_info:
            Clause(**minimal_clause_dict)
        assert "risk_score" in str(exc_info.value).lower()

    def test_risk_score_below_0_rejected(self, minimal_clause_dict):
        """Test that risk_score < 0 is rejected."""
        minimal_clause_dict["risk_score"] = -5
        with pytest.raises(ValidationError):
            Clause(**minimal_clause_dict)

    def test_risk_score_boundary_values_accepted(self, minimal_clause_dict):
        """Test that boundary values 0 and 100 are accepted."""
        for boundary in [0, 100]:
            minimal_clause_dict["risk_score"] = boundary
            clause = Clause(**minimal_clause_dict)
            assert clause.risk_score == boundary

    def test_risk_score_mid_values_accepted(self, minimal_clause_dict):
        """Test that typical mid-range values work."""
        for value in [25, 50, 75]:
            minimal_clause_dict["risk_score"] = value
            clause = Clause(**minimal_clause_dict)
            assert clause.risk_score == value

    def test_clause_minimal_required_fields(self):
        """Test that only actually required fields are needed."""
        minimal = {
            "clause_id": "1",
            "text": "Some clause text",
            "plain_english": "Some plain english",
            "type": "Confidentiality",
            "category": ClauseCategory.OBLIGATION,
            "risk_level": RiskLevel.LOW,
            "risk_score": 25,
            "risk_justification": "Standard clause",
        }
        clause = Clause(**minimal)
        assert clause.clause_id == "1"


class TestDocumentMetadata:
    """Tests for DocumentMetadata model."""

    def test_all_fields_optional(self):
        """Verify that DocumentMetadata has no required fields (FACT 5)."""
        meta = DocumentMetadata()
        assert meta.document_type is None
        assert meta.governing_law is None
        assert meta.jurisdiction is None
        assert meta.language == "English"  # Has default

    def test_document_type_can_be_set(self):
        """Test that document_type enum is properly validated."""
        from models.schema import DocumentType
        meta = DocumentMetadata(document_type=DocumentType.LOAN)
        assert meta.document_type == DocumentType.LOAN


class TestPartySchema:
    """Tests for Party model validation."""

    def test_valid_party_creation(self):
        """Test creating a valid party."""
        party = Party(
            name="ACME Corp LLC",
            role="Borrower",
            legal_entity_type="LLC"
        )
        assert party.name == "ACME Corp LLC"
        assert party.role == "Borrower"

    def test_party_minimal_fields(self):
        """Test party with only required fields."""
        party = Party(name="John Smith", role="Individual")
        assert party.name == "John Smith"
        assert party.address is None


class TestObligationSchema:
    """Tests for Obligation model."""

    def test_valid_obligation_creation(self):
        """Test creating a valid obligation."""
        obligation = Obligation(
            party="Borrower",
            action="Repay principal within 30 days"
        )
        assert obligation.party == "Borrower"
        assert obligation.action == "Repay principal within 30 days"
        assert obligation.is_recurring is False  # Default

    def test_obligation_with_deadline(self):
        """Test obligation with deadline specified."""
        obligation = Obligation(
            party="Bank",
            action="Fund the loan",
            deadline="Within 5 business days",
            is_recurring=False
        )
        assert obligation.deadline == "Within 5 business days"
