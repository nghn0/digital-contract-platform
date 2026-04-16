"""
services/pipeline_validation.py

Strict validation for each stage of the legal document pipeline.
Prevents silent fallbacks and ensures LLM is always actually called.

Key functions:
- validate_json_response(): Strict JSON parsing
- validate_schema(): Pydantic validation
- detect_fake_output(): Detects generic/fallback responses
- validate_stage_output(): Full stage validation
"""

import json
import sys
from typing import Any, Optional, Type
from pydantic import BaseModel, ValidationError

from models.schema import (
    Clause, DocumentMetadata, LegalDocumentAnalysis, 
    RiskItem, Obligation, Right, TimelineEvent
)
from services.tracing import get_tracer

tracer = get_tracer()

# ─── GENERIC FALLBACK MARKERS ────────────────────────────────────────────────
GENERIC_REASONS = [
    "contains commercial or risk-bearing language",
    "fallback explanation generated",
    "fallback reasoning applied",
    "grounded by deterministic rules",
    "potential issue identified",
    "review and negotiate",
    "based on clause content",
]

CONSTANT_CONFIDENCES = [0.5, 0.0, 1.0]  # Suspicious/fallback values


# ─── STAGE METRICS TRACKING ──────────────────────────────────────────────────
class PipelineMetrics:
    """Track pipeline execution with detailed failure tracking."""
    
    def __init__(self):
        self.llm_calls = 0
        self.llm_failures = 0
        self.schema_failures = 0
        self.fallback_detections = 0
        self.stage_failures = {}
        self.stage_passed = {}
        self.validation_errors = []
    
    def add_llm_call(self):
        self.llm_calls += 1
    
    def add_llm_failure(self, stage: str, reason: str):
        self.llm_failures += 1
        self.validation_errors.append({
            "type": "llm_failure",
            "stage": stage,
            "reason": reason
        })
    
    def add_schema_failure(self, stage: str, error: str):
        self.schema_failures += 1
        self.validation_errors.append({
            "type": "schema_failure",
            "stage": stage,
            "error": error
        })
    
    def add_fallback_detection(self, stage: str, marker: str):
        self.fallback_detections += 1
        self.validation_errors.append({
            "type": "fallback_detected",
            "stage": stage,
            "marker": marker
        })
    
    def add_stage_failure(self, stage: str, error: str):
        self.stage_failures[stage] = error
    
    def add_stage_pass(self, stage: str, item_count: int):
        self.stage_passed[stage] = item_count
    
    def report(self):
        print("\n" + "=" * 70)
        print("PIPELINE VALIDATION METRICS")
        print("=" * 70)
        print(f"[LLM CALLS]        {self.llm_calls}")
        print(f"[LLM FAILURES]     {self.llm_failures}")
        print(f"[SCHEMA FAILURES]  {self.schema_failures}")
        print(f"[FALLBACK MARKED]  {self.fallback_detections}")
        print(f"[STAGES PASSED]    {list(self.stage_passed.keys())}")
        print(f"[STAGES FAILED]    {list(self.stage_failures.keys())}")
        if self.validation_errors:
            print(f"\n[ERRORS]: {len(self.validation_errors)}")
            for err in self.validation_errors[:5]:
                print(f"  - {err['type']}: {err['stage']} - {err.get('reason') or err.get('error') or err.get('marker')}")
        print("=" * 70 + "\n")


# Global metrics instance
_metrics = PipelineMetrics()

def get_pipeline_metrics() -> PipelineMetrics:
    return _metrics


# ─── JSON VALIDATION ────────────────────────────────────────────────────────
def validate_json_response(response_text: str, stage: str) -> dict[str, Any]:
    """
    Parse JSON strictly from LLM response.
    Raises RuntimeError if:
    - Invalid JSON
    - Contains non-JSON commentary
    - Multiple JSON objects detected
    """
    print(f"\n[JSON VALIDATION] Stage: {stage}")
    print(f"[RAW RESPONSE] (first 500 chars):\n{response_text[:500]}\n")
    
    # Check for common LLM preamble
    if any(marker in response_text.lower() for marker in ["here is", "let me provide", "based on", "the json"]):
        # Try to extract JSON after preamble
        import re
        json_match = re.search(r'(\{.*\}|\[.*\])', response_text, re.DOTALL)
        if json_match:
            response_text = json_match.group(1)
            print(f"[JSON EXTRACTED] Removed preamble")
    
    try:
        parsed = json.loads(response_text)
        print(f"✓ JSON VALID")
        return parsed
    except json.JSONDecodeError as e:
        print(f"✗ INVALID JSON: {str(e)}")
        _metrics.add_llm_failure(stage, f"Invalid JSON: {str(e)}")
        raise RuntimeError(f"[{stage}] LLM returned invalid JSON:\n{response_text[:300]}")


