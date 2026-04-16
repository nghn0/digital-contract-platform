#!/usr/bin/env python
"""
LegalT - Legal Contract Intelligence System
Main CLI entrypoint for document analysis pipeline.

Usage:
    python main.py /path/to/contract.pdf [--verbose] [--trace] [--trace-log trace.json]
"""

import sys
import json
import argparse
from pathlib import Path

from services.pipeline import run_pipeline, print_pipeline_json
from services.pipeline_validation import hard_stop as pipeline_hard_stop
from services.tracing import initialize_tracer


def _slugify_doc_name(name: str) -> str:
    """Create a filesystem-safe document folder name."""
    safe = []
    for ch in name.strip().lower():
        if ch.isalnum() or ch in {"-", "_"}:
            safe.append(ch)
        elif ch.isspace() or ch in {".", "(" , ")"}:
            safe.append("_")
    slug = "".join(safe).strip("_")
    while "__" in slug:
        slug = slug.replace("__", "_")
    return slug or "document"


def _default_output_paths(input_file: Path) -> tuple[Path, Path]:
    """Return default result and trace paths under tests/outputs/<doc_name>/."""
    project_root = Path(__file__).resolve().parent
    base_dir = project_root / "tests" / "outputs" / _slugify_doc_name(input_file.stem)
    return base_dir / "result.json", base_dir / "trace.json"


def main():
    parser = argparse.ArgumentParser(
        description="LegalT Contract Analysis Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python main.py contract.pdf
    python main.py contract.pdf --verbose
    python main.py contract.pdf --output result.json
    python main.py contract.pdf --verbose --trace --trace-log trace.json
        """,
    )
    
    parser.add_argument(
        "file",
        help="Path to contract file (PDF, DOCX, or TXT)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed progress information",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output JSON file path (default: stdout)",
    )
    parser.add_argument(
        "--trace",
        "-t",
        action="store_true",
        help="Enable execution tracing with detailed logging",
    )
    parser.add_argument(
        "--trace-log",
        type=str,
        default=None,
        help="Save trace log to specified JSON file (requires --trace)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Halt immediately on any validation or pipeline error",
    )
    
    args = parser.parse_args()
    
    file_path = Path(args.file)
    if not file_path.exists():
        print(f"ERROR: File not found: {file_path}")
        sys.exit(1)
    
    if file_path.suffix.lower() not in [".pdf", ".docx", ".doc", ".txt"]:
        print(f"ERROR: Unsupported file type: {file_path.suffix}")
        sys.exit(1)

    default_output_path, default_trace_path = _default_output_paths(file_path)

    # Keep explicit CLI values; otherwise default to structured outputs.
    output_path = Path(args.output) if args.output else default_output_path
    trace_log_path = Path(args.trace_log) if args.trace_log else (default_trace_path if args.trace else None)

    # Initialize tracer if requested
    if args.trace or trace_log_path:
        initialize_tracer(verbose=args.trace, log_file=str(trace_log_path) if trace_log_path else None)

    print("=" * 70)
    print("LegalT Contract Intelligence System")
    print("=" * 70)
    
    try:
        result = run_pipeline(str(file_path), verbose=args.verbose)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(result, indent=2))
        print(f"\n✓ Analysis complete! Output saved to: {output_path}")
        if args.verbose:
            print_pipeline_json(result)
        
        # Save trace log if requested
        if trace_log_path:
            from services.tracing import get_tracer
            trace_log_path.parent.mkdir(parents=True, exist_ok=True)
            get_tracer().save_trace_log(str(trace_log_path))
        
        print("\n" + "=" * 70)
        print("✓ Pipeline completed successfully")
        print("=" * 70)
        
        return 0
    
    except KeyboardInterrupt:
        print("\n\n⚠ Pipeline interrupted by user")
        return 130
    
    except Exception as e:
        if args.strict:
            print(f"\n[STRICT MODE] Pipeline failed: {str(e)}")
            pipeline_hard_stop()
        print(f"\n✗ Pipeline failed: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
