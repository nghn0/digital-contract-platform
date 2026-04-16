"""
services/llm_debug.py

Comprehensive LLM call logging and debugging.
Saves all LLM inputs and outputs for forensic analysis.
Integrates with pipeline_validation for strict error handling.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class LLMDebugLogger:
    """
    Logs all LLM calls with input/output/parsed.
    Creates debug files for each stage.
    """
    
    def __init__(self, logs_dir: str = "logs"):
        self.logs_dir = logs_dir
        self.debug_dir = Path(logs_dir) / "llm_debug"
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        self.calls = []
    
    def log_call(
        self,
        stage: str,
        model: str,
        llm_input: str,
        llm_output: str,
        parsed: Optional[Any] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Log a single LLM call.
        Saves input/output to separate files.
        Tracks all calls for final report.
        """
        timestamp = datetime.utcnow().isoformat()
        call_id = f"{stage}_{len(self.calls):04d}_{timestamp.replace(':', '-')}"
        
        # Create stage subdirectory
        stage_dir = self.debug_dir / stage
        stage_dir.mkdir(parents=True, exist_ok=True)
        
        # Save input
        input_file = stage_dir / f"{call_id}_input.txt"
        with open(input_file, "w", encoding="utf-8") as f:
            f.write(f"[STAGE] {stage}\n")
            f.write(f"[MODEL] {model}\n")
            f.write(f"[TIMESTAMP] {timestamp}\n")
            f.write(f"[SUCCESS] {success}\n")
            f.write("\n" + "="*70 + "\n[PROMPT INPUT]\n" + "="*70 + "\n\n")
            f.write(llm_input)
        
        # Save output
        output_file = stage_dir / f"{call_id}_output.txt"
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(f"[STAGE] {stage}\n")
            f.write(f"[MODEL] {model}\n")
            f.write(f"[TIMESTAMP] {timestamp}\n")
            f.write(f"[SUCCESS] {success}\n")
            if error:
                f.write(f"[ERROR] {error}\n")
            f.write("\n" + "="*70 + "\n[RAW OUTPUT]\n" + "="*70 + "\n\n")
            f.write(llm_output)
        
        # Save parsed JSON if available
        if parsed is not None:
            parsed_file = stage_dir / f"{call_id}_parsed.json"
            with open(parsed_file, "w", encoding="utf-8") as f:
                json.dump({
                    "stage": stage,
                    "model": model,
                    "timestamp": timestamp,
                    "success": success,
                    "error": error,
                    "data": parsed
                }, f, indent=2, ensure_ascii=True)
        
        # Track call
        self.calls.append({
            "call_id": call_id,
            "stage": stage,
            "model": model,
            "timestamp": timestamp,
            "success": success,
            "error": error,
            "input_file": str(input_file),
            "output_file": str(output_file),
            "parsed_file": str(parsed_file) if parsed is not None else None
        })
        
        print(f"[DEBUG LOG] {stage} - {call_id}")
        print(f"  Input:  {input_file.name}")
        print(f"  Output: {output_file.name}")
        if parsed:
            print(f"  Parsed: {parsed_file.name}")
        if error:
            print(f"  Error:  {error}")
    
    def generate_report(self, output_file: Optional[str] = None) -> dict[str, Any]:
        """Generate summary report of all LLM calls."""
        report = {
            "generated_at": datetime.utcnow().isoformat(),
            "debug_directory": str(self.debug_dir),
            "total_calls": len(self.calls),
            "successful_calls": sum(1 for c in self.calls if c["success"]),
            "failed_calls": sum(1 for c in self.calls if not c["success"]),
            "stages": list(set(c["stage"] for c in self.calls)),
            "calls_by_stage": {},
            "calls": self.calls
        }
        
        # Group by stage
        for call in self.calls:
            stage = call["stage"]
            if stage not in report["calls_by_stage"]:
                report["calls_by_stage"][stage] = []
            report["calls_by_stage"][stage].append(call)
        
        # Save report
        if output_file is None:
            output_file = str(self.debug_dir / "llm_debug_report.json")
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2, ensure_ascii=True)
        
        print(f"\n[LLM DEBUG REPORT SAVED] {output_file}")
        print(f"  Total calls: {report['total_calls']}")
        print(f"  Successful: {report['successful_calls']}")
        print(f"  Failed: {report['failed_calls']}")
        print(f"  Stages: {report['stages']}")
        
        return report


# Global debug logger instance
_debug_logger: Optional[LLMDebugLogger] = None


def get_debug_logger(logs_dir: str = "logs") -> LLMDebugLogger:
    """Get or create global debug logger."""
    global _debug_logger
    if _debug_logger is None:
        _debug_logger = LLMDebugLogger(logs_dir)
    return _debug_logger


def reset_debug_logger() -> None:
    """Reset global debug logger."""
    global _debug_logger
    _debug_logger = None