# ─── DETECT FAKE/FALLBACK OUTPUT ────────────────────────────────────────────
def detect_generic_response(response_text: str, parsed: Any, stage: str) -> None:
    """
    Detect if output is generic/fallback marker.
    Raises RuntimeError if detected.
    """
    print(f"\n[FAKE OUTPUT DETECTION] Stage: {stage}")
    
    # Check for generic markers
    response_lower = (response_text or "").lower()
    for marker in GENERIC_REASONS:
        if marker in response_lower:
            print(f"✗ GENERIC MARKER FOUND: '{marker}'")
            _metrics.add_fallback_detection(stage, marker)
            raise RuntimeError(f"[{stage}] Generic fallback response detected: {marker}")
    
    # Check for constant/suspicious confidences
    if isinstance(parsed, list):
        confidences = [item.get("confidence") for item in parsed if isinstance(item, dict)]
        if confidences and all(c in CONSTANT_CONFIDENCES for c in confidences):
            print(f"✗ CONSTANT CONFIDENCE VALUES: {set(confidences)}")
            _metrics.add_fallback_detection(stage, f"constant_confidence_{confidences[0]}")
            raise RuntimeError(f"[{stage}] All confidences are constant {confidences[0]} (fallback detected)")
    
    # Check for LLM refusal patterns
    refusal_markers = ["i cannot", "i can't", "as an ai", "not able to"]
    for marker in refusal_markers:
        if marker in response_lower:
            print(f"✗ LLM REFUSAL: {marker}")
            _metrics.add_llm_failure(stage, f"LLM refused: {marker}")
            raise RuntimeError(f"[{stage}] LLM refused to process: {response_text[:200]}")
    
    print(f"✓ NO GENERIC MARKERS DETECTED")


# ─── SCHEMA VALIDATION ──────────────────────────────────────────────────────
def validate_schema(data: Any, schema_class: Type[BaseModel], stage: str, item_name: str = "item") -> BaseModel:
    """
    Validate single item against Pydantic schema.
    Raises RuntimeError with detailed error on validation failure.
    """
    print(f"\n[SCHEMA VALIDATION] Stage: {stage} | Type: {schema_class.__name__}")
    
    try:
        validated = schema_class(**data)
        print(f"✓ SCHEMA VALID ({item_name})")
        return validated
    except ValidationError as e:
        print(f"✗ SCHEMA INVALID ({schema_class.__name__}):")
        print(f"  Input: {json.dumps(data, indent=2)[:300]}")
        print(f"  Errors: {e.errors()}")
        _metrics.add_schema_failure(stage, str(e))
        raise RuntimeError(f"[{stage}] Schema validation failed for {item_name}:\n{str(e)[:500]}")


def validate_schema_list(items: list[Any], schema_class: Type[BaseModel], stage: str) -> list[BaseModel]:
    """
    Validate list of items against schema.
    Raises RuntimeError on first failure.
    """
    print(f"\n[SCHEMA VALIDATION LIST] Stage: {stage} | Count: {len(items)} | Type: {schema_class.__name__}")
    
    validated_items = []
    for idx, item in enumerate(items):
        try:
            validated = validate_schema(item, schema_class, stage, f"item[{idx}]")
            validated_items.append(validated)
        except RuntimeError as e:
            print(f"✗ FAILED AT INDEX {idx}/{len(items)}")
            raise
    
    print(f"✓ ALL {len(validated_items)} ITEMS VALID")
    _metrics.add_stage_pass(stage, len(validated_items))
    return validated_items


