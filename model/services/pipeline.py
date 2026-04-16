"""
services/pipeline.py
End-to-end orchestration for LegalT with explicit stage tracing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from core.llm_config import LLM_CONFIG, get_required_api_key_name, has_active_api_key
from services.ingestion import extract_text
from services.segmentation import segment_clauses
from services.extractor import run_full_extraction
from services.validator import validate_and_clean
from services.tracing import get_tracer


MIN_EXTRACTED_TEXT_CHARS = 40


def _post_extraction_quality_gates(contract_text: str, output: dict[str, Any]) -> None:
    """Quality checks for mixed-document coverage and reference integrity."""
    clauses = output.get("clauses", []) or []
    if not isinstance(clauses, list):
        raise ValueError("Post-validation failed: clauses is not a list")

    min_expected = max(3, min(10, len(contract_text) // 2200 + 2))
    if len(clauses) < min_expected:
        raise ValueError(
            f"Post-validation failed: clauses count {len(clauses)} is below expected minimum {min_expected}"
        )

    clause_text = "\n".join(
        " ".join(
            str(clause.get(key, ""))
            for key in ("heading", "text", "type", "plain_english")
        )
        for clause in clauses
        if isinstance(clause, dict)
    ).lower()

    raw_text = contract_text.lower()
    nda_markers = [
        "non-disclosure",
        "nda",
        "confidential information",
        "disclosing party",
        "receiving party",
    ]
    raw_nda_hits = sum(1 for marker in nda_markers if marker in raw_text)
    clause_nda_hits = sum(1 for marker in nda_markers if marker in clause_text)
    if raw_nda_hits >= 2 and clause_nda_hits == 0:
        raise ValueError("Post-validation failed: NDA indicators found in raw text but missing from clauses")

    clause_ids = {
        str(clause.get("clause_id"))
        for clause in clauses
        if isinstance(clause, dict) and str(clause.get("clause_id") or "").strip()
    }
    for field in ("obligations", "rights", "timelines"):
        items = output.get(field, []) or []
        if not isinstance(items, list):
            raise ValueError(f"Post-validation failed: {field} is not a list")
        for index, item in enumerate(items, start=1):
            if not isinstance(item, dict):
                continue
            clause_id = str(item.get("clause_id") or "").strip()
            if not clause_id or clause_id not in clause_ids:
                raise ValueError(
                    f"Post-validation failed: orphan {field} reference at item {index} ({clause_id or 'missing'})"
                )


def _prepare_retry_text(contract_text: str) -> str:
    """Insert boundary-friendly newlines around common embedded agreement markers."""
    marker_pattern = re.compile(
        r"(?i)(non[-\s]?disclosure\s+agreement|\bnda\b|this\s+agreement\s+is\s+made\s+on|in\s+witness\s+whereof|confidential\s+information\s*:)",
    )
    return marker_pattern.sub(r"\n\n\1\n", contract_text)


def run_pipeline(file_path: str, *, verbose: bool = False) -> dict[str, Any]:
    tracer = get_tracer()
    path = Path(file_path)

    tracer.trace(stage="Stage 0", event_type="validation", description="Input validation", details={
        "file": path.name,
        "provider": LLM_CONFIG.active_provider,
        "model": LLM_CONFIG.model or "default",
    })

    if not path.exists():
        tracer.trace_error("Stage 0", f"File not found: {path}", "FileNotFound")
        raise FileNotFoundError(f"File not found: {path}")

    if path.suffix.lower() not in {".pdf", ".docx", ".doc", ".txt"}:
        tracer.trace_error("Stage 0", f"Unsupported file type: {path.suffix}", "FileTypeError")
        raise ValueError(f"Unsupported file type: {path.suffix}")

    if not has_active_api_key():
        tracer.trace_error("Stage 0", f"{get_required_api_key_name()} not set", "MissingAPIKey")
        raise RuntimeError(f"{get_required_api_key_name()} environment variable not set")

    tracer.trace(stage="Stage 1", event_type="extraction", description="Extracting raw document text", details={})
    contract_text = extract_text(str(path))
    tracer.trace(stage="Stage 1", event_type="extraction", description=f"Text extracted: {len(contract_text)} characters", details={
        "character_count": len(contract_text),
        "preview": contract_text[:200],
    })
    
    normalized_text = contract_text.strip()
    if not normalized_text or len(normalized_text) < MIN_EXTRACTED_TEXT_CHARS:
        tracer.trace_error("Stage 1", "Extracted text is empty", "EmptyDocument")
        raise ValueError("Extracted document text is empty or too short for analysis")

    tracer.trace(stage="Stage 2", event_type="extraction", description="Splitting document into clauses", details={})
    clauses = segment_clauses(contract_text)
    tracer.trace(stage="Stage 2", event_type="extraction", description=f"Clauses segmented: {len(clauses)} sections found", details={
        "clause_count": len(clauses),
        "sample_clauses": [{"heading": h[:60], "length": len(t)} for h, t in clauses[:3]],
    })
    
    if verbose and clauses:
        for i, (heading, text) in enumerate(clauses[:5], 1):
            tracer.trace(stage="Stage 2", event_type="validation", description=f"Sample clause {i}", details={
                "heading": heading[:60],
                "length": len(text),
            })

    output: dict[str, Any] | None = None
    extraction_text = contract_text
    extraction_clauses = clauses

    for attempt in (1, 2):
        tracer.trace(stage="Stage 3", event_type="extraction", description="Running grounded two-pass extraction", details={"attempt": attempt})
        document = run_full_extraction(extraction_text, extraction_clauses)
        document.filename = path.name
        tracer.trace_extraction(stage="Stage 3", entity_type="clauses", count=len(document.clauses))
        tracer.trace_extraction(stage="Stage 3", entity_type="risks", count=len(document.risks))
        tracer.trace_extraction(stage="Stage 3", entity_type="obligations", count=len(document.obligations))

        tracer.trace(stage="Stage 4", event_type="validation", description="Strict validation and schema normalization", details={"attempt": attempt})
        output_candidate = document.model_dump()
        validated = validate_and_clean(output_candidate)
        candidate = validated.model_dump()

        try:
            _post_extraction_quality_gates(extraction_text, candidate)
            tracer.trace(stage="Stage 4", event_type="validation", description="Validation complete", details={
                "attempt": attempt,
                "enriched_keys": list(output_candidate.keys()),
                "validated_keys": list(validated.model_dump().keys()),
            })
            output = candidate
            break
        except ValueError as gate_error:
            tracer.trace_error(
                "Stage 4",
                str(gate_error),
                "PostExtractionGateError",
                {"attempt": attempt},
            )
            if attempt == 2:
                raise

            extraction_text = _prepare_retry_text(contract_text)
            extraction_clauses = segment_clauses(extraction_text)
            tracer.trace(
                stage="Stage 2",
                event_type="validation",
                description="Retry segmentation prepared after quality gate failure",
                details={"retry_clause_count": len(extraction_clauses)},
            )

    if output is None:
        raise RuntimeError("Pipeline failed to produce validated output")

    tracer.print_summary()
    
    return output


def print_pipeline_json(result: dict[str, Any]) -> None:
    print("\n" + "=" * 70)
    print("ANALYSIS RESULTS")
    print("=" * 70)
    print(json.dumps(result, indent=2))
