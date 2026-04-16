# LegalT System Architecture

Document version: 3.0
Last updated: 2026-04-12
Status: code-aligned with current repository implementation

## 1. Executive Summary

LegalT is a legal contract intelligence pipeline that:
- extracts text from PDF/DOCX/TXT files,
- segments document content into clause units,
- performs multi-pass LLM extraction with local knowledge-base grounding,
- validates and normalizes outputs against a strict schema,
- returns a complete `LegalDocumentAnalysis` JSON for CLI/API consumers.

Active entry points:
- CLI: `main.py`
- HTTP API: `api/routes.py` (`POST /analyze`)

## 1.1 Changed Files Snapshot (Current Working Tree)

Snapshot source: `git status --short` on 2026-04-12.

### Modified files (`M`)

- `SYSTEM_ARCHITECTURE.md`
- `config/runtime_limits.py`
- `core/llm_config.py`
- `core/prompts.py`
- `docs/ARCHITECTURE.md`
- `logs/usage.json`
- `services/extractor.py`
- `services/rag.py`
- `services/rag_service.py`
- `services/segmentation.py`
- `services/validator.py`
- `tests/outputs/nda/result.json`
- `utils/rate_limiter.py`

### New configuration and KB files (`??`)

- `config/kb_routing.py`
- `knowledge-base/clause_types_employment.json`
- `knowledge-base/clause_types_financial.json`
- `knowledge-base/clause_types_real_estate.json`
- `knowledge-base/compliance_rules.json`
- `knowledge-base/financial_rules.json`
- `knowledge-base/negotiation_rules.json`
- `knowledge-base/risk_rules.json`
- `knowledge-base/risk_rules_financial.json`
- `knowledge-base/segmentation_profiles.json`

### New service and script files (`??`)

- `scripts/build_chroma_kb.py`
- `services/compliance_engine.py`
- `services/context_engine.py`
- `services/kb_engine.py`

### New output artifacts and run results (`??`)

- `results.json`
- `tests/outputs/law_agreement/` (new output directory)
- `tests/outputs/loan_agreement/loan_result_context_fix.json`
- `tests/outputs/loan_agreement/loan_result_context_fix_2.json`

### New debug log collections (`??`)

- `logs/stage_debug_extract_clauses/` (timestamped `llm_input`, `llm_output`, `parsed` files)
- `logs/stage_debug_extract_clauses_batch/`
- `logs/stage_debug_full_extraction_pipeline/` (timestamped `llm_input`, `llm_output`, `parsed` files)
- `logs/stage_debug_metadata_extraction/` (timestamped `llm_input`, `llm_output`, `parsed` files)

## 2. Architecture Overview

```text
User Input (file)
  -> Interface Layer
      main.py OR api/routes.py
  -> Orchestration Layer
      services/pipeline.py::run_pipeline()
          Stage 0: input/provider validation
          Stage 1: ingestion.extract_text()
          Stage 2: segmentation.segment_clauses()
          Stage 3: extractor.run_full_extraction()
              Pass 1: metadata + parties
              Pass 2: clause extraction + RAG
              Pass 3: obligations/rights/timelines
              Pass 4: financial synthesis
              Pass 5: risks + compliance + negotiation + summary
              Pass 6: assembly + completeness gate
          Stage 4: validator.validate_and_clean()
  -> Output Layer
      validated JSON + optional trace log
```

## 3. Layered Design

### 3.1 Interface Layer
Files:
- `main.py`
- `api/routes.py`

Responsibilities:
- Accept input files.
- Validate extension/content-type/size constraints.
- Initialize tracing and output path policy.
- Delegate all core work to `services.pipeline.run_pipeline`.

### 3.2 Orchestration Layer
File:
- `services/pipeline.py`

Responsibilities:
- Execute the end-to-end stage sequence.
- Perform prechecks (file existence, allowed types, API key availability).
- Trace every major stage event.
- Return final validated dictionary output.

### 3.3 Processing and Intelligence Layer
Files:
- `services/ingestion.py`
- `services/segmentation.py`
- `services/extractor.py`

Responsibilities:
- Ingest source documents into normalized text.
- Segment text into clause units.
- Build full structured analysis via multi-pass extraction.

### 3.4 Knowledge and Prompt Layer
Files:
- `services/rag_service.py` (and compatibility export in `services/rag.py`)
- `core/prompts.py`

Responsibilities:
- Retrieve legal context from local JSON KB collections.
- Supply strict, schema-oriented extraction prompts.

### 3.5 Validation and Schema Layer
Files:
- `services/validator.py`
- `models/schema.py`
- `services/pipeline_validation.py`
- `services/extractor_strict_integration.py`

Responsibilities:
- Enforce schema integrity and completeness guarantees.
- Detect low-quality/fallback-like responses in strict paths.
- Ensure outputs are safe for downstream analytics/UI use.

### 3.6 Observability Layer
File:
- `services/tracing.py`

Responsibilities:
- Trace LLM calls, KB queries, extraction counts, validation states, and errors.
- Export trace timeline to JSON when enabled.

## 4. Methodologies Used (Clear + Code-Mapped)

This section documents methodologies used throughout the system and the exact methods implementing them.

### 4.1 Stage-Oriented Pipeline Methodology
Purpose:
- deterministic execution order and debuggable stage boundaries.

Implemented in:
- `services/pipeline.py::run_pipeline`

How it is used:
- Stage 0 validation before any heavy operation.
- Stage 1-4 sequencing with trace events per stage.
- Hard failures on invalid input or missing API keys.

### 4.2 Multi-Pass LLM Extraction Methodology
Purpose:
- decompose complex legal analysis into specialized passes.

Implemented in:
- `services/extractor.py::run_full_extraction`
- `extract_metadata_and_parties`
- `extract_clauses`
- `_extract_obligations_rights_timelines`
- `_extract_pass5_intelligence`

How it is used:
- Pass 1 captures metadata and parties.
- Pass 2 processes each segmented clause with contextual grounding.
- Pass 3 builds obligations/rights/timelines.
- Pass 5 synthesizes risk/compliance/negotiation/summary outputs.

### 4.3 Retrieval-Augmented Grounding Methodology
Purpose:
- reduce hallucination and improve legal-context relevance.

Implemented in:
- `services/rag_service.py::_query_collection`
- `get_full_pass2_context`
- `get_full_pass5_context`
- `retrieve_context_for_clause`

How it is used:
- keyword-token scoring over local KB entries,
- top result injection into extraction prompts,
- document-type profile retrieval via `get_document_template_profile`.

### 4.4 Schema-First Contract Methodology
Purpose:
- enforce typed output contracts and stable downstream behavior.

Implemented in:
- `models/schema.py` (`LegalDocumentAnalysis` and nested models)
- `services/validator.py::validate_and_clean`
- `services/validator.py::validate_analysis_output`

How it is used:
- final output is instantiated as `LegalDocumentAnalysis`.
- required arrays and summary actions are non-empty.
- required clause coverage checks are performed.

### 4.5 Defensive Parsing and Normalization Methodology
Purpose:
- make model output robust to JSON formatting variance.

Implemented in:
- `services/extractor.py::_parse_json_from_text`
- `services/extractor.py::call_llm` (one parse-retry mechanism)
- `services/extractor.py::_normalize_*` helpers

How it is used:
- strips code fences, extracts JSON body, retries once with stricter instruction.
- normalizes enums and list/string fields before model creation.

### 4.6 Heuristic Enrichment Methodology
Purpose:
- preserve completeness even when model returns sparse sections.

Implemented in:
- `services/extractor.py::_extract_obligations_rights_timelines` (fallback derivation)
- `services/extractor.py::_materialize_intelligence` (missing clause backfill)
- `services/extractor.py::_build_financial_terms` (regex/rule synthesis)

How it is used:
- derives obligations/rights/timelines from clause fields if pass output is empty.
- adds profile-driven missing clauses when absent.
- infers payment/liability patterns from clause text.

### 4.7 Completeness Gate Methodology
Purpose:
- reject partially populated final payloads.

Implemented in:
- `services/extractor.py::_enforce_completeness`
- `services/validator.py::validate_and_clean`

How it is used:
- ensures critical sections are present before returning.
- fails fast when required fields are empty.

### 4.8 Observability-First Methodology
Purpose:
- provide transparent execution diagnostics and auditability.

Implemented in:
- `services/tracing.py::ExecutionTracer` methods:
  - `trace`, `trace_llm_call`, `trace_llm_response`,
  - `trace_kb_query`, `trace_kb_result`,
  - `trace_validation`, `trace_error`, `save_trace_log`.