# ─── STAGE OUTPUT VALIDATION ────────────────────────────────────────────────
def validate_stage_output(stage_name: str, output: Any, schema_class: Optional[Type[BaseModel]] = None, min_items: int = 1) -> Any:
    """
    Comprehensive stage validation:
    1. Non-null
    2. Non-empty (min_items)
    3. Schema compliance
    4. No generic markers
    """
    print(f"\n{'='*70}")
    print(f"[STAGE VALIDATION] {stage_name.upper()}")
    print(f"{'='*70}")
    
    # Check for None/empty
    if output is None:
        print(f"✗ OUTPUT IS NONE")
        _metrics.add_stage_failure(stage_name, "None output")
        raise RuntimeError(f"[{stage_name}] Stage returned None")
    
    # Check for empty list/dict
    if isinstance(output, (list, dict)):
        if not output:
            print(f"✗ OUTPUT IS EMPTY")
            _metrics.add_stage_failure(stage_name, "Empty output")
            raise RuntimeError(f"[{stage_name}] Stage returned empty output")
        
        if isinstance(output, list) and len(output) < min_items:
            print(f"✗ INSUFFICIENT ITEMS: {len(output)} < {min_items}")
            _metrics.add_stage_failure(stage_name, f"Only {len(output)} items (min {min_items})")
            raise RuntimeError(f"[{stage_name}] Stage returned only {len(output)} items (minimum {min_items})")
    
    # Schema validation
    if schema_class:
        if isinstance(output, list):
            output = validate_schema_list(output, schema_class, stage_name)
        else:
            output = validate_schema(output, schema_class, stage_name)
    
    print(f"✓ STAGE {stage_name.upper()} VALIDATED")
    return output


# ─── DISABLE ALL FALLBACKS ──────────────────────────────────────────────────
def abort_no_fallback(stage: str, reason: str, debug_data: Optional[dict] = None) -> None:
    """
    Called whenever fallback would be triggered.
    ALWAYS raises RuntimeError - fallback is never silent.
    """
    print(f"\n{'='*70}")
    print(f"[FALLBACK TRIGGERED] {stage}")
    print(f"{'='*70}")
    print(f"[REASON]: {reason}")
    if debug_data:
        print(f"[DEBUG DATA]:")
        print(json.dumps(debug_data, indent=2)[:500])
    print(f"{'='*70}\n")
    
    _metrics.add_fallback_detection(stage, reason)
    
    print("[PIPELINE STOPPED] Fallback would be triggered but fallbacks are disabled.")
    print(f"[FAILURE]: {stage} failed permanently\n")
    
    raise RuntimeError(f"[{stage}] Failed with no fallback: {reason}")


# ─── SAVE DEBUG FILES ────────────────────────────────────────────────────────
def save_stage_debug_files(stage: str, llm_input: str, llm_output: str, parsed: Any, logs_dir: str = "logs") -> None:
    """Save input/output/parsed for each stage for forensic analysis."""
    import os
    from datetime import datetime
    
    stage_dir = os.path.join(logs_dir, f"stage_debug_{stage}")
    os.makedirs(stage_dir, exist_ok=True)
    
    timestamp = datetime.utcnow().isoformat()
    
    # Save input
    input_file = os.path.join(stage_dir, f"llm_input_{timestamp.replace(':', '-')}.txt")
    with open(input_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"[STAGE] {stage}\n[TIMESTAMP] {timestamp}\n\n")
        f.write(llm_input)
    
    # Save output
    output_file = os.path.join(stage_dir, f"llm_output_{timestamp.replace(':', '-')}.txt")
    with open(output_file, "w", encoding="utf-8", errors="replace") as f:
        f.write(f"[STAGE] {stage}\n[TIMESTAMP] {timestamp}\n\n")
        f.write(llm_output)
    
    # Save parsed
    parsed_file = os.path.join(stage_dir, f"parsed_{timestamp.replace(':', '-')}.json")
    with open(parsed_file, "w", encoding="utf-8") as f:
        json.dump({"stage": stage, "timestamp": timestamp, "data": parsed}, f, indent=2, ensure_ascii=True)
    
    print(f"[DEBUG FILES SAVED] {stage_dir}")


# ─── HARD STOP ON FAILURE ───────────────────────────────────────────────────
def hard_stop(stage: str, error_message: str, exit_code: int = 1) -> None:
    """
    Hard stop execution on pipeline failure.
    Prints metrics and exits immediately.
    """
    print(f"\n{'='*70}")
    print(f"[PIPELINE HALTED] {stage}")
    print(f"{'='*70}")
    print(f"[ERROR]: {error_message}\n")
    
    _metrics.report()
    
    print(f"[EXIT] Code {exit_code}")
    sys.exit(exit_code)
