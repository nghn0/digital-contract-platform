"""
Wrapper functions that integrate strict validation into pipeline stages.
These replace silent fallbacks with hard errors and comprehensive logging.

Usage:
    from services.extractor_strict_integration import validate_clause_extraction

    try:
        clause = extract_clauses(...)
    except Exception as e:
        validate_clause_extraction(
            stage="clause_extraction",
            error=e,
            clause_text=text,
            llm_output=result if 'result' in locals() else None
        )
"""

import json
import traceback
from typing import Any, Optional
from services.pipeline_validation import (
    _metrics, 
    abort_no_fallback, 
    save_stage_debug_files,
    detect_generic_response
)
from services.llm_debug import get_debug_logger


def validate_clause_extraction(
    stage: str,
    error: Exception,
    clause_text: str,
    llm_output: Optional[Any] = None,
) -> None:
    """
    Called when clause extraction fails. NEVER silently falls back.
    Instead, logs error, saves debug files, and raises RuntimeError.
    
    Args:
        stage: Pipeline stage name (e.g., "clause_extraction")
        error: The exception that occurred
        clause_text: The clause text being processed
        llm_output: The LLM output (if any) before failure
    
    Raises:
        RuntimeError: ALWAYS (no silent fallback)
    """
    _metrics.add_llm_failure(stage, str(error))
    
    # Save debug information
    debug_logger = get_debug_logger()
    debug_data = {
        "stage": stage,
        "error": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc(),
        "clause_text": clause_text[:1000],  # First 1000 chars
        "llm_output": str(llm_output)[:1000] if llm_output else None,
    }
    
    # Save to files
    save_stage_debug_files(
        stage=stage,
        llm_input=f"Stage: {stage}\nClause: {clause_text[:500]}",
        llm_output=str(llm_output) if llm_output else f"ERROR: {str(error)}",
        parsed=debug_data
    )
    
    # HARD ERROR - never silent fallback
    abort_no_fallback(
        stage=stage,
        reason=f"Extraction failed: {str(error)}",
        debug_data=debug_data
    )


def validate_metadata_extraction(
    stage: str,
    error: Exception,
    contract_text: str,
) -> None:
    """
    Called when metadata/parties extraction fails. NEVER silently falls back.
    
    Args:
        stage: Pipeline stage name (e.g., "metadata_extraction")
        error: The exception that occurred
        contract_text: The contract text being processed
    
    Raises:
        RuntimeError: ALWAYS (no silent fallback)
    """
    _metrics.add_llm_failure(stage, str(error))
    
    debug_logger = get_debug_logger()
    debug_data = {
        "stage": stage,
        "error": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc(),
        "contract_text_sample": contract_text[:500],
    }
    
    save_stage_debug_files(
        stage=stage,
        llm_input=f"Stage: {stage}\nContract: {contract_text[:200]}",
        llm_output=f"ERROR: {str(error)}",
        parsed=debug_data
    )
    
    abort_no_fallback(
        stage=stage,
        reason=f"Metadata extraction failed: {str(error)}",
        debug_data=debug_data
    )


def validate_pipeline_stage(
    stage: str,
    error: Exception,
    stage_input: str,
) -> None:
    """
    Generic validation for any pipeline stage failure.
    
    Args:
        stage: Pipeline stage name
        error: Exception that occurred
        stage_input: Input data for the stage
    
    Raises:
        RuntimeError: ALWAYS (no silent fallback)
    """
    _metrics.add_llm_failure(stage, str(error))
    
    debug_data = {
        "stage": stage,
        "error": str(error),
        "error_type": type(error).__name__,
        "traceback": traceback.format_exc(),
        "input_sample": stage_input[:500] if isinstance(stage_input, str) else str(stage_input)[:500],
    }
    
    save_stage_debug_files(
        stage=stage,
        llm_input=stage_input[:1000] if isinstance(stage_input, str) else json.dumps(stage_input)[:1000],
        llm_output=f"ERROR: {str(error)}",
        parsed=debug_data
    )
    
    abort_no_fallback(
        stage=stage,
        reason=f"Stage {stage} failed: {str(error)}",
        debug_data=debug_data
    )


def is_fallback_marker(text: str) -> bool:
    """Check if text contains fallback markers."""
    fallback_markers = [
        "fallback",
        "deterministic",
        "mock",
        "generic",
        "default",
        "extraction failed",
    ]
    text_lower = text.lower()
    return any(marker in text_lower for marker in fallback_markers)


def assert_no_fallback(
    stage: str,
    output: Any,
    min_confidence: float = 0.7,
) -> None:
    """
    Assert that output doesn't appear to be a fallback result.
    
    Args:
        stage: Pipeline stage name
        output: Output to check
        min_confidence: Minimum confidence threshold (0-1)
    
    Raises:
        RuntimeError: If output appears to be a fallback
    """
    if output is None:
        abort_no_fallback(stage, "Output is None - no extraction attempted")
    
    if isinstance(output, dict):
        # Check for fallback markers in string fields
        for key, value in output.items():
            if isinstance(value, str) and is_fallback_marker(value):
                _metrics.add_fallback_detection(stage, f"Fallback marker in field '{key}'")
                abort_no_fallback(
                    stage=stage,
                    reason=f"Fallback marker detected in field '{key}': {value}",
                    debug_data={"field": key, "value": value}
                )
        
        # Check for suspicious confidence values
        if "confidence" in output:
            conf = output.get("confidence", 0.5)
            if conf < min_confidence:
                _metrics.add_fallback_detection(stage, f"Low confidence: {conf}")
                abort_no_fallback(
                    stage=stage,
                    reason=f"Confidence too low: {conf} < {min_confidence}",
                    debug_data={"confidence": conf, "threshold": min_confidence}
                )
    
    if isinstance(output, list) and len(output) == 0:
        abort_no_fallback(
            stage=stage,
            reason="Empty list returned - no items extracted",
            debug_data={"output_length": 0}
        )
