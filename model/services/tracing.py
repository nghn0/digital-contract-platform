"""
Comprehensive tracing and logging system for LegalT pipeline.
Tracks LLM inputs/outputs, KB queries, and intermediate processing steps.
"""

import json
import sys
from datetime import datetime
from typing import Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict


@dataclass
class TraceEvent:
    """Single event in the execution trace."""
    timestamp: str
    stage: str
    event_type: str  # 'kb_query', 'llm_call', 'extraction', 'validation', etc.
    description: str
    details: dict[str, Any]


class ExecutionTracer:
    """Centralized tracing system for the pipeline."""
    
    def __init__(self, verbose: bool = True, log_file: Optional[str] = None):
        self.verbose = verbose
        self.events: list[TraceEvent] = []
        self.log_file = log_file
        
    def trace(
        self,
        stage: str,
        event_type: str,
        description: str,
        details: Optional[dict[str, Any]] = None,
    ) -> None:
        """Record a trace event."""
        event = TraceEvent(
            timestamp=datetime.now().isoformat(),
            stage=stage,
            event_type=event_type,
            description=description,
            details=details or {},
        )
        self.events.append(event)
        
        if self.verbose:
            self._print_event(event)
            
    def _safe_print(self, *args, **kwargs) -> None:
        """Print to stdout while catching potential I/O errors (Errno 5)."""
        try:
            print(*args, **kwargs)
        except OSError:
            # Silently ignore if stdout is broken (broken pipe, disconnected terminal)
            pass
    
    def _print_event(self, event: TraceEvent) -> None:
        """Pretty print a trace event."""
        color_map = {
            'kb_query': '\033[94m',      # Blue
            'kb_result': '\033[92m',     # Green
            'llm_call': '\033[93m',      # Yellow
            'llm_response': '\033[92m',  # Green
            'extraction': '\033[96m',    # Cyan
            'validation': '\033[95m',    # Magenta
            'error': '\033[91m',         # Red
        }
        reset = '\033[0m'
        if event.details:
            self._safe_print("  Details:")
            for key, value in event.details.items():
                if isinstance(value, (list, dict)):
                    self._safe_print(f"    {key}:")
                    try:
                        formatted = json.dumps(value, indent=6)[:500]
                        self._safe_print(f"      {formatted}")
                    except:
                        self._safe_print(f"      {str(value)[:500]}")
                else:
                    self._safe_print(f"    {key}: {str(value)[:200]}")
    
    def trace_kb_query(
        self,
        stage: str,
        collection: str,
        query: str,
        n_results: int,
    ) -> None:
        """Trace a knowledge base query."""
        self.trace(
            stage=stage,
            event_type='kb_query',
            description=f"Querying KB collection: {collection}",
            details={
                'collection': collection,
                'query': query[:200],
                'n_results': n_results,
            }
        )
    
    def trace_kb_result(
        self,
        stage: str,
        collection: str,
        num_results: int,
        results: list[str],
    ) -> None:
        """Trace knowledge base query results."""
        self.trace(
            stage=stage,
            event_type='kb_result',
            description=f"KB result: {collection} - {num_results} documents",
            details={
                'collection': collection,
                'num_results': num_results,
                'result_preview': [r[:150] for r in results[:2]],
            }
        )
    
    def trace_llm_call(
        self,
        stage: str,
        system_prompt: str,
        user_message: str,
        model: str,
        temperature: float,
        max_tokens: int,
    ) -> None:
        """Trace an LLM API call."""
        self.trace(
            stage=stage,
            event_type='llm_call',
            description=f"Calling LLM: {model}",
            details={
                'model': model,
                'temperature': temperature,
                'max_tokens': max_tokens,
                'system_prompt_preview': system_prompt[:200],
                'user_message_preview': user_message[:300],
                'total_message_length': len(user_message),
            }
        )
    
    def trace_llm_response(
        self,
        stage: str,
        response_text: str,
        parsed_json: Optional[dict[str, Any]] = None,
    ) -> None:
        """Trace an LLM response."""
        preview = response_text[:300] if response_text else "[empty]"
        parsed_json_keys: Optional[Any] = None
        if parsed_json is not None:
            if isinstance(parsed_json, dict):
                parsed_json_keys = list(parsed_json.keys())
            elif isinstance(parsed_json, list):
                parsed_json_keys = ["<list>", f"items={len(parsed_json)}"]
            else:
                parsed_json_keys = [f"<{type(parsed_json).__name__}>"]
        
        self.trace(
            stage=stage,
            event_type='llm_response',
            description="LLM response received",
            details={
                'response_length': len(response_text),
                'response_preview': preview,
                'parsed_json_keys': parsed_json_keys,
                'parse_success': parsed_json is not None,
            }
        )
    
    def trace_extraction(
        self,
        stage: str,
        entity_type: str,
        count: int,
        sample: Optional[Any] = None,
    ) -> None:
        """Trace extracted entities."""
        self.trace(
            stage=stage,
            event_type='extraction',
            description=f"Extracted {entity_type}: {count} items",
            details={
                'entity_type': entity_type,
                'count': count,
                'sample': str(sample)[:200] if sample else None,
            }
        )
    
    def trace_validation(
        self,
        stage: str,
        validation_type: str,
        passed: bool,
        issues: Optional[list[str]] = None,
    ) -> None:
        """Trace validation results."""
        self.trace(
            stage=stage,
            event_type='validation',
            description=f"Validation {'PASSED' if passed else 'FAILED'}: {validation_type}",
            details={
                'validation_type': validation_type,
                'passed': passed,
                'issues': issues[:5] if issues else [],
            }
        )
    
    def trace_error(
        self,
        stage: str,
        error_message: str,
        error_type: str,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        """Trace an error."""
        self.trace(
            stage=stage,
            event_type='error',
            description=f"ERROR in {error_type}",
            details={
                'error_type': error_type,
                'error_message': error_message,
                'context': context or {},
            }
        )
    
    def get_trace_summary(self) -> dict[str, Any]:
        """Get a summary of all trace events."""
        by_type = {}
        by_stage = {}
        
        for event in self.events:
            # Count by type
            if event.event_type not in by_type:
                by_type[event.event_type] = []
            by_type[event.event_type].append(event)
            
            # Count by stage
            if event.stage not in by_stage:
                by_stage[event.stage] = []
            by_stage[event.stage].append(event)
        
        return {
            'total_events': len(self.events),
            'events_by_type': {k: len(v) for k, v in by_type.items()},
            'events_by_stage': {k: len(v) for k, v in by_stage.items()},
            'timeline': [asdict(e) for e in self.events],
        }
    
    def save_trace_log(self, output_file: str) -> None:
        """Save trace log to a JSON file."""
        summary = self.get_trace_summary()
        with open(output_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        print(f"\n[OK] Trace log saved to: {output_file}")
    
    def print_summary(self) -> None:
        """Print a summary of trace events."""
        summary = self.get_trace_summary()
        self._safe_print("\n" + "=" * 70)
        self._safe_print("EXECUTION TRACE SUMMARY")
        self._safe_print("=" * 70)
        self._safe_print(f"Total Events: {summary['total_events']}")
        self._safe_print("\nEvents by Type:")
        for event_type, count in summary['events_by_type'].items():
            self._safe_print(f"  - {event_type}: {count}")
        self._safe_print("\nEvents by Stage:")
        for stage, count in summary['events_by_stage'].items():
            self._safe_print(f"  - {stage}: {count}")


# Global tracer instance
_GLOBAL_TRACER: Optional[ExecutionTracer] = None


def get_tracer() -> ExecutionTracer:
    """Get or create the global tracer instance."""
    global _GLOBAL_TRACER
    if _GLOBAL_TRACER is None:
        _GLOBAL_TRACER = ExecutionTracer(verbose=True)
    return _GLOBAL_TRACER


def initialize_tracer(verbose: bool = True, log_file: Optional[str] = None) -> ExecutionTracer:
    """Initialize the global tracer with options."""
    global _GLOBAL_TRACER
    _GLOBAL_TRACER = ExecutionTracer(verbose=verbose, log_file=log_file)
    return _GLOBAL_TRACER