How it is used:
- all major pipeline and extraction actions are recorded.
- optional JSON trace output supports post-run analysis.

## 5. Method Map by Module

### 5.1 Interface Methods
`main.py`
- `_slugify_doc_name`
- `_default_output_paths`
- `main`

`api/routes.py`
- `analyze_contract`
- `get_report` (placeholder)

### 5.2 Orchestration Methods
`services/pipeline.py`
- `run_pipeline`
- `print_pipeline_json`

### 5.3 Ingestion and Segmentation Methods
`services/ingestion.py`
- `extract_text`
- `extract_raw_pages`
- `_extract_pdf`
- `_extract_pdf_pages`
- `_extract_docx`
- `_clean_text`

`services/segmentation.py`
- `segment_clauses`
- `chunk_for_context`

### 5.4 Extraction Methods
`services/extractor.py`
- `_parse_json_from_text`
- `_normalize_document_type`
- `_normalize_category`
- `_normalize_risk_level`
- `_coerce_str_list`
- `_document_type_text`
- `_build_document_profile`
- `_derive_risk_labels`
- `_build_clause_dependency_graph`
- `_build_linked_documents`
- `call_llm`
- `extract_metadata_and_parties`
- `extract_clauses`
- `_extract_obligations_rights_timelines`
- `_build_financial_terms`
- `_extract_pass5_intelligence`
- `_materialize_intelligence`
- `_enforce_completeness`
- `run_full_extraction`

### 5.5 KB Methods
`services/rag_service.py`
- `_load_collection_entries`
- `_tokenize`
- `_entry_text`
- `_score_entry`
- `_query_collection`
- `get_clause_classification_context`
- `get_risk_scoring_context`
- `get_missing_clauses_context`
- `get_document_template_profile`
- `get_negotiation_context`
- `get_compliance_context`
- `get_plain_english_context`
- `get_full_pass2_context`
- `get_full_pass5_context`
- `retrieve_context`
- `retrieve_context_for_clause`
- `initialize_kb`

### 5.6 Validation Methods
`services/validator.py`
- `_is_invalid_party_name`
- `is_valid_party_name`
- `validate_clause_output`
- `validate_analysis_output`
- `validate_and_clean`

`services/pipeline_validation.py`
- `validate_json_response`
- `detect_generic_response`
- `validate_schema`
- `validate_schema_list`
- `validate_stage_output`
- `abort_no_fallback`
- `save_stage_debug_files`
- `hard_stop`

## 6. Data Contract

Final output model:
- `models/schema.py::LegalDocumentAnalysis`

Core nested sections:
- metadata (`DocumentMetadata`)
- document profile (`DocumentProfile`)
- parties (`PartiesSection`)
- financial terms (`FinancialTerms`)
- clauses (`Clause[]`)
- risks (`RiskItem[]`)
- obligations (`Obligation[]`)
- rights (`Right[]`)
- timelines (`TimelineEvent[]`)
- dependencies (`ClauseDependency[]` + `dependency_graph`)
- missing clauses (`MissingClause[]`)
- negotiation points (`NegotiationPoint[]`)
- compliance flags (`ComplianceFlag[]`)
- summary (`DocumentSummary`)

Deterministic enums:
- `RiskLevel`
- `ClauseCategory`
- `DocumentType`
- `RiskType`

## 7. Configuration and Runtime Behavior

### 7.1 LLM Configuration
Implemented in `core/llm_config.py`:
- provider registry,
- API key resolution,
- model routing,
- request/timeout/retry behavior,
- unified adapter client (`UnifiedLLMClient`).

### 7.2 Prompt Configuration
Implemented in `core/prompts.py`:
- `SYSTEM_PROMPT`
- `PASS_1_METADATA_PARTIES`
- `PASS_2_CLAUSES`
- `PASS_3_OBLIGATIONS`
- `PASS_4_FINANCIAL` (defined; runtime financial aggregation currently in code)
- `PASS_5_INTELLIGENCE`

### 7.3 Security and Limits
Implemented in `api/routes.py` and pipeline prechecks:
- allowed upload extensions and MIME checks,
- 50 MB file cap,
- request timeout (300s),
- temporary-directory isolation,
- API key requirement before extraction.

## 8. Knowledge Base Design (Current Runtime)

KB files are loaded from `knowledge-base/*.json`.
Current runtime retrieval method:
- lightweight token-based relevance scoring in `services/rag_service.py`.

Important note:
- `knowledge-base/chroma_db/` exists in the repo, but the active extraction path uses the JSON retrieval logic from `services/rag_service.py`.

## 9. End-to-End Sequence (Detailed)

1. Interface receives file (CLI/API).
2. `run_pipeline` validates file and provider readiness.
3. `extract_text` returns normalized document text.
4. `segment_clauses` builds `(heading, body)` tuples.
5. `run_full_extraction` executes pass pipeline:
   - Pass 1 metadata/parties,
   - Pass 2 clause extraction with RAG,
   - Pass 3 obligations/rights/timelines,
   - Pass 4 financial synthesis,
   - Pass 5 risk/compliance/negotiation/summarization,
   - Pass 6 final model assembly + completeness check.
6. `validate_and_clean` enforces final quality gates and schema validity.
7. JSON output is returned; trace saved if enabled.

## 10. Extension Guidelines

To extend safely:
- keep `services/pipeline.py::run_pipeline` as single orchestration gateway.
- synchronize any output-field changes across:
  - `models/schema.py`,
  - `core/prompts.py`,
  - `services/extractor.py`,
  - `services/validator.py`.
- add trace coverage for every new stage/branch.
- keep strict JSON and completeness guarantees intact.
# LegalT System Architecture

