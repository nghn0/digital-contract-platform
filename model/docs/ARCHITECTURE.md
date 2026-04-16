# LegalT Architecture (Code-Accurate)

Last updated: 2026-04-12
Status: aligned to current repository files and active execution path.

## 1. What The System Does

LegalT ingests legal documents (PDF, DOCX/DOC, TXT), segments text into clauses, runs a multi-pass LLM extraction pipeline with local KB grounding, validates the output against strict schema and quality rules, and returns a normalized `LegalDocumentAnalysis` JSON.

Primary entry points:
- CLI: `main.py`
- API: `api/routes.py` (`POST /analyze`)

## 2. High-Level Runtime Flow

```text
Input File
	-> main.py / api/routes.py
	-> services.pipeline.run_pipeline()
			Stage 0: input + provider/API-key validation
			Stage 1: services.ingestion.extract_text()
			Stage 2: services.segmentation.segment_clauses()
			Stage 3: services.extractor.run_full_extraction()
					Pass 1: metadata + parties
					Pass 2: per-clause extraction + KB context
					Pass 3: obligations/rights/timelines
					Pass 4: financial terms (rule/regex synthesis)
					Pass 5: risks/missing clauses/dependencies/negotiation/compliance/summary
					Pass 6: assemble LegalDocumentAnalysis
			Stage 4: services.validator.validate_and_clean()
	-> final JSON output (CLI file/stdout or API response)
```

Observability across stages is provided by `services.tracing.ExecutionTracer`.

## 3. Layered Architecture

### Layer A: Interface Layer
- `main.py`
- `api/routes.py`

Responsibilities:
- Input contract file acceptance and basic type checks.
- Path/trace/output setup (CLI).
- Upload size/time limits and safe temp-file handling (API).

### Layer B: Orchestration Layer
- `services/pipeline.py`

Responsibilities:
- Orchestrates Stage 0 through Stage 4.
- Emits trace events for each stage.
- Calls extraction and post-validation services.

### Layer C: Processing + Extraction Layer
- `services/ingestion.py`
- `services/segmentation.py`
- `services/extractor.py`

Responsibilities:
- Parse source file text.
- Segment text into heading/body clause units.
- Run multi-pass intelligence extraction and compose final typed model.

### Layer D: Knowledge + Prompt Layer
- `services/rag_service.py` (re-exported through `services/rag.py`)
- `core/prompts.py`

Responsibilities:
- Retrieve relevant legal context from local JSON KB collections.
- Provide strict JSON-output prompts for each pass.

### Layer E: Configuration + Validation Layer
- `core/llm_config.py`
- `services/validator.py`
- `models/schema.py`
- `services/pipeline_validation.py` and `services/extractor_strict_integration.py` (strict-mode helpers)

Responsibilities:
- Provider/model/API-key resolution and unified request adapters.
- Output completeness and semantic validation.
- Pydantic schema contract for all entities.

## 4. Method-Level Module Guide

This section lists the main methods used throughout the active system path.

### 4.1 CLI and API

`main.py`
- `_slugify_doc_name(name)`
	- Creates deterministic folder-safe output names.
- `_default_output_paths(input_file)`
	- Defaults outputs to `tests/outputs/<doc_slug>/result.json` and `trace.json`.
- `main()`
	- Parses args, validates file extension, initializes tracing, invokes `run_pipeline`, writes output/trace.

`api/routes.py`
- `analyze_contract(file)`
	- Validates MIME type, extension, filename length, upload size.
	- Writes to `TemporaryDirectory`, runs `run_pipeline` in worker thread with timeout.
	- Returns `LegalDocumentAnalysis` response model.
- `get_report(document_id)`
	- Stub endpoint for future persistence lookup.

### 4.2 Orchestration

`services/pipeline.py`
- `run_pipeline(file_path, verbose=False)`
	- Stage 0: file + extension + active API key validation.
	- Stage 1: text extraction via `extract_text`.
	- Stage 2: segmentation via `segment_clauses`.
	- Stage 3: extraction via `run_full_extraction`.
	- Stage 4: strict validation and normalization via `validate_and_clean`.
	- Returns validated dictionary payload.
- `print_pipeline_json(result)`
	- Pretty prints final JSON in CLI verbose mode.

### 4.3 Ingestion + Segmentation

`services/ingestion.py`
- `extract_text(file_path)`
	- Dispatches by suffix (`.pdf`, `.docx/.doc`, `.txt`).
- `extract_raw_pages(file_path)`
	- Page-preserving extraction helper used by stage/debug flows.
