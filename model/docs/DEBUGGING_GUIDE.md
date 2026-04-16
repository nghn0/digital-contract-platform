"""
DEBUGGING & VALIDATION GUIDE

This document explains the new strict validation and debugging system
that prevents silent fallbacks and ensures LLM is always used.

═══════════════════════════════════════════════════════════════════════

1. HOW THE NEW SYSTEM WORKS
═══════════════════════════════════════════════════════════════════════

The pipeline now has THREE validation layers:

  [Layer 1] LLM Wrapper
  ├─ Log all inputs/outputs
  ├─ Reject JSON parsing failures
  └─ Detect generic/fallback markers

  [Layer 2] Strict Validation (services/pipeline_validation.py)
  ├─ Check response isn't generic
  ├─ Verify JSON structure
  ├─ Validate Pydantic schema
  └─ Compare against expected schema

  [Layer 3] Stage Validation (services/strict_pipeline.py)
  ├─ Validate each clause individually
  ├─ Check completeness (min items)
  ├─ Hard stop on first failure
  └─ Generate forensic logs

═══════════════════════════════════════════════════════════════════════

2. KEY PRINCIPLES
═══════════════════════════════════════════════════════════════════════

✓ ALWAYS call LLM - no silent fallbacks
✓ ALWAYS validate output - reject generic responses
✓ ALWAYS show errors - don't hide failures
✓ ALWAYS save debug files - for forensic analysis
✓ HARD STOP on failure - don't continue after error

═══════════════════════════════════════════════════════════════════════

3. RUNNING WITH STRICT VALIDATION
═══════════════════════════════════════════════════════════════════════

Command:
  python main.py document.pdf --strict --debug

Flags:
  --strict     Enable strict validation mode (halt on error)
  --debug      Enable verbose output
  --trace      Enable execution tracing
  --trace-log  Save trace to file

═══════════════════════════════════════════════════════════════════════

4. DEBUG FILE LOCATIONS
═══════════════════════════════════════════════════════════════════════

All debug files saved to: logs/llm_debug/

Structure:
  logs/llm_debug/
  ├── stage_1_ingestion/
  │   ├── stage_1_000_[timestamp]_input.txt
  │   ├── stage_1_000_[timestamp]_output.txt
  │   └── stage_1_000_[timestamp]_parsed.json
  ├── stage_2_segmentation/
  │   ├── stage_2_000_[timestamp]_input.txt
  │   ├── stage_2_000_[timestamp]_output.txt
  │   └── stage_2_000_[timestamp]_parsed.json
  └── llm_debug_report.json

Each call creates THREE files:
  - input.txt   → Full LLM prompt
  - output.txt  → Raw LLM response
  - parsed.json → Parsed + validated JSON

═══════════════════════════════════════════════════════════════════════

5. UNDERSTANDING ERROR MESSAGES
═══════════════════════════════════════════════════════════════════════

[LLM CALL] Stage: clause_extraction
  → LLM call initiating

[LLM INPUT] (2000 chars shown)
  → Full prompt being sent to LLM

[LLM OUTPUT RAW] (2000 chars shown)
  → Raw response from LLM

[JSON VALIDATION] Stage: clause_extraction
  → Parsing JSON response

[FAKE OUTPUT DETECTION] Stage: clause_extraction
  ✗ GENERIC MARKER: 'fallback explanation generated'
  → Response contains fallback marker - RAISING ERROR

[SCHEMA VALIDATION] Stage: clause_extraction | Type: Clause
  → Validating against Pydantic schema

[CLAUSE SCHEMA VALIDATION] Stage: stage_2
  ✗ RISK SCORE OUT OF BOUNDS: 150
  → Schema constraint violated (0-100 required)

[EXTRACTION COMPLETENESS CHECK] Stage: stage_2
  ✗ INSUFFICIENT CLAUSES: 0 < 1
  → No clauses extracted from document

═══════════════════════════════════════════════════════════════════════

6. PIPELINE VALIDATION METRICS
═══════════════════════════════════════════════════════════════════════

Printed at end of run:

  PIPELINE VALIDATION METRICS
  ════════════════════════════════════════════
  [LLM CALLS]        42
  [LLM FAILURES]     2
  [SCHEMA FAILURES]  1
  [FALLBACK MARKED]  3
  [STAGES PASSED]    ['stage_1', 'stage_2']
  [STAGES FAILED]    ['stage_3']

═══════════════════════════════════════════════════════════════════════

7. WHAT HAPPENS ON FAILURE
═══════════════════════════════════════════════════════════════════════

BEFORE (Old System):
  - LLM fails silently
  - Fallback logic triggered without notice
  - Output appears valid but is synthetic
  - No way to know something went wrong

AFTER (New System):
  - LLM fails → caught immediately
  - Error printed with full context
  - Debug files saved for analysis
  - Pipeline HALTS with exit code 1
  - Metrics report shows exactly what failed

═══════════════════════════════════════════════════════════════════════

8. COMMON FAILURE MODES & FIXES
═══════════════════════════════════════════════════════════════════════

FAILURE: Invalid JSON from LLM
  CAUSE:  LLM returned text instead of JSON
  FIX:    Check temperature setting (should be 0.0)
          Verify prompt includes "return ONLY JSON"
          Check model supports function calling

FAILURE: Schema validation failed
  CAUSE:  risk_score out of bounds, missing required fields
  FIX:    Update LLM prompt to enforce constraints
          Add explicit validation rules to prompt

FAILURE: Generic marker detected
  CAUSE:  LLM returned fallback explanation
  FIX:    Make prompt more specific
          Provide better examples in KB context

FAILURE: Insufficient clauses extracted
  CAUSE:  Document had poor structure or LLM missed clauses
  FIX:    Check input document is readable
          Verify segmentation stage extracted text properly

═══════════════════════════════════════════════════════════════════════

9. FORENSIC ANALYSIS WORKFLOW
═══════════════════════════════════════════════════════════════════════

Step 1: Run pipeline with --strict
  python main.py document.pdf --strict --debug

Step 2: Check which stage failed
  Look at printed error message and stage name

Step 3: Open debug files
  logs/llm_debug/stage_X/
  - input.txt:   Review prompt sent to LLM
  - output.txt:  See raw response
  - parsed.json: Check parsed structure

Step 4: Identify issue
  - Is prompt clear?
  - Did LLM understand (check raw output)?
  - Does response match schema?

Step 5: Fix and retry
  - Adjust prompt in core/prompts.py
  - Update KB context
  - Modify schema constraints
  - Re-run with --strict

═══════════════════════════════════════════════════════════════════════

10. CODE INTEGRATION EXAMPLES
═══════════════════════════════════════════════════════════════════════

Using strict validation in your own code:

  from services.strict_pipeline import validate_llm_clause_response
  from services.pipeline_validation import validate_stage_output

  # After LLM call:
  clause_dict = validate_llm_clause_response(
      stage="my_stage",
      llm_input=prompt,
      llm_raw_output=response_text
  )

  # After extraction:
  validate_stage_output(
      stage_name="clause_extraction",
      output=clauses,
      schema_class=Clause,
      min_items=5
  )

═══════════════════════════════════════════════════════════════════════

11. DISABLING FALLBACKS PERMANENTLY
═══════════════════════════════════════════════════════════════════════

To remove all fallback code from the system:

  grep -r "_fallback\\|fallback_used\\|FALLBACK" services/
  
Remove or replace with:
  from services.pipeline_validation import abort_no_fallback
  
  abort_no_fallback(
      stage="example_stage",
      reason="LLM response invalid",
      debug_data={"response": response_text}
  )

═══════════════════════════════════════════════════════════════════════

12. METRICS & REPORTING
═══════════════════════════════════════════════════════════════════════

Automatically generated:

  logs/llm_debug/llm_debug_report.json
  
Contains:
  - Total LLM calls
  - Success/failure count
  - Calls grouped by stage
  - Timestamp
  - File locations for each call

═══════════════════════════════════════════════════════════════════════
"""

print(__doc__)
