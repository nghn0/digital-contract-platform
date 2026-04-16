"""
Centralized debug logging and pipeline tracing.

Follows the logs/stage_N_name/output.json convention from FACT 6.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any


class DebugLogger:
    """Unified logger for pipeline execution tracking and debugging."""

    def __init__(self, debug: bool = False, log_dir: str = "logs"):
        """
        Initialize the debug logger.
        
        Args:
            debug: Whether to print debug output to console
            log_dir: Root directory for log files
        """
        self.debug = debug
        self.log_dir = log_dir
        self._ensure_log_dir()

    def _ensure_log_dir(self) -> None:
        """Create log directory if it doesn't exist."""
        os.makedirs(self.log_dir, exist_ok=True)

    def save_json(self, relative_path: str, data: dict) -> None:
        """
        Save data as JSON to a file.
        
        Follows logs/stage_N_name/output.json naming convention.
        Creates parent directories as needed.
        
        Args:
            relative_path: Path relative to log_dir (e.g., "stage_1_analysis/output.json")
            data: Dictionary to save as JSON
        """
        full_path = os.path.join(self.log_dir, relative_path)
        parent = os.path.dirname(full_path)

        os.makedirs(parent, exist_ok=True)

        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=True, default=str)

    def log_llm_call(
        self,
        stage: str,
        prompt: str,
        response: str,
        duration_ms: int,
        success: bool,
        fallback_used: bool = False,
    ) -> None:
        """
        Log an LLM API call.
        
        Prints to console if debug=True. Always writes to file.
        
        Args:
            stage: Stage name (e.g., "stage3_classification")
            prompt: Full prompt text
            response: Full response text
            duration_ms: Call duration in milliseconds
            success: Whether call succeeded
            fallback_used: Whether fallback logic was used
        """
        if self.debug:
            print(f"\n{'='*60}")
            print(f"[LLM INPUT][{stage}] (first 1000 chars)")
            print(prompt[:1000])
            print(f"\n[LLM OUTPUT][{stage}] (first 1000 chars)")
            print((response or "<empty>")[:1000])
            print(f"[LLM] Duration: {duration_ms}ms | Success: {success} | Fallback: {fallback_used}")
            print("=" * 60)

        log_entry = {
            "stage": stage,
            "prompt_chars": len(prompt),
            "response_chars": len(response) if response else 0,
            "duration_ms": duration_ms,
            "success": success,
            "fallback_used": fallback_used,
            "timestamp": datetime.utcnow().isoformat(),
            "prompt_preview": prompt[:500],
            "response_preview": (response or "")[:500],
        }

        self.save_json(f"llm_{stage}/output.json", log_entry)

    def log_stage_result(
        self,
        stage: str,
        result_summary: dict,
        validation_errors: list[str],
        duration_ms: int,
    ) -> None:
        """
        Log a pipeline stage completion.
        
        Prints to console if debug=True. Always writes to file.
        
        Args:
            stage: Stage name (e.g., "stage3_classification")
            result_summary: Summary dict of stage result
            validation_errors: List of validation errors (empty if valid)
            duration_ms: Stage duration in milliseconds
        """
        if self.debug:
            print(f"\n[STAGE RESULT][{stage}]")
            print(f"  Duration  : {duration_ms}ms")
            print(f"  Validation: {'PASS' if not validation_errors else 'FAIL'}")
            if validation_errors:
                for error in validation_errors:
                    print(f"  ⚠️  {error}")

        # Determine output path based on whether logs/stage_name/ exists
        # from existing pipeline
        stage_number = stage.split("_")[0].replace("stage", "")
        existing_path = Path(self.log_dir) / f"stage_{stage_number}_{stage.split('_', 1)[1]}"

        if existing_path.exists():
            # Write to validation.json to avoid overwriting existing pipeline output
            output_file = f"stage_{stage_number}_{stage.split('_', 1)[1]}/validation.json"
        else:
            # Write to output.json for new stages
            output_file = f"{stage}/output.json"

        log_entry = {
            "stage": stage,
            "duration_ms": duration_ms,
            "validation_errors": validation_errors,
            "validation_passed": len(validation_errors) == 0,
            "result_summary": result_summary,
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.save_json(output_file, log_entry)

    def log_schema_gaps(self, gaps: list[str]) -> None:
        """
        Log unpopulated schema fields.
        
        Args:
            gaps: List of gap descriptions
        """
        if gaps:
            for gap in gaps:
                print(f"[SCHEMA GAP] {gap}")

        self.save_json(
            "schema_coverage/output.json",
            {
                "gaps": gaps,
                "gap_count": len(gaps),
                "timestamp": datetime.utcnow().isoformat(),
            },
        )

    def log_pipeline_failure(
        self, stage: str, error: Any, context: dict = None
    ) -> None:
        """
        Log a pipeline failure (always prints, always writes file).
        
        Args:
            stage: Stage where failure occurred
            error: Exception or error message
            context: Optional context dict
        """
        # Always print (not gated by debug flag)
        print(f"\n[PIPELINE STOPPED] FAILURE DETECTED")
        print(f"[FAILED STAGE]    {stage}")
        print(f"[ERROR]           {error}")

        error_type = type(error).__name__ if isinstance(error, Exception) else "Unknown"

        log_entry = {
            "failed_stage": stage,
            "error": str(error),
            "exception_type": error_type,
            "context": context or {},
            "timestamp": datetime.utcnow().isoformat(),
        }

        self.save_json("pipeline_failure/output.json", log_entry)