- `_extract_pdf(path)`
	- Primary extractor via `pdfplumber`, fallback via `pypdf`.
- `_extract_pdf_pages(path)`
	- Page-wise variant with same fallback behavior.
- `_extract_docx(path)`
	- Extracts non-empty paragraphs with `python-docx`.
- `_clean_text(text)`
	- Normalizes whitespace and removes page-number artifacts.

`services/segmentation.py`
- `segment_clauses(text)`
	- Regex heading strategy first; paragraph fallback when headings are sparse.
	- Returns `list[(heading, body)]`.
- `chunk_for_context(text, max_chars=6000)`
	- Overlapping chunk utility for long-context workflows.

### 4.4 Core Extraction Pipeline

`services/extractor.py`

Utility/normalization methods:
- `_parse_json_from_text(raw_text)`
- `_normalize_document_type(value)`
- `_normalize_category(value)`
- `_normalize_risk_level(value)`
- `_coerce_str_list(value)`
- `_document_type_text(document_type)`

Profile/intelligence graphing methods:
- `_build_document_profile(metadata, clauses)`
	- Enriches metadata with KB template expectations and confidence score.
- `_derive_risk_labels(risk_type, reason, clause_text='')`
- `_build_clause_dependency_graph(clauses, dependencies)`
- `_build_linked_documents(metadata, document_profile, clauses)`

LLM execution methods:
- `call_llm(system, user_message, json_mode=True)`
	- Unified client call, strict JSON parsing, one parse-retry path.

Pass implementations:
- `extract_metadata_and_parties(contract_text)`
	- Pass 1: metadata + parties.
- `extract_clauses(clauses_with_headings, metadata, parties)`
	- Pass 2: per-clause extraction with RAG injection.
- `_extract_obligations_rights_timelines(contract_text, parties, clauses)`
	- Pass 3 with fallback derivation from clause fields when needed.
- `_build_financial_terms(clauses)`
	- Pass 4 regex/rule synthesis for payment/liability signals.
- `_extract_pass5_intelligence(contract_text, metadata, document_profile, parties, clauses, obligations, rights, timelines)`
	- Pass 5 split prompts for risks, missing/dependencies, negotiation/compliance, summary.
- `_materialize_intelligence(intelligence, clauses, document_profile)`
	- Converts raw pass-5 JSON into typed objects and performs profile-based backfill logic.

Completion method:
- `_enforce_completeness(document)`
	- Ensures critical arrays and summary actions are non-empty.

Entrypoint:
- `run_full_extraction(contract_text, segmented_clauses)`
	- Runs Pass 1-6, builds `LegalDocumentAnalysis`, enforces completeness.

### 4.5 KB Retrieval Methods

`services/rag_service.py` (active KB engine used by extraction)

Core retrieval internals:
- `_load_collection_entries(collection_key)`
- `_tokenize(text)`
- `_entry_text(entry)`
- `_score_entry(query_tokens, entry)`
- `_query_collection(collection_key, query, n_results=3, where=None)`

Pass-specific retrieval APIs:
- `get_clause_classification_context(clause_text, n=3)`
- `get_risk_scoring_context(clause_text, clause_type='', n=4)`
- `get_missing_clauses_context(document_type)`
- `get_document_template_profile(document_type)`
- `get_negotiation_context(risk_type, clause_type='', n=3)`
- `get_compliance_context(contract_text_snippet, jurisdiction='General')`
- `get_plain_english_context(legal_term)`
- `get_full_pass2_context(clause_text, clause_type='')`
- `get_full_pass5_context(contract_text, document_type, jurisdiction, identified_risks)`

Compatibility helpers:
- `retrieve_context(query_text, n_results=5)`
- `retrieve_context_for_clause(clause_text, clause_heading)`
- `initialize_kb()`

`services/rag.py` re-exports these methods for compatibility.

### 4.6 Validation and Quality Gates

`services/validator.py`
- `_is_invalid_party_name(name)` and `is_valid_party_name(name)`
	- Enforces party-name hygiene.
- `validate_clause_output(clause_json)`
	- Guardrails clause object quality.
- `validate_analysis_output(output)`
	- Checks required coverage and required-clause presence.
- `validate_and_clean(raw)`
	- Applies final non-empty constraints, summary checks, schema instantiation.

