from __future__ import annotations

"""Domain-aware KB routing tables for LegalT retrieval."""

KB_DOMAIN_ROUTING: dict[str, list[str]] = {
    "Loan": [
        "kb_clause_types_financial",
        "kb_risk_rules_financial",
        "kb_red_flags",
        "kb_legal_glossary",
    ],
    "NDA": [
        "kb_clause_types",
        "kb_standard_clauses",
        "kb_risk_rules",
        "kb_red_flags",
    ],
    "Employment": [
        "kb_clause_types_employment",
        "kb_risk_rules",
        "kb_red_flags",
        "kb_legal_glossary",
    ],
    "Service Agreement": [
        "kb_clause_types",
        "kb_standard_clauses",
        "kb_risk_rules",
        "kb_red_flags",
    ],
    "Lease": [
        "kb_clause_types_real_estate",
        "kb_risk_rules",
        "kb_red_flags",
        "kb_legal_glossary",
    ],
    "Amendment": [
        "kb_clause_types",
        "kb_risk_rules",
        "kb_red_flags",
    ],
    "default": [
        "kb_clause_types",
        "kb_risk_rules",
        "kb_red_flags",
    ],
}