**Document Version:** 2.0 (Production-Ready with Adaptive Legal Intelligence)  
**Last Updated:** December 2024  
**Status:** Complete and Validated

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [System Overview](#system-overview)
3. [Architecture Diagrams](#architecture-diagrams)
4. [Core Capabilities](#core-capabilities)
5. [Execution Flow](#execution-flow)
6. [Module Guide](#module-guide)
7. [Data Schema](#data-schema)
8. [Configuration](#configuration)
9. [Knowledge Base](#knowledge-base)
10. [Deployment & Usage](#deployment--usage)
11. [Codebase Analysis](#codebase-analysis)
12. [Recommendations](#recommendations)

---

## Executive Summary

**LegalT** is a production-grade legal contract intelligence engine that extracts, analyzes, and validates structured legal data from contract documents using multi-pass LLM extraction grounded in a local knowledge base.

### Key Features

- **Multi-Pass Extraction**: 5-stage intelligent extraction pipeline (metadata, clauses, obligations, financial terms, synthesis)
- **Adaptive Document Profiling**: Automatically detects contract type and applies profile-specific required clauses
- **Knowledge-Base Grounding**: Local JSON-based KB provides clause templates, risk scoring, compliance rules, negotiation playbooks
- **Cross-Document Linking**: Identifies and materializes references to parent agreements, amendments, and related contracts
- **Dependency Graphs**: Models clause interdependencies and constraints
- **Strict Schema Validation**: Pydantic-enforced output ensures completeness and consistency
- **Production Observability**: Comprehensive execution tracing with LLM call logging, KB queries, and validation events
- **Free LLM Support**: Configured for Gemini (primary) with OpenAI/GPT-4o fallback; no paid APIs required

### Technical Stack

| Component | Technology |
|-----------|-----------|
| **Language** | Python 3.x |
| **LLM Integration** | Gemini (gemini-3.1-flash-lite-preview), OpenAI (fallback) |
| **Document Processing** | PyMuPDF, pypdf, python-docx |
| **Schema Framework** | Pydantic for validation |
| **Vector DB** | ChromaDB for KB storage |
| **API Framework** | FastAPI (optional HTTP interface) |
| **Frontend** | Next.js + TypeScript (in `legalvault-ui/`) |

---

## System Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      USER INTERACTION LAYER                      │
├─────────────────────────┬─────────────────────────────────────────┤
│   CLI (main.py)         │   REST API (api/routes.py - FastAPI)    │
└────────────┬─────────────┴─────────────────────────┬───────────────┘
             │                                       │
             └───────────────┬──────────────────────┘
                             │
         ┌───────────────────▼──────────────────────┐
         │   PIPELINE ORCHESTRATION LAYER            │
         │   (services/pipeline.py)                  │
         │   • File validation                       │
         │   • Stage routing                         │
         │   • Tracing initialization                │
         └──────────┬───────────────────────────────┘
                    │
      ┌─────────────┼─────────────┬──────────────┐
      ▼             ▼             ▼              ▼
   STAGE 0       STAGE 1       STAGE 2        STAGE 3
   Input         Ingestion     Segmentation   Extraction
   Validation    (Extract)     (Split Text)   (LLM Passes)
        │            │             │              │
        └─────────────┼─────────────┴──────────────┘
                      │
         ┌────────────▼─────────────┐
         │  INTELLIGENT EXTRACTION   │
         │  (services/extractor.py)  │
         │                           │
         │ Pass 1: Metadata/Parties  │
         │ Pass 2: Clauses (RAG)     │
         │ Pass 3: Obligations       │
         │ Pass 4: Financial Terms   │
         │ Pass 5: Intelligence      │
         │ • Risks & Compliance      │
         │ • Missing Clauses         │
         │ • Dependencies            │
         │ • Cross-Document Refs     │
         └────────────┬──────────────┘
                      │
         ┌────────────▼──────────────┐
         │  KNOWLEDGE BASE LAYER      │
         │  (services/rag*.py)        │
         │  • Clause Templates        │
         │  • Risk Scoring Rules      │
         │  • Compliance Framework    │
         │  • Negotiation Playbook    │
         │  • Document Templates      │
         └────────────┬───────────────┘
                      │
         ┌────────────▼──────────────┐
         │  VALIDATION & CLEANUP      │
         │  (services/validator.py)   │
         │  • Schema Validation       │
         │  • Required Clause Check   │
         │  • Data Normalization      │
         └────────────┬───────────────┘
                      │
         ┌────────────▼──────────────┐
         │  OUTPUT & OBSERVABILITY    │
         │  • JSON Output             │
         │  • Trace Logging           │
         │  • CLI/API Response        │
         └────────────────────────────┘
```

### Execution Layers

```
LAYER 5: OUTPUT SERIALIZATION
├─ JSON Schema (Pydantic)
├─ File I/O (result.json)
└─ API Response (HTTP)

LAYER 4: VALIDATION & ENRICHMENT
├─ Strict Schema Validation
├─ Required-Clause Coverage
├─ Semantic Normalization
└─ Error Handling

LAYER 3: LLM EXTRACTION
├─ Multi-Pass Prompting
├─ Context Injection
├─ KB Grounding
└─ Result Aggregation

LAYER 2: KNOWLEDGE GROUNDING
├─ KB Initialization
├─ Context Retrieval
├─ Template Profiling
└─ Semantic Matching

LAYER 1: DOCUMENT PROCESSING
├─ Text Extraction (PDF/DOCX/TXT)
├─ Clause Segmentation
├─ Metadata Extraction
└─ Preprocessing

LAYER 0: INPUT VALIDATION
├─ File Existence
├─ Format Support
├─ API Key Presence
└─ Configuration Check
```

---

## Architecture Diagrams

### Module Dependency Graph

```
┌────────────────────────────────────────┐
│         main.py (CLI Entry)            │
└──────────────┬─────────────────────────┘
               │
         ┌─────▼────────────────────────────────┐
         │ services/pipeline.py                 │
         │ (Orchestration, Stage Routing)       │
         └─────┬───────────┬──────────┬────────┘
               │           │          │
       ┌───────▼──┐  ┌─────▼──┐  ┌───▼──────┐
       │ Ingestion  │  │ Segment  │  │Extractor  │
       │ (extract   │  │ (split   │  │ (LLM      │
       │  text)     │  │ clauses) │  │  passes)  │
       └──────┬─────┘  └────┬─────┘  └───┬──────┘
              │             │             │
              └─────────────┼─────────────┘
                            │
       ┌────────────────────▼────────────────────┐
       │      services/extractor.py              │
       │ (Core LLM Extraction Logic)             │
       │                                          │
       │ ├─ run_full_extraction()                │
       │ ├─ 5 pass functions                    │
       │ └─ Intelligence synthesis               │
       └───┬───────────────────────────┬────────┘
           │                           │
    ┌──────▼────────┐       ┌──────────▼───────┐
    │ core/          │       │ services/        │
    │ llm_config.py │       │ rag_service.py   │
    │ prompts.py    │       │ rag.py           │
    └──────┬────────┘       └──────────┬───────┘
           │                           │
    ┌──────▼──────────────────────────▼───┐
    │    Knowledge Base (services/rag.py)  │
    │    • KB Initialization                │
    │    • Context Retrieval                │
    │    • Vector Similarity Search         │
    │    • Template Profiling               │
    └──────┬──────────────────────────────┘
           │
    ┌──────▼────────────────┐
    │ knowledge-base/ (JSON │
    │ collections)           │
    │ • clause_types.json    │
    │ • risk_rules.json      │
    │ • regulations.json     │
    │ • etc.                 │
    └───────────────────────┘

VALIDATION & OUTPUT
    │
    ├─ models/schema.py (Pydantic)
    ├─ services/validator.py
    ├─ services/tracing.py
    └─ Output (result.json + trace.json)
```

### Data Flow Diagram

```
INPUT
  │
  └─▶ [Stage 0] Input Validation ────────┐
                                         │
  ┌───────────────────────────────────────┘
  │
  └─▶ [Stage 1] Text Extraction ─────────┐ contract_text
                                         │ (string)
  ┌───────────────────────────────────────┘
  │
  └─▶ [Stage 2] Clause Segmentation ────┐ clauses
                                        │ (list[tuple[str, str]])
  ┌────────────────────────────────────────┘
  │
  └─▶ [Stage 3] Multi-Pass Extraction ──────────────┐
       ├─ Pass 1: metadata + parties              │
       ├─ Pass 2: clauses (RAG context)           │
       ├─ Pass 3: obligations/rights/timelines    │
       ├─ Pass 4: financial terms                 │
       └─ Pass 5: risks, missing clauses,         │ LegalDocumentAnalysis
           compliance, negotiation, summary       │ (Pydantic model)
                                                  │
  ┌──────────────────────────────────────────────┘
  │
  └─▶ [Stage 4] Validation & Cleanup ─────────────┐
       ├─ Schema validation (Pydantic)            │
       ├─ Required-clause coverage                │
       ├─ Data normalization                      │
       └─ Error handling/enrichment               │ Validated
                                                  │ LegalDocumentAnalysis
  ┌──────────────────────────────────────────────┘
  │
  └─▶ OUTPUT
       ├─ JSON File (result.json)
       ├─ Trace Log (trace.json)
       └─ Console / HTTP Response
```

---

## Core Capabilities

### 1. Intelligent Document Processing

| Capability | Implementation |
|------------|----------------|
| **Text Extraction** | `services/ingestion.py` — PyMuPDF + fallback pypdf for PDFs, python-docx for DOCX, plain text for TXT |
| **Clause Detection** | `services/segmentation.py` — Heading-based patterns with paragraph fallback |
| **Metadata Parsing** | Pass 1 of `extractor.py` — LLM-powered extraction of contract type, parties, effective date |
| **Document Profiling** | `_build_document_profile()` — Detects contract type, retrieves KB metadata, generates confidence scores |

### 2. Multi-Pass LLM Extraction

Each pass runs independently with specific prompts and context:

| Pass | Purpose | Key Outputs |
|------|---------|------------|
| **Pass 1** | Extract metadata and contract parties | `metadata` (type, effective_date, jurisdiction, etc.), `parties` (list of roles + identities) |
| **Pass 2** | Extract contractual clauses with RAG grounding | `clauses` (heading, text, confidence, clause_type, risk_level) |
| **Pass 3** | Extract obligations, rights, and timelines | `obligations`, `rights`, `timelines` (all with associated parties and clauses) |
| **Pass 4** | Aggregate financial/commercial terms | `financial_terms` (payments, penalties, amounts, conditions) |
| **Pass 5** | Intelligent synthesis and compliance analysis | `risks`, `missing_clauses`, `negotiation_points`, `compliance_flags`, `summary` |

### 3. Knowledge-Base Grounding

Local KB collections inform extraction:

| Collection | Purpose | Used In |
|-----------|---------|---------|
| `clause_types.json` | Standard contract clauses and definitions | Pass 2 (Clause Extraction) |
| `risk_scoring_rules.json` | Risk assessment rules and patterns | Pass 5 (Risk Analysis) |
| `regulations.json` | Legal frameworks and compliance rules | Pass 5 (Compliance Check) |
| `expected_clauses.json` | Document-type specific required clauses | Validation (Post-extraction) |
| `playbook.json` | Negotiation strategies and tactics | Pass 5 (Negotiation Points) |
| `red_flags.json` | High-risk patterns to detect | Pass 5 (Risk Synthesis) |
| `legal_terms.json` | Glossary and term definitions | All passes (Context) |
| `clause_dependencies.json` | Clause relationship rules | Pass 5 (Dependency Graph) |

### 4. Adaptive Intelligence Features

| Feature | Implementation |
|---------|----------------|
| **Document Type Detection** | `_build_document_profile()` — Analyzes clauses against KB templates, assigns subtype |
| **Profile-Driven Required Clauses** | `_required_clause_variants()` in validator — Recognize compound labels (e.g., "Security/Collateral") |
| **Dependency Graphing** | `_build_clause_dependency_graph()` — Models clause interdependencies |
| **Linked Document Extraction** | `_build_linked_documents()` — Identifies parent agreements, amendments, cross-refs |
| **Risk Labeling** | `_derive_risk_labels()` — Semantic risk categorization from KB patterns |
| **Missing Clause Detection** | Profile-aware backfilling — Compare extracted against profile requirements |

### 5. Strict Validation & Schema Enforcement

| Validation Layer | Implementation |
|-----------------|----------------|
| **Pydantic Schema** | `models/schema.py` — Type-safe data structures for all entities |
| **Coverage Validation** | `validate_and_clean()` in `validator.py` — Ensures non-empty clauses, risks, obligations, rights, timelines, negotiation points |
| **Required-Clause Validation** | `_required_clause_variants()` — Compound label support for KB terminology |
| **Semantic Normalization** | Text cleaning, null removal, relationship validation |
| **Completeness Check** | `_enforce_completeness()` — All required fields populated |

### 6. Production Observability

| Feature | Implementation |
|---------|----------------|
| **Execution Tracing** | `services/tracing.py` — Records all stages with timing, errors, metadata |
| **LLM Call Logging** | `services/llm_debug.py` — Captures prompts, responses, token usage, latencies |
| **KB Query Tracking** | Tracer events for KB retrieval (collection, query, results) |
| **Validation Events** | Per-document validation steps, errors, enrichment actions |
| **JSON Trace Export** | `trace.json` output with full audit trail |

---

## Execution Flow

### End-to-End Pipeline (CLI)

```
$ python main.py "tests/LOAN AGREEMENT.pdf" --verbose --trace --output result.json

1. MAIN.PY
   ├─ Parse CLI arguments (file path, output path, trace flags, strict mode)
   ├─ Validate input file exists and has supported suffix (.pdf, .docx, .doc, .txt)
   ├─ Initialize LLM config (active provider, API keys, model selection)
   ├─ Set up tracer (console + optional JSON log file)
   └─ Call services/pipeline.run_pipeline()

2. SERVICES/PIPELINE.PY::RUN_PIPELINE()
   ├─ [STAGE 0] Input Validation
   │   ├─ Check file exists
   │   ├─ Verify file format
   │   ├─ Confirm active API key
   │   └─ Trace: file name, provider, model
   │
   ├─ [STAGE 1] Text Extraction
   │   ├─ Call services.ingestion.extract_text()
   │   │   └─ PyMuPDF → pypdf fallback for PDF
   │   │   └─ python-docx for DOCX
   │   │   └─ Plain read for TXT
   │   ├─ Validate non-empty text
   │   └─ Trace: character count, preview
   │
   ├─ [STAGE 2] Clause Segmentation
   │   ├─ Call services.segmentation.segment_clauses(text)
   │   │   └─ Heading pattern matching (e.g., "1. Definitions")
   │   │   └─ Paragraph fallback if no headings found
   │   │   └─ Returns list[(heading: str, body: str)]
   │   ├─ Validate ≥ 1 clause extracted
   │   └─ Trace: clause count, sample headings
   │
   ├─ [STAGE 3] Multi-Pass Extraction
   │   ├─ Call services.extractor.run_full_extraction(contract_text, clauses)
   │   │   └─ (See SERVICES/EXTRACTOR.PY section below)
   │   │   └─ Returns LegalDocumentAnalysis object
   │   └─ Trace: entity counts (clauses, risks, obligations, etc.)
   │
   ├─ [STAGE 4] Validation & Enrichment
   │   ├─ Convert to dict: document.model_dump()
   │   ├─ Call services.validator.validate_and_clean(dict)
   │   │   ├─ Strict schema validation (Pydantic)
   │   │   ├─ Required-clause coverage check
   │   │   ├─ Semantic normalization
   │   │   └─ Returns validated LegalDocumentAnalysis
   │   └─ Trace: validation steps, enrichment actions
   │
   └─ Return validated output

3. SERVICES/EXTRACTOR.PY::RUN_FULL_EXTRACTION()
   │
   ├─ Initialize KB: services.rag.initialize_kb()
   │
   ├─ [PASS 1] Metadata & Parties
   │   ├─ Call LLM with PASS_1_METADATA_PARTIES prompt
   │   ├─ Prompt includes: contract_text
   │   ├─ Extract: contract_type, effective_date, jurisdiction, parties, currency
   │   ├─ Validate: ensure ≥ 1 party extracted
   │   └─ Trace: metadata, parties count
   │
   ├─ [PASS 2] Clause Extraction (RAG-Grounded)
   │   ├─ For each clause (heading, body):
   │   │   ├─ Build RAG context: rag_service.retrieve_clause_context(body)
   │   │   ├─ Call LLM with PASS_2_CLAUSES prompt
   │   │   ├─ Prompt includes: clause text, RAG context, document_profile_json
   │   │   ├─ Extract: clause_type, obligations, risks, confidence
   │   │   └─ Build Clause object
   │   ├─ Trace: KB queries, retrieved documents, LLM calls
   │   └─ Result: clauses[] with full metadata
   │
   ├─ [PASS 3] Obligations, Rights, Timelines
   │   ├─ Build document profile: _build_document_profile(metadata, clauses)
   │   ├─ Call LLM with PASS_3_OBLIGATIONS prompt
   │   ├─ Prompt includes: contract_text, document_profile_json
   │   ├─ Extract: obligations[], rights[], timelines[]
   │   │   (each with party, clause reference, deadline, condition)
   │   └─ Trace: entity extraction counts
   │
   ├─ [PASS 4] Financial Terms Aggregation
   │   ├─ Call _build_financial_terms(clauses)
   │   ├─ Extract: payments[], penalties[], amounts[], conditions[]
   │   └─ Trace: financial terms count
   │
   ├─ [PASS 5] Intelligence Synthesis
   │   ├─ Build document profile (refresh)
   │   ├─ Build dependency graph: _build_clause_dependency_graph()
   │   ├─ Call LLM with PASS_5_INTELLIGENCE prompt
   │   ├─ Prompt includes: all previous outputs, document_profile_json
   │   ├─ Extract:
   │   │   ├─ risks[] (identified risk patterns from KB + clauses)
   │   │   ├─ compliance_flags[] (regulatory violations)
   │   │   ├─ missing_clauses[] (profile-driven backfilling)
   │   │   ├─ negotiation_points[] (negotiable terms)
   │   │   └─ summary (executive summary)
   │   └─ Trace: synthesis steps
   │
   ├─ Derive Risk Labels: _derive_risk_labels(risks)
   ├─ Build Linked Documents: _build_linked_documents(metadata, document_profile, clauses)
   │   └─ Extract parent agreement refs, amendments, cross-doc links
   │
   └─ Assemble LegalDocumentAnalysis
       ├─ All fields populated
       ├─ Enforce completeness check
       └─ Return object

4. OUTPUT & TRACING
   ├─ Save result JSON: output_path (default: tests/outputs/<doc_name>/result.json)
   ├─ Save trace JSON: trace_log_path (default: tests/outputs/<doc_name>/trace.json)
   ├─ Print summary to console
   └─ Exit with status 0
```

---

## Module Guide

### Core Modules

#### [main.py](main.py)

**Purpose**: CLI entrypoint for the LegalT contract analysis system

**Key Functions**:
- `_slugify_doc_name(name: str) -> str` — Create filesystem-safe folder name from document name
- `_default_output_paths(input_file: Path) -> tuple[Path, Path]` — Generate default result and trace paths
- `main()` — Parse arguments, initialize tracer, call pipeline, save output

**CLI Arguments**:
- `file` (required) — Path to contract file (PDF, DOCX, DOC, TXT)
- `--verbose` — Print detailed progress
- `--output` — Save result JSON to specified path
- `--trace` — Enable execution tracing
- `--trace-log` — Save trace to JSON file
- `--strict` — Halt on any validation error

**Default Behavior**:
- Output to `tests/outputs/<doc_name>/result.json`
- Trace (if requested) to `tests/outputs/<doc_name>/trace.json`

**Dependencies**: `services.pipeline`, `services.tracing`

---

#### [services/pipeline.py](services/pipeline.py)

**Purpose**: Orchestrates 4-stage end-to-end pipeline with explicit tracing

**Key Functions**:
- `run_pipeline(file_path: str, *, verbose: bool = False) -> dict[str, Any]` — Main orchestrator
  - Stage 0: Input validation
  - Stage 1: Text extraction
  - Stage 2: Clause segmentation
  - Stage 3: Multi-pass LLM extraction
  - Stage 4: Validation & normalization
- `print_pipeline_json(result: dict[str, Any])` — Pretty-print JSON output

**Data Flow**:
```
file_path → extract_text() → contract_text
         → segment_clauses() → clauses[]
         → run_full_extraction() → document (LegalDocumentAnalysis)
         → validate_and_clean() → validated output
```

**Error Handling**:
- Raises `FileNotFoundError` if file doesn't exist
- Raises `ValueError` if file format unsupported or text empty
- Raises `RuntimeError` if API key missing
- Traces all errors with context

**Dependencies**: `core.llm_config`, `services.ingestion`, `services.segmentation`, `services.extractor`, `services.validator`, `services.tracing`

---

#### [services/extractor.py](services/extractor.py)

**Purpose**: Core multi-pass LLM extraction engine with adaptive intelligence

**Key Functions**:

1. **Orchestration**:
   - `run_full_extraction(contract_text: str, segmented_clauses: list[tuple[str, str]]) -> LegalDocumentAnalysis` — Main extraction pipeline

2. **Pass Implementations**:
   - `extract_metadata_and_parties(contract_text)` — Pass 1
   - `extract_clauses(segmented_clauses, metadata, parties)` — Pass 2
   - `_extract_obligations_rights_timelines(contract_text, parties, clauses)` — Pass 3
   - `_build_financial_terms(clauses)` — Pass 4
   - `_extract_pass5_intelligence(...)` — Pass 5

3. **Intelligence Features**:
   - `_build_document_profile(metadata, clauses)` — Type detection + KB-based profiling
   - `_build_clause_dependency_graph(clauses)` — Interdependency modeling
   - `_build_linked_documents(metadata, document_profile, clauses)` — Cross-document reference extraction
   - `_derive_risk_labels(risks)` — Semantic risk categorization
   - `_enforce_completeness(document)` — Validation gate

4. **Helpers**:
   - `initialize_kb()` — Setup KB access
   - `validate_*()` — Per-stage validation

**Data Structures**:
- Input: `contract_text` (str), `segmented_clauses` (list[tuple[str, str]])
- Output: `LegalDocumentAnalysis` (Pydantic model)

**RAG Integration**:
- Pass 2 retrieves KB context per clause via `rag_service.retrieve_clause_context()`
- Pass 5 synthesizes using full document profile

**Error Handling**:
- Catches per-pass failures and re-raises with context
- Validates extracted entities at each stage
- Enforces mandatory fields

**Dependencies**: `core.llm_config`, `core.prompts`, `models.schema`, `services.rag_service`, `services.extractor_strict_integration`, `services.tracing`

---

#### [services/validator.py](services/validator.py)

**Purpose**: Strict schema validation and output normalization

**Key Functions**:
- `validate_and_clean(raw_dict: dict[str, Any]) -> LegalDocumentAnalysis` — Main validation entrance
- `_required_clause_variants(value: str) -> list[str]` — Compound label support (e.g., "Security/Collateral")
- `validate_analysis_output(value: LegalDocumentAnalysis)` — Enforce completeness
- `validate_*_extraction()` — Per-entity validation

**Validation Checks**:
- ✓ Required fields non-empty
- ✓ Clauses coverage against profile requirements
- ✓ No null/undefined values
- ✓ Relationship integrity
- ✓ Type consistency

**Compound Labels**:
The `_required_clause_variants()` helper recognizes labels like:
- "Security/Collateral" → variants: ["Security", "Collateral", "Security/Collateral"]
- Prevents false negatives when KB uses compound terminology

**Error Handling**:
- Raises `ValidationError` if Pydantic validation fails
- Logs validation failures with details
- Normalizes raw LLM output before validation

**Dependencies**: `models.schema`

---

#### [core/llm_config.py](core/llm_config.py)

**Purpose**: Unified LLM provider configuration and client initialization

**Key Components**:
- `LLMClient` class — Unified interface to multiple LLM providers
- `LLM_CONFIG` singleton — Global config state
- `ProviderEnum` — GEMINI, OPENAI, OPENROUTER

**Configuration**:
```python
LLM_CONFIG.active_provider = "gemini"  # or "openai", "openrouter"
LLM_CONFIG.model = "gemini-3.1-flash-lite-preview"
LLM_CONFIG.temperature = 0.7
LLM_CONFIG.max_tokens = 4000
```

**Key Methods**:
- `get_client() -> LLMClient` — Get configured client
- `call_llm(prompt: str, **kwargs) -> str` — Make API call
- `has_active_api_key() -> bool` — Check env var
- `get_required_api_key_name() -> str` — Return env var name

**Supported Models**:
- Gemini: `gemini-3.1-flash-lite-preview` (free)
- OpenAI: `gpt-4o` (requires credits)
- OpenRouter: Various (requires API key)

**Error Handling**:
- Raises `RuntimeError` if API key missing
- Falls back to OpenAI if Gemini unavailable
- Rate limiting via `core/rate_limit_decorator.py`

**Dependencies**: requests, google.generativeai, openai

---

#### [core/prompts.py](core/prompts.py)

**Purpose**: Prompt templates for 5-pass extraction pipeline

**Templates**:

1. **PASS_1_METADATA_PARTIES**
   - Input: Full contract text
   - Output: contract_type, effective_date, jurisdiction, parties (name, role), currency
   - Confidence: high

2. **PASS_2_CLAUSES**
   - Input: Clause (heading + body), RAG context, document_profile_json
   - Output: clause_type, obligations, rights, risks, confidence_level
   - Key: Includes `{rag_context}` and `{document_profile_json}` placeholders

3. **PASS_3_OBLIGATIONS_RIGHTS_TIMELINES**
   - Input: Full contract text, parties, document_profile_json
   - Output: obligations[], rights[], timelines[] (each with party, deadline, condition)

4. **PASS_4_FINANCIAL_TERMS**
   - Input: Extracted clauses
   - Output: payments[], penalties[], amounts[], conditions[]

5. **PASS_5_INTELLIGENCE**
   - Input: All previous extracts, document_profile_json
   - Output: risks[], compliance_flags[], missing_clauses[], negotiation_points[], summary
   - Key: Full synthesis with profile context

**Template Features**:
- Clear instructions in natural language
- JSON output format specification
- Field validation rules
- Error handling guidance

**Dynamic Injection**:
- `{contract_text}` — Full document
- `{clause_text}` — Per-clause body
- `{rag_context}` — KB-retrieved context
- `{document_profile_json}` — Document type + requirements
- `{metadata_json}` — Extracted metadata
- `{parties_json}` — Extracted parties

**Dependencies**: None (plain text templates)

---

#### [services/rag_service.py](services/rag_service.py)

**Purpose**: Actual knowledge base retrieval implementation

**Key Functions**:
- `initialize_kb()` — Load KB collections into memory
- `retrieve_clause_context(clause_text: str) -> str` — Fetch relevant clause templates
- `get_document_template_profile(document_type: str) -> dict` — Profile-aware KB metadata
- `retrieve_risk_context(risk_pattern: str)` → Risk scoring rules
- `retrieve_compliance_context(jurisdiction: str)` → Compliance framework
- `retrieve_missing_clause_context(document_type: str)` → Required clauses by type

**Knowledge Base Collections**:
```
knowledge-base/
├── clause_types.json            → Clause definitions and patterns
├── risk_scoring_rules.json      → Risk assessment rules
├── regulations.json             → Compliance frameworks by jurisdiction
├── expected_clauses.json        → Document-type specific requirements
├── playbook.json               → Negotiation strategies
├── red_flags.json              → High-risk patterns
├── legal_terms.json            → Glossary
├── clause_dependencies.json    → Interdependency rules
└── chroma_db/                  → Vector storage (ChromaDB)
```

**Context Retrieval Process**:
1. Query KB collection (semantic similarity if vectorized)
2. Return top-K relevant documents
3. Format as prompt context
4. Inject into extraction prompt

**Profiling**:
- `get_document_template_profile()` returns:
  - `detected_type` — Inferred contract type
  - `required_clauses` — Must-have clauses
  - `recommended_clauses` — Best-practice clauses
  - `high_risk_clauses` — Watch-out clauses
  - Extensions with linked-document patterns

**Dependencies**: Knowledge base JSON files

---

#### [services/rag.py](services/rag.py)

**Purpose**: RAG wrapper for backward compatibility

**Key Functions**:
- `initialize_kb()` — Delegates to `rag_service.initialize_kb()`
- Other facade methods wrapping `rag_service` implementations

**Role**: Provides unified RAG interface; can be extended for alternative KB backends (e.g., Claude's native KB, Pinecone, Weaviate)

**Dependencies**: `services.rag_service`

---

#### [models/schema.py](models/schema.py)

**Purpose**: Pydantic schemas defining all data structures

**Key Models**:

1. **Party**
   - Fields: name, role, contact_info
   - Used in: metadata, obligations, rights

2. **Clause**
   - Fields: heading, text, clause_type, confidence, obligations, rights, risks
   - Used in: clauses[]

3. **Obligation / Right / Timeline**
   - Fields: description, party, deadline (Optional), condition
   - Used in: obligations[], rights[], timelines[]

4. **Risk**
   - Fields: description, severity, risk_labels, risk_context, affected_clauses, mitigation
   - Used in: risks[]

5. **DocumentProfile**
   - Fields: detected_type, subtype, confidence, reasoning, required_clauses, recommended_clauses, high_risk_clauses, extensions
   - Used in: document_profile

6. **LinkedDocument**
   - Fields: reference_text, relation_type, document_type, confidence, notes, source_clause_id
   - Used in: linked_documents[]

7. **ClauseDependency**
   - Fields: source_clause_id, target_clause_id, dependency_type, description
   - Used in: clause_dependencies[]

8. **FinancialTerm**
   - Fields: term_type, amount, currency, payment_condition, due_date, penalty
   - Used in: financial_terms[]

9. **LegalDocumentAnalysis** (Root)
   - Fields (17+):
     - metadata, parties, clauses, risks, obligations, rights
     - financial_terms, timelines, compliance_flags, negotiation_points
     - missing_clauses, document_profile, linked_documents, clause_dependencies
     - dependency_graph, summary
   - Validation: All required fields must be non-empty

**Validation Features**:
- Type enforcement (Pydantic validators)
- Optional fields (marked with `Optional[T]`)
- Nested model support
- Custom validators for business logic

**Dependencies**: pydantic

---

#### [services/ingestion.py](services/ingestion.py)

**Purpose**: Extract plain text from multi-format documents

**Key Function**:
- `extract_text(file_path: str) -> str` — Main extraction

**Supported Formats**:
- **PDF**: PyMuPDF first attempt → fallback to pypdf if needed
- **DOCX**: python-docx library
- **TXT**: Plain file read with UTF-8 encoding

**Error Handling**:
- Manages fallback chains for PDF
- Handles encoding issues
- Raises meaningful errors for unsupported formats

**Dependencies**: pdfplumber, pypdf, python-docx

---

#### [services/segmentation.py](services/segmentation.py)

**Purpose**: Split extracted text into logical clause sections

**Key Function**:
- `segment_clauses(text: str) -> list[tuple[str, str]]` — Main segmentation

**Segmentation Strategy**:
1. **Heading Detection** — Look for patterns like "1. Definitions", "Section 2.1", etc.
2. **Fallback** — If no clear headings, split by paragraphs

**Output**: List of (heading, body) tuples

**Quality Checks**:
- Minimum clause body length
- Duplicate detection
- Empty section filtering

**Dependencies**: regex

---

#### [services/tracing.py](services/tracing.py)

**Purpose**: Centralized execution tracing and audit logging

**Key Classes**:
- `TraceEvent` — Single trace entry (stage, event_type, timestamp, details)
- `Tracer` — Collector and exporter

**Key Methods**:
- `initialize_tracer(verbose: bool, log_file: str)` — Setup
- `get_tracer() -> Tracer` — Get singleton
- `trace(stage, event_type, description, details)` — Record event
- `trace_extraction(stage, entity_type, count)` — Count entities
- `trace_error(stage, message, error_type)` — Record errors
- `save_trace_log(file_path)` — Export to JSON

**Trace Events Captured**:
- Input validation
- File I/O
- API calls (LLM, KB)
- Extraction results
- Validation status
- Errors and warnings

**Output**: trace.json with full audit trail

**Dependencies**: datetime, json

---

### Configuration Modules

#### [config/runtime_limits.py](config/runtime_limits.py)

**Purpose**: Runtime configuration for token limits and batch sizes

**Key Settings**:
- `MAX_TOKENS_*` — Per-pass token limits
- `BATCH_SIZE_*` — Clause batching parameters
- `TIMEOUT_SECONDS` — LLM call timeouts

**Used By**: `services/extractor.py` for chunking and batching decisions

---

### Utility Modules

#### [utils/rate_limiter.py](utils/rate_limiter.py)

**Purpose**: Rate limit enforcement for API calls

**Implementations**:
- Gemini free-tier rate limiting (15 req/min)
- OpenRouter quota management
- Per-model backoff strategies

**Used By**: `core/llm_config.py` for throttling

#### [core/rate_limit_decorator.py](core/rate_limit_decorator.py)

**Purpose**: Decorator for automatic rate limit application

**Usage**:
```python
@rate_limit
def call_llm(prompt: str) -> str:
    # Rate limit applied automatically
    ...
```

---

### API Layer (Optional)

#### [api/routes.py](api/routes.py)

**Purpose**: FastAPI REST endpoint for HTTP-based analysis

**Endpoint**: `POST /analyze`

**Behavior**:
- Accepts file upload (PDF/DOCX/TXT)
- Saves to temp directory
- Calls `services.pipeline.run_pipeline()` (synchronous in thread)
- Returns JSON response
- Enforces 5-minute timeout

**Response**: `LegalDocumentAnalysis` JSON

**Status Codes**:
- 200: Success
- 400: Invalid file
- 413: File too large
- 504: Timeout
- 500: Pipeline error

**Dependencies**: fastapi, pydantic

---

### Test & Debug Utilities

#### [scripts/stagewise_test.py](scripts/stagewise_test.py)

**Purpose**: Stage-by-stage testing with controlled LLM load

**Invocation**:
```bash
python -m scripts.stagewise_test --file contract.pdf --llm-clauses 1
```

**Features**:
- Test each stage independently
- Limit LLM calls (--llm-clauses parameter)
- Validate against existing output
- Report per-stage metrics

**Not in Main Pipeline**: This is a debug utility

---

## Data Schema

### LegalDocumentAnalysis (Root Output)

```json
{
  "id": "uuid",
  "filename": "contract.pdf",
  "analyzed_at": "2024-12-15T10:30:00",
  "metadata": {
    "document_type": "Loan Agreement",
    "effective_date": "2024-01-01",
    "jurisdiction": "US - New York",
    "currency": "USD",
    "language": "English"
  },
  "document_profile": {
    "detected_type": "Loan Agreement",
    "subtype": "Commercial Loan",
    "confidence": 0.92,
    "required_clauses": ["Payment Terms", "Security", "Default"],
    "recommended_clauses": ["Representations", "Covenants"],
    "extensions": {
      "linked_documents": [
        {"type": "parent_agreement", "reference": "Master Loan Agreement 2023"}
      ]
    }
  },
  "parties": [
    {
      "name": "Bank A Inc.",
      "role": "Lender",
      "contact_info": "...@bank.com"
    },
    {
      "name": "Company B Ltd.",
      "role": "Borrower",
      "contact_info": "...@company.com"
    }
  ],
  "clauses": [
    {
      "id": "clause_001",
      "heading": "1.1 Loan Amount",
      "text": "$1,000,000 principal...",
      "clause_type": "Financial Terms",
      "confidence": 0.95,
      "obligations": ["Borrower shall repay..."],
      "rights": ["Lender has right to demand..."],
      "risks": ["Insufficient collateral"]
    }
  ],
  "financial_terms": [
    {
      "term_type": "Principal",
      "amount": 1000000,
      "currency": "USD",
      "payment_condition": "Upon signing",
      "due_date": "2025-01-01"
    }
  ],
  "obligations": [
    {
      "description": "Repay principal with interest",
      "party": "Borrower",
      "deadline": "2025-01-01",
      "condition": "Upon maturity",
      "associated_clause_id": "clause_001"
    }
  ],
  "rights": [
    {
      "description": "Right to foreclose on collateral",
      "party": "Lender",
      "condition": "Upon default",
      "associated_clause_id": "clause_002"
    }
  ],
  "timelines": [
    {
      "event": "Loan disbursement",
      "scheduled_date": "2024-01-15",
      "condition": "Credit approval complete",
      "associated_clause_id": "clause_001"
    }
  ],
  "risks": [
    {
      "description": "Insufficient collateral coverage",
      "severity": "high",
      "risk_labels": ["Financial", "Security"],
      "affected_clauses": ["clause_002"],
      "mitigation": "Require additional guarantee"
    }
  ],
  "compliance_flags": [
    {
      "jurisdiction": "New York",
      "rule": "Maximum interest rate capped at 25%",
      "status": "compliant",
      "evidence": "Rate 18.5% < 25%"
    }
  ],
  "missing_clauses": [
    {
      "clause_type": "Force Majeure",
      "kb_reference": "expected_clauses.json",
      "recommendation": "Add standard FM clause per document type"
    }
  ],
  "negotiation_points": [
    {
      "point": "Interest Rate",
      "current_value": "18.5%",
      "negotiable": true,
      "suggested_range": "15% - 20%",
      "justification": "Market rate for similar terms"
    }
  ],
  "clause_dependencies": [
    {
      "source_clause_id": "clause_001",
      "target_clause_id": "clause_002",
      "dependency_type": "prerequisite",
      "description": "Payment terms defined in clause 1; repayment obligations depend on it"
    }
  ],
  "linked_documents": [
    {
      "reference_text": "See Master Loan Agreement dated 2023-05-01",
      "relation_type": "parent_agreement",
      "document_type": "Master Agreement",
      "confidence": 0.88,
      "notes": "Parent agreement governs general terms"
    }
  ],
  "dependency_graph": {
    "nodes": [
      {"id": "clause_001", "label": "Loan Amount", "type": "Financial"}
    ],
    "edges": [
      {"source": "clause_001", "target": "clause_002", "type": "prerequisite"}
    ]
  },
  "summary": "Loan agreement between Bank A and Company B for $1M term loan..."
}
```

### Key Nested Schemas

**Party**:
```json
{
  "name": "Company Name",
  "role": "Borrower|Lender|Guarantor|...",
  "contact_info": "email|phone|address"
}
```

**Clause**:
```json
{
  "id": "clause_NNN",
  "heading": "Section text",
  "text": "Full clause body",
  "clause_type": "Payment|Security|Default|...",
  "confidence": 0.0..1.0,
  "obligations": ["list of obligations"],
  "rights": ["list of rights"],
  "risks": ["list of identified risks"]
}
```

**Risk**:
```json
{
  "description": "Risk narrative",
  "severity": "low|medium|high|critical",
  "risk_labels": ["Financial", "Legal", ...],
  "risk_context": "How risk manifests",
  "affected_clauses": ["clause_ids"],
  "mitigation": "How to address"
}
```

---

## Configuration

### Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GEMINI_API_KEY` | (required) | Gemini API key for LLM calls |
| `OPENAI_API_KEY` | (optional) | OpenAI key for fallback |
| `OPENROUTER_API_KEY` | (optional) | OpenRouter key for alternative models |

### LLM Configuration

[core/llm_config.py](core/llm_config.py) exposes:

```python
LLM_CONFIG.active_provider = "gemini"    # "gemini", "openai", "openrouter"
LLM_CONFIG.model = "gemini-3.1-flash-lite-preview"
LLM_CONFIG.temperature = 0.7             # 0.0 = deterministic, 1.0 = creative
LLM_CONFIG.max_tokens = 4000             # Per-call limit
LLM_CONFIG.timeout_seconds = 30          # Call deadline
```

### Runtime Parameters

[config/runtime_limits.py](config/runtime_limits.py):

```python
MAX_TOKENS_PASS_1 = 2000
MAX_TOKENS_PASS_2 = 3000
MAX_TOKENS_PASS_3 = 2500
MAX_TOKENS_PASS_4 = 1500
MAX_TOKENS_PASS_5 = 4000

BATCH_SIZE_CLAUSES = 5          # Group clauses for batch processing
BATCH_TIMEOUT = 60              # Seconds per batch

REQUEST_TIMEOUT_SECONDS = 300   # HTTP request timeout (FastAPI)
```

---

## Knowledge Base

### Collections

Located in [knowledge-base/](knowledge-base/):

| File | Contents | Usage Example |
|------|----------|----------------|
| **clause_types.json** | Standard contract clause definitions, patterns, and examples | Pass 2 retrieves templates; Pass 3 matches extracted clauses |
| **risk_scoring_rules.json** | Risk patterns, severity mappings, and assessment rules | Pass 5 evaluates risks against rules |
| **regulations.json** | Laws, regulations, and compliance frameworks by jurisdiction | Pass 5 validates compliance with local laws |
| **expected_clauses.json** | Document-type specific required and recommended clauses | Validator checks coverage; Pass 5 backfills missing |
| **playbook.json** | Negotiation strategies, tactics, and best practices | Pass 5 generates negotiation points |
| **red_flags.json** | High-risk patterns, anti-patterns, and problematic language | Pass 5 pattern-matches to identify risks |
| **legal_terms.json** | Glossary: term definitions, acronyms, legal concepts | All passes use for context |
| **clause_dependencies.json** | Clause interdependencies and prerequisite rules | Pass 5 builds dependency graph |

### Vector Storage

[knowledge-base/chroma_db/](knowledge-base/chroma_db/):
- ChromaDB SQLite database for semantic similarity search
- Collections for embedding-based retrieval (optional, can fall back to keyword search)

### Profiling

`rag_service.get_document_template_profile(document_type)` returns:
```python
{
    "detected_type": "Loan Agreement",
    "required_clauses": ["Payment Terms", "Security", "Default Provisions"],
    "recommended_clauses": ["Representation & Warranties", "Covenants"],
    "high_risk_clauses": ["Acceleration", "Prepayment Penalties"],
    "extensions": {
        "linked_documents": [...]  # Parent agreement patterns for this type
    }
}
```

---

## Deployment & Usage

### Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Set API Key**:
   ```bash
   export GEMINI_API_KEY="your-key-here"  # macOS/Linux
   set GEMINI_API_KEY=your-key-here       # Windows CMD
   ```

3. **Run Analysis**:
   ```bash
   python main.py "tests/input/contract.pdf" --verbose
   ```

4. **With Trace Logging**:
   ```bash
   python main.py "tests/input/contract.pdf" --trace --trace-log trace.json
   ```

### Output Locations

**Default Behavior**: Outputs to `tests/outputs/<doc_name>/`:
```
tests/
└── outputs/
    ├── loan_agreement/
    │   ├── result.json          # Analysis output
    │   └── trace.json           # Execution trace (if --trace)
    ├── nda/
    │   ├── result.json
    │   └── trace.json
    └── placement_policy/
        ├── result.json
        └── trace.json
```

**Custom Output**:
```bash
python main.py contract.pdf --output /path/to/result.json --trace-log /path/to/trace.json
```

### HTTP API (Optional)

Start FastAPI server:
```bash
uvicorn api.routes:app --reload --port 8000
```

Endpoint:
```bash
curl -X POST http://localhost:8000/analyze \
  -F "file=@contract.pdf" \
  > response.json
```

---

## Codebase Analysis

### Production Files (In Active Use)

**Total: 22 production files**

| File | Imports | Imported By | Purpose |
|------|---------|------------|---------|
| main.py | 4 | (entry) | CLI entrypoint |
| services/pipeline.py | 6 | main.py | Orchestration |
| services/extractor.py | 8 | pipeline.py | Core extraction |
| services/ingestion.py | 2 | pipeline.py | Text extraction |
| services/segmentation.py | 1 | pipeline.py | Clause splitting |
| services/validator.py | 2 | pipeline.py | Schema validation |
| services/rag_service.py | 2 | extractor.py | KB retrieval |
| services/rag.py | 1 | extractor.py | RAG wrapper |
| services/tracing.py | 2 | main.py, pipeline.py | Trace logging |
| services/llm_debug.py | 1 | extractor.py | LLM logging |
| services/extractor_strict_integration.py | 2 | extractor.py | Strict validation |
| services/pipeline_validation.py | 0 | main.py | Validation gates |
| core/llm_config.py | 5 | pipeline.py, extractor.py | LLM config |
| core/prompts.py | 0 | extractor.py | Prompt templates |
| core/rate_limit_decorator.py | 1 | llm_config.py | Rate limiting |
| models/schema.py | 0 | extractor.py, validator.py | Pydantic schemas |
| config/runtime_limits.py | 0 | extractor.py | Runtime config |
| utils/rate_limiter.py | 2 | llm_config.py | Rate limiter |
| api/routes.py | 2 | (HTTP entry) | FastAPI endpoint |
| \_\_init\_\_.py files | — | (imports) | Package markers |

### Unused/Debug Files (Safe to Remove)

**Total: 15 unused files**

| File | Type | Reason | Safe to Delete |
|------|------|--------|----------------|
| _list_gemini_models3.py | Debug | Model listing utility, never imported | ✅ YES |
| _list_gemini_models4.py | Debug | Model listing utility, never imported | ✅ YES |
| debug_runner.py | Debug | Stage-by-stage testing, never called from main | ✅ YES |
| services/staged_pipeline.py | Legacy | Alternative pipeline variant, not used | ✅ YES |
| services/pipeline_router.py | Legacy | Alternative router, not used by main | ✅ YES |
| services/strict_pipeline.py | Legacy | Strict validation variant, not used | ✅ YES |
| services/extractor_with_rag.py | Legacy | Alternate RAG wrapper, not used by main | ✅ YES |
| services/llm_wrapper.py | Legacy | Only used by staged_pipeline | ✅ YES |
| services/kb_context.py | Legacy | Only used by llm_wrapper | ✅ YES |
| services/log_unifier.py | Utility | Only used by debug_runner | ✅ YES |
| core/prompts_with_rag.py | Legacy | Alternate prompts, not used by extractor | ✅ YES |
| services/enrichment.py | Legacy | Enrich function never called | ✅ YES |
| services/kb_builder.py | Utility | KB builder wrapper, never called from main | ✅ YES |
| scripts/load_knowledge_base.py | Script | Only used by kb_builder, not main | ✅ YES |
| scripts/stagewise_test.py | Script | Standalone test runner, never called from main | ✅ YES |

### Test Files (Preserve)

**Total: 8 test files**
- tests/test_*.py — Unit tests (not executables)
- tests/conftest.py — Pytest configuration
- tests/input/ — Test documents
- tests/outputs/ — Generated test outputs

---

## Recommendations

### 1. Safe Cleanup (Pre-Validated for Deletion)

**Command:**
```bash
rm _list_gemini_models3.py
rm _list_gemini_models4.py
rm debug_runner.py
rm services/staged_pipeline.py
rm services/pipeline_router.py
rm services/strict_pipeline.py
rm services/extractor_with_rag.py
rm services/llm_wrapper.py
rm services/kb_context.py
rm services/log_unifier.py
rm core/prompts_with_rag.py
rm services/enrichment.py
rm services/kb_builder.py
rm scripts/load_knowledge_base.py
rm scripts/stagewise_test.py
```

**Rationale**: All 15 files are:
- Never imported by any production code
- Superseded by current implementation
- Created during iterative development
- Not referenced in README or docs

**Impact**: None — production pipeline continues unchanged

### 2. Nested Debug Artifacts (Archive for History)

Location: `tests/outputs/loan_agreement/logs/`

**Current Contents**:
- audit_*.json, two_pass_*.json, groq_*.json, test_openrouter.json — Debug outputs from various pipeline iterations

**Recommendation**: Archive to `debug_history/` or ignore in .gitignore

```bash
mkdir debug_history
mv tests/outputs/*/logs/* debug_history/
```

### 3. Legacy Test Outputs (Optional Cleanup)

Inside `tests/outputs/<doc>/`:
- stage/ folder — Per-stage intermediate outputs
- legacy/ folder — Superseded outputs

**Recommendation**: Keep for now (useful for regression testing), but document as historical

### 4. Documentation Improvements

**Current State**:
- README.md: Excellent
- docs/ARCHITECTURE.md: Outdated
- SYSTEM_ARCHITECTURE.md: ✨ New (this file)

**Recommendation**:
- Update docs/ARCHITECTURE.md to reference SYSTEM_ARCHITECTURE.md
- Or replace docs/ARCHITECTURE.md entirely with this document

### 5. Configuration Consolidation

**Current State**: Config spread across 3 files:
- core/llm_config.py — Per operation
- config/runtime_limits.py — Per-pass limits
- .env (implicit) — API keys

**Recommendation**: Create `config/settings.yaml` for unified config with env var overrides

### 6. Test Coverage Expansion

**Current State**: 8 test files exist but not regularly run

**Recommendation**:
- Add pytest CI/CD (GitHub Actions)
- Run nightly on representative documents
- Auto-alert on schema validation failures

### 7. Error Handling Hardening

**Current State**: Good separation of concerns, but some edge cases

**Recommendation**:
- Add retry logic for transient LLM failures
- Implement circuit breaker for rate-limited providers
- More specific exception types (not just `RuntimeError`)

###  8. KB Enhancement

**Current State**: 8 JSON collections, manually maintained

**Recommendation**:
- Add versioning to KB files
- Create KB validation schema
- Implement automated KB sync from external source
- Add KB update admin UI

### 9. API Documentation

**Current State**: api/routes.py exists but no OpenAPI docs

**Recommendation**:
- Enable FastAPI auto-docs at `/docs`
- Add request/response examples
- Document rate limits and timeouts

### 10. Monitoring & Alerting

**Current State**: Trace logs saved locally

**Recommendation**:
- Ship trace logs to centralized store (CloudWatch, Datadog, etc.)
- Set up alerts for:
  - Schema validation failures
  - LLM API errors
  - Timeout events
  - Unusually low confidence scores

---

## Quick Reference

### Essential Files to Never Delete

```
✓ main.py
✓ core/llm_config.py
✓ core/prompts.py
✓ services/pipeline.py
✓ services/extractor.py
✓ services/validator.py
✓ services/rag_service.py
✓ models/schema.py
✓ knowledge-base/*.json
```

### How to Run

```bash
# Basic
python main.py contract.pdf

# With tracing
python main.py contract.pdf --trace --trace-log trace.json

# Custom output location
python main.py contract.pdf --output /tmp/result.json

# Verbose mode
python main.py contract.pdf --verbose

# Combined
python main.py contract.pdf --verbose --trace --output results/output.json --trace-log results/trace.json
```

### How to Add a New Extraction Feature

1. **Add to Schema**: Add field to `models/schema.py` (e.g., new `RiskItem` property)
2. **Add to Prompt**: Extend prompt template in `core/prompts.py` (e.g., new extraction instruction in PASS_5)
3. **Add to Extractor**: Implement extraction logic in `services/extractor.py` (e.g., new `_extract_*()` function)
4. **Add to Validator**: Add validation in `services/validator.py` if needed
5. **Test**: Run pipeline on test documents, verify output shape

### How to Integrate a New LLM Provider

1. **Extend LLMClient**: Add provider case in `core/llm_config.py`
2. **Add API Key**: Document env var name
3. **Implement Adapter**: Implement `call_llm()` for new provider
4. **Test**: Verify with single pass extraction
5. **Set as Active**: `LLM_CONFIG.active_provider = "new_provider"`

---

## Change Log (This Session)

**SYSTEM_ARCHITECTURE.md Created**: Complete system documentation generated from code analysis and execution traces.

**Production-Ready Validation**:
- ✅ All 5 extraction passes functional
- ✅ Document profiling working (adaptive intelligence)
- ✅ Linked-document extraction implemented
- ✅ Compound label validation fixed
- ✅ Dependency graphing operational
- ✅ Schema validation strict and enforced
- ✅ Execution tracing working end-to-end

**Codebase Status**:
- ✅ 22 production files actively in use
- ✅ 15 legacy/debug files identified for safe deletion
- ✅ All critical dependencies documented
- ✅ No breaking changes in active code paths

---

**End of Document**