`services/pipeline_validation.py` (strict/diagnostic toolkit)
- `validate_json_response(response_text, stage)`
- `detect_generic_response(response_text, parsed, stage)`
- `validate_schema(data, schema_class, stage, item_name='item')`
- `validate_schema_list(items, schema_class, stage)`
- `validate_stage_output(stage_name, output, schema_class=None, min_items=1)`
- `abort_no_fallback(stage, reason, debug_data=None)`
- `save_stage_debug_files(stage, llm_input, llm_output, parsed, logs_dir='logs')`
- `hard_stop(stage, error_message, exit_code=1)`

`services/extractor_strict_integration.py`
- `validate_clause_extraction(...)`
- `validate_metadata_extraction(...)`
- `validate_pipeline_stage(...)`
- `is_fallback_marker(text)`
- `assert_no_fallback(...)`

### 4.7 Tracing and Observability

`services/tracing.py`
- `ExecutionTracer.trace(...)`
- `ExecutionTracer.trace_kb_query(...)`
- `ExecutionTracer.trace_kb_result(...)`
- `ExecutionTracer.trace_llm_call(...)`
- `ExecutionTracer.trace_llm_response(...)`
- `ExecutionTracer.trace_extraction(...)`
- `ExecutionTracer.trace_validation(...)`
- `ExecutionTracer.trace_error(...)`
- `ExecutionTracer.get_trace_summary()`
- `ExecutionTracer.save_trace_log(output_file)`
- `ExecutionTracer.print_summary()`
- `get_tracer()` and `initialize_tracer(...)`

## 5. Data Contract (Schema Backbone)

The final payload is `models.schema.LegalDocumentAnalysis`, which composes:
- `DocumentMetadata`
- `DocumentProfile`
- `PartiesSection`
- `FinancialTerms`
- `LinkedDocument[]`
- `Clause[]`
- `RiskItem[]`
- `Obligation[]`
- `Right[]`
- `TimelineEvent[]`
- `ClauseDependency[]`
- `MissingClause[]`
- `NegotiationPoint[]`
- `ComplianceFlag[]`
- `dependency_graph` (derived topology)
- `DocumentSummary`

Enums central to deterministic behavior:
- `RiskLevel`
- `ClauseCategory`
- `DocumentType`
- `RiskType`

## 6. LLM Provider and Prompt Architecture

`core/llm_config.py` provides:
- Provider registry and API key mapping (`get_provider_spec`, `get_required_api_key_name`, `has_active_api_key`).
- Model routing (`get_active_model_name`, `get_stage_model_name`).
- Unified message and embedding adapters (`UnifiedLLMClient`, `get_llm_client`, `get_embedding_vectors`).
- Retry/timeout handling and provider-specific request shaping.

`core/prompts.py` defines strict JSON-oriented prompts:
- `SYSTEM_PROMPT`
- `PASS_1_METADATA_PARTIES`
- `PASS_2_CLAUSES`
- `PASS_3_OBLIGATIONS`
- `PASS_4_FINANCIAL`
- `PASS_5_INTELLIGENCE`

Note: the active extraction path currently uses Passes 1, 2, 3, and 5 as LLM prompts, and computes financial terms in code for Pass 4.

## 7. Security and Runtime Constraints

Implemented protections in active path:
- API upload size limit: 50 MB.
- API request timeout: 300 seconds.
- Temporary-directory file handling for uploads.
- Allowed extension gate: `.pdf`, `.docx`, `.doc`, `.txt`.
- Active provider API key required at Stage 0.

Related runtime controls:
- `config/runtime_limits.py` for token and feature limits.
- `core/rate_limit_decorator.py` and `utils/rate_limiter.py` for provider throttling support.

## 8. File/Folder Notes (Current State)

- Knowledge files are read from `knowledge-base/*.json` via `services/rag_service.py`.
- `knowledge-base/chroma_db/` exists, but active retrieval is JSON keyword scoring, not direct Chroma vector querying in runtime extraction.
- Test coverage exists under `tests/` for schema, ingestion, segmentation, token utils, and validation utilities.

## 9. Extension Guidance

When extending the system, preserve these invariants:
- Keep `run_pipeline` as the single orchestration gateway for both CLI and API.
- Keep all output shape changes synchronized with `models/schema.py`, prompts, extractor materialization, and validator checks.
- Keep pass outputs strict-JSON and non-empty for required sections.
- Add new trace events for any new stage or high-impact branch.

Recommended extension points:
- Add/adjust prompt contracts in `core/prompts.py`.
- Add schema entities in `models/schema.py`.
- Extend pass logic in `services/extractor.py`.
- Add KB collections and retrieval methods in `services/rag_service.py`.
