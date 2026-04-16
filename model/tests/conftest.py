"""
Pytest configuration and shared fixtures for LegalT test suite.

This module defines reusable fixtures for testing contract analysis stages,
schema validation, and utility functions.
"""

import pytest
from pathlib import Path


@pytest.fixture
def sample_contract_text():
    """Minimal valid contract text for unit testing."""
    return """
    LOAN AGREEMENT

    This Loan Agreement is entered into as of January 1, 2025,
    by and among ACME CORP LLC, a Delaware limited liability company
    (the "Borrower") and FIRST BANK, a Kansas state-chartered bank
    (the "Bank").

    Section 1. DEFINITIONS
    "Loan" means the credit facility established hereunder by the Bank.
    "Borrower" means the party receiving the credit facility.
    "Interest Rate" means the annual percentage rate of interest charged by Bank.

    Section 2. PAYMENT TERMS
    The Borrower shall repay the outstanding principal balance within 30 days
    of the maturity date specified in the Note. Interest accrues daily and
    is due monthly on the 15th of each month.

    Section 3. GOVERNING LAW
    This Agreement shall be governed by the laws of the State of Oklahoma,
    without regard to its conflicts of law principles. The Borrower submits
    to the jurisdiction and venue of the state and federal courts located
    in Oklahoma County, Oklahoma.
    """


@pytest.fixture
def minimal_clause_dict():
    """Minimal valid clause dict matching Stage 2 output format."""
    return {
        "clause_id": "seg_001",
        "section_number": "1",
        "heading": "Section 1. DEFINITIONS",
        "text": "Terms used herein shall have the meanings given below.",
        "plain_english": "This section defines key terms.",
        "type": "Definition",
        "category": "Definition",
        "risk_level": "LOW",
        "risk_score": 10,
        "risk_justification": "Standard definitions clause with no unusual language.",
    }


@pytest.fixture
def sample_stage1_output():
    """
    Simulated Stage 1 output — uses actual key 'document_text' (FACT 4).
    
    This fixture matches the exact output structure of services/ingestion.py.
    """
    return {
        "document_text": "A" * 2000,   # 2000 chars = ~500 tokens
        "total_chars": 2000,
        "text_length": 2000,
        "approx_pages": 1,
        "text_preview": "AAAA...",
        "has_encoding_issues": False,
    }


@pytest.fixture
def sample_clause_batch():
    """Sample batch of clauses for batch processing tests."""
    return [
        {
            "clause_id": "1",
            "heading": "Confidentiality",
            "text": "The parties agree to keep confidential any proprietary information disclosed.",
            "category": "Obligation",
        },
        {
            "clause_id": "2",
            "heading": "Governing Law",
            "text": "This Agreement shall be governed by the laws of New York.",
            "category": "Definition",
        },
        {
            "clause_id": "3",
            "heading": "Termination",
            "text": "Either party may terminate this agreement with 30 days notice.",
            "category": "Condition",
        },
    ]
