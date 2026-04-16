"""Regression tests for pipeline completeness and empty-input guards."""

import pytest

from models.schema import Clause, ClauseCategory, RiskLevel
from services.extractor import _dedupe_clauses
from services.pipeline import _post_extraction_quality_gates
from services.pipeline import run_pipeline
from services.validator import validate_and_clean


def test_validate_and_clean_rejects_empty_required_sections() -> None:
    """Completeness gate must reject empty sections before schema acceptance."""
    payload = {
        "summary": {
            "executive_summary": "x",
            "key_points": [],
            "red_flags": [],
            "favorable_clauses": [],
            "unusual_clauses": [],
            "favorable_to": None,
            "overall_risk_score": 0,
            "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "recommended_actions": ["x"],
        },
        "clauses": [],
        "risks": [],
        "obligations": [],
        "rights": [],
        "timelines": [],
        "negotiation_points": [],
    }

    with pytest.raises(ValueError, match="clauses is empty"):
        validate_and_clean(payload)


def test_pipeline_rejects_empty_text_file(tmp_path) -> None:
    """Pipeline should fail fast on empty/too-short extracted text."""
    doc = tmp_path / "empty.txt"
    doc.write_text("\n", encoding="utf-8")

    with pytest.raises(ValueError, match="empty or too short"):
        run_pipeline(str(doc), verbose=False)


def test_post_extraction_quality_gate_rejects_nda_drop() -> None:
    """If NDA markers exist in raw text, clauses must preserve NDA coverage."""
    contract_text = (
        "Internship terms apply. "
        "This Non-Disclosure Agreement defines Confidential Information between Disclosing Party and Receiving Party."
    )
    output = {
        "clauses": [
            {
                "clause_id": "1",
                "heading": "Internship Details",
                "text": "Internship details only",
                "type": "Other",
                "plain_english": "Internship details",
            },
            {
                "clause_id": "2",
                "heading": "Roles",
                "text": "Work expectations",
                "type": "Other",
                "plain_english": "Roles",
            },
            {
                "clause_id": "3",
                "heading": "Code of Conduct",
                "text": "Conduct rules",
                "type": "Other",
                "plain_english": "Conduct",
            },
        ],
        "obligations": [{"clause_id": "1", "party": "A", "action": "Do work"}],
        "rights": [{"clause_id": "2", "party": "A", "right": "Access systems"}],
        "timelines": [{"clause_id": "3", "event": "Start", "timeframe": "Immediate"}],
    }

    with pytest.raises(ValueError, match="NDA indicators"):
        _post_extraction_quality_gates(contract_text, output)


def test_post_extraction_quality_gate_rejects_orphan_obligation() -> None:
    """Obligations/rights/timelines must point to valid clause ids."""
    contract_text = "Simple contract text with enough words. " * 200
    output = {
        "clauses": [
            {"clause_id": "1", "heading": "Scope", "text": "Scope text", "type": "Other", "plain_english": "Scope"},
            {"clause_id": "2", "heading": "Confidentiality", "text": "Confidential terms", "type": "Other", "plain_english": "Confidential"},
            {"clause_id": "3", "heading": "Termination", "text": "Termination terms", "type": "Other", "plain_english": "Termination"},
            {"clause_id": "4", "heading": "Law", "text": "Law terms", "type": "Other", "plain_english": "Law"},
            {"clause_id": "5", "heading": "Notices", "text": "Notice terms", "type": "Other", "plain_english": "Notices"},
        ],
        "obligations": [{"clause_id": "Bad Clause Ref", "party": "A", "action": "Do work"}],
        "rights": [{"clause_id": "2", "party": "A", "right": "Access systems"}],
        "timelines": [{"clause_id": "3", "event": "Start", "timeframe": "Immediate"}],
    }

    with pytest.raises(ValueError, match="orphan obligations reference"):
        _post_extraction_quality_gates(contract_text, output)


def test_dedupe_clauses_removes_exact_duplicates() -> None:
    """Duplicate extracted clauses should collapse before downstream passes."""
    clauses = [
        Clause(
            clause_id="1",
            section_number="1",
            heading="Confidentiality",
            text="Confidential Information must be protected.",
            plain_english="Confidentiality clause.",
            type="Confidentiality",
            category=ClauseCategory.DEFINITION,
            risk_level=RiskLevel.LOW,
            risk_score=10,
            risk_justification="Standard confidentiality obligation.",
        ),
        Clause(
            clause_id="2",
            section_number="1",
            heading="Confidentiality",
            text="Confidential Information must be protected.",
            plain_english="Duplicate confidentiality clause.",
            type="Confidentiality",
            category=ClauseCategory.DEFINITION,
            risk_level=RiskLevel.LOW,
            risk_score=10,
            risk_justification="Duplicate confidentiality obligation.",
        ),
        Clause(
            clause_id="3",
            section_number="2",
            heading="Return of Information",
            text="Return or destroy all copies on termination.",
            plain_english="Return clause.",
            type="Confidentiality",
            category=ClauseCategory.REMEDY,
            risk_level=RiskLevel.MEDIUM,
            risk_score=30,
            risk_justification="Return obligation.",
        ),
    ]

    deduped = _dedupe_clauses(clauses)
    assert len(deduped) == 2
    assert [clause.clause_id for clause in deduped] == ["1", "3"]
