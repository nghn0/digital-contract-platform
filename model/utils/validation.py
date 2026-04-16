"""
Schema validation and output quality checks.

Validates pipeline outputs at each stage against the Pydantic schema
and flags unpopulated fields and suspicious data patterns.
"""

from typing import Any


def validate_stage1_output(output: dict) -> list[str]:
    """
    Validate Stage 1 (PDF extraction) output.
    
    Checks:
    - 'document_text' key exists (FACT 1: actual key name)
    - Text is substantive (>= 1000 chars)
    - Text is a string
    
    Args:
        output: Stage 1 output dict
        
    Returns:
        List of error strings (empty = valid)
    """
    errors = []

    if "document_text" not in output:
        errors.append("MISSING: 'document_text' key in Stage 1 output")
        return errors

    text = output.get("document_text")

    if not isinstance(text, str):
        errors.append(f"INVALID: 'document_text' is {type(text).__name__}, not str")
        return errors

    if len(text) < 1000:
        errors.append(
            f"INSUFFICIENT: 'document_text' has {len(text)} chars, minimum 1000"
        )

    return errors


def validate_clauses(clauses: list[dict]) -> list[str]:
    """
    Validate clause extraction output.
    
    Checks:
    - Each clause has clause_id with non-empty value
    - Each clause has text with len > 20
    - Flags unfilled plain_english fields
    - Flags unverified low-risk clauses
    
    Args:
        clauses: List of clause dicts
        
    Returns:
        List of warning/error strings
    """
    errors = []

    if not clauses:
        errors.append("WARNING: No clauses extracted")
        return errors

    for clause in clauses:
        clause_id = clause.get("clause_id", "")

        if not clause_id or not str(clause_id).strip():
            errors.append("ERROR: Clause missing clause_id")
            continue

        text = clause.get("text", "")
        if not text or len(text) < 20:
            errors.append(f"ERROR: Clause {clause_id} has insufficient text ({len(text)} chars)")

        plain_english = clause.get("plain_english", "")
        if plain_english == "Extraction fallback":
            errors.append(f"UNFILLED: Clause {clause_id} plain_english is fallback text")

        # Unverified low-risk: risk_score=0 with no fallback flag
        if (
            clause.get("risk_score") == 0
            and clause.get("risk_level") == "Low"
            and not clause.get("fallback_used")
        ):
            errors.append(
                f"UNVERIFIED: Clause {clause_id} has risk_score=0 LOW with no fallback_used flag"
            )

    return errors


def validate_parties(parties_list: list[dict]) -> list[str]:
    """
    Validate party extraction.
    
    Flags:
    - Party names longer than 80 chars (likely sections, not parties)
    - All-caps multi-word names (likely section headings)
    
    Args:
        parties_list: List of party dicts
        
    Returns:
        List of error strings
    """
    errors = []

    for party in parties_list:
        name = party.get("name", "")

        if len(name) > 80:
            errors.append(
                f"SUSPICIOUS PARTY NAME (too long): {name[:60]}..."
            )

        name_words = name.split()
        if name.isupper() and len(name_words) > 5:
            errors.append(
                f"LIKELY CLAUSE MISIDENTIFIED AS PARTY: {name[:60]}..."
            )

    return errors


def validate_risk_summary(summary: dict) -> list[str]:
    """
    Validate risk summary output.
    
    Flags:
    - Suspicious zero scores with no red flags
    - Internal debug strings in user-facing output
    
    Args:
        summary: Risk summary dict
        
    Returns:
        List of error strings
    """
    errors = []

    overall_score = summary.get("overall_risk_score", 0)
    red_flags = summary.get("red_flags", [])

    if overall_score == 0 and not red_flags:
        errors.append(
            "SUSPICIOUS: overall_risk_score=0 with no red_flags — "
            "verify this is not a silent fallback on a risky document"
        )

    # Check for internal debug strings
    exec_summary = (summary.get("executive_summary") or "").lower()
    internal_strings = [
        "api quota",
        "llm disabled",
        "fallback generated",
        "pass5 again",
        "quota resets",
    ]

    for debug_str in internal_strings:
        if debug_str in exec_summary:
            errors.append(
                f"INTERNAL MESSAGE IN USER-FACING OUTPUT: '{debug_str}'"
            )

    return errors


def validate_schema_coverage(pipeline_output: dict) -> list[str]:
    """
    Check for unpopulated schema fields (known gaps from FACT 7).
    
    Warns about fields defined in schema but never populated by pipeline.
    
    Args:
        pipeline_output: Full pipeline output dict
        
    Returns:
        List of warning strings
    """
    warnings = []

    # Check document metadata
    metadata = pipeline_output.get("metadata", {})
    if isinstance(metadata, dict):
        meta_fields = ["document_type", "effective_date", "governing_law"]
        for field in meta_fields:
            if not metadata.get(field):
                warnings.append(f"SCHEMA GAP: Metadata.{field} is unpopulated")

    # Check parties section
    parties = pipeline_output.get("parties", {})
    if isinstance(parties, dict):
        party_list = parties.get("parties", [])
        if not party_list:
            warnings.append("SCHEMA GAP: Parties list is empty")

    # Check clauses for plain_english
    clauses = pipeline_output.get("clauses", [])
    if isinstance(clauses, list):
        for clause in clauses:
            if isinstance(clause, dict):
                plain_english = clause.get("plain_english", "")
                if (
                    not plain_english
                    or plain_english == "Extraction fallback"
                ):
                    clause_id = clause.get("clause_id", "unknown")
                    warnings.append(
                        f"SCHEMA GAP: Clause {clause_id} plain_english is unpopulated"
                    )

    return warnings


def run_all_validations(
    stage: str, data: Any, strict: bool = False
) -> list[str]:
    """
    Route validation based on stage name.
    
    Prints each error with prefix: [VALIDATION][{stage}] {error}
    
    Args:
        stage: Stage identifier ("stage1", "clauses", "parties", "risk_summary", "schema")
        data: Data to validate
        strict: If True, raise ValueError on any errors
        
    Returns:
        Full list of errors (regardless of strict flag)
        
    Raises:
        ValueError: If strict=True and any errors found
    """
    errors: list[str] = []

    if stage == "stage1":
        if isinstance(data, dict):
            errors = validate_stage1_output(data)
    elif stage == "clauses":
        if isinstance(data, list):
            errors = validate_clauses(data)
    elif stage == "parties":
        if isinstance(data, list):
            errors = validate_parties(data)
    elif stage == "risk_summary":
        if isinstance(data, dict):
            errors = validate_risk_summary(data)
    elif stage == "schema":
        if isinstance(data, dict):
            errors = validate_schema_coverage(data)
    else:
        errors = [f"UNKNOWN STAGE: {stage}"]

    # Print all errors
    for error in errors:
        print(f"[VALIDATION][{stage}] {error}")

    # Raise if strict mode and errors exist
    if strict and errors:
        raise ValueError(f"Stage {stage} validation failed: {len(errors)} error(s)")

    return errors
