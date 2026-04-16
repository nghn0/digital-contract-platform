# LegalT

LegalT is a legal contract intelligence pipeline that extracts structured data from contract documents, grounds the analysis in a local knowledge base, and returns validated JSON for downstream use. The current codebase runs as a CLI pipeline, with a Next.js frontend available under `legalvault-ui/` and a knowledge base stored in ChromaDB under `knowledge-base/`.

This README is written for collaborators who need to understand the repository quickly: how the project is laid out, what each file does, how the pipeline flows end to end, how to run it, and where to change behavior safely.

## What The System Does

The main pipeline takes a contract file (`.pdf`, `.docx`, `.doc`, or `.txt`) and processes it in stages:

1. Extract text from the document.
2. Split the text into clause-like segments.
3. Run multi-pass LLM extraction with prompt templates.
4. Retrieve relevant context from the knowledge base during extraction.
5. Enrich and validate the output into a stable JSON schema.
6. Optionally trace every stage, including LLM inputs, LLM outputs, and KB retrieval results.

## Repository Layout

```text
LegalT/
├── main.py
├── core/
│   ├── llm_config.py
│   ├── prompts.py
│   ├── prompts_with_rag.py
│   └── __init__.py
├── services/
│   ├── ingestion.py
│   ├── segmentation.py
│   ├── extractor.py
│   ├── enrichment.py
│   ├── validator.py
│   ├── pipeline.py
│   ├── rag_service.py
│   ├── rag.py
│   ├── tracing.py
│   ├── kb_builder.py
│   ├── extractor_with_rag.py
│   └── __init__.py
├── models/
│   ├── schema.py
│   └── __init__.py
├── scripts/
│   └── load_knowledge_base.py
├── knowledge-base/
│   ├── *.json
│   └── chroma_db/
├── docs/
│   ├── ARCHITECTURE.md
│   └── synopsis_output.json
├── legalvault-ui/
│   ├── app/
│   ├── components/
│   └── public/
├── tests/
└── sample_contract.txt
```

## File And Folder Guide

### Entry point and orchestration

- [main.py](main.py) is the CLI entry point. It validates the file path, sets up tracing, calls the pipeline, and prints or saves the final JSON.
- [services/pipeline.py](services/pipeline.py) orchestrates the full flow. It is the best place to read first if you want the actual processing order.
- [services/tracing.py](services/tracing.py) centralizes console tracing and JSON trace export. It records LLM prompts/responses, KB queries/results, extraction counts, validation events, and errors.

### Ingestion and preprocessing

- [services/ingestion.py](services/ingestion.py) extracts plain text from PDF, DOCX, and TXT files. It uses `pdfplumber` first and falls back to `pypdf` for PDFs when needed.
- [services/segmentation.py](services/segmentation.py) splits long text into clause-like blocks using heading patterns and a fallback paragraph split.

### LLM extraction

- [services/extractor.py](services/extractor.py) performs the multi-pass extraction. It calls the LLM, normalizes document metadata, parses parties, classifies clauses, and constructs the structured analysis object.
- [core/prompts.py](core/prompts.py) stores the actual prompts used by the extractor.
- [core/prompts_with_rag.py](core/prompts_with_rag.py) contains prompt variants that include retrieved knowledge-base context.
- [core/llm_config.py](core/llm_config.py) defines the active provider, model, and runtime LLM settings.

### Knowledge base and RAG

- [services/rag_service.py](services/rag_service.py) queries ChromaDB collections and returns context used by the extractor.
- [services/rag.py](services/rag.py) is a compatibility wrapper around the RAG service.
- [scripts/load_knowledge_base.py](scripts/load_knowledge_base.py) loads the JSON knowledge-base files into ChromaDB.
- [knowledge-base/](knowledge-base/) stores the source JSON files and the generated persistent ChromaDB database.

### Enrichment and validation

- [services/enrichment.py](services/enrichment.py) fills in missing structured sections and derives useful dashboard fields when the LLM returns partial data.
- [services/validator.py](services/validator.py) validates the final output against the Pydantic schema in [models/schema.py](models/schema.py).

### Frontend and API placeholders

- [legalvault-ui/](legalvault-ui/) is the Next.js frontend for the project.
- [api/](api/) currently holds API scaffolding and route code.

## Pipeline Flow

The execution flow in the current codebase is:

```text
main.py
  -> services.pipeline.run_pipeline()
    -> services.ingestion.extract_text()
    -> services.segmentation.segment_clauses()
    -> services.extractor.run_full_extraction()
        -> Pass 1: metadata + parties
        -> Pass 2: clause extraction with RAG context
        -> Pass 3: risk extraction
        -> Pass 4: obligations / rights / deadlines
        -> Pass 5: summary / missing clauses / recommendation pass
    -> services.enrichment.enrich_dashboard_data()
    -> services.validator.validate_and_clean()
    -> final JSON output
```

### What happens in each stage

- Stage 0 validates input, provider configuration, and the active API key.
- Stage 1 extracts raw text from the uploaded file.
- Stage 2 splits the document into clause sections.
- Stage 3 runs the multi-pass LLM extraction pipeline.
- Stage 4 enriches the draft output and validates it against the schema.

When tracing is enabled, you also get visibility into:

- the exact prompt sent to the LLM,
- the parsed LLM response,
- the knowledge-base collection queried,
- the retrieved KB documents,
- and the intermediate validation/enrichment steps.

## Supported Inputs

- `.pdf`
- `.docx`
- `.doc`
- `.txt`

If the input is a scanned PDF with no text layer, extraction may fail unless OCR has been run beforehand.

## Setup

### 1. Create and activate the virtual environment

The repo is set up to use a local `.venv/`. On Windows PowerShell:

```powershell
& .\.venv\Scripts\Activate.ps1
```

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

If you plan to rebuild the knowledge base, install the KB-specific extras too:

```bash
pip install -r requirements.kb_builder.txt
```

### 3. Configure environment variables

Create or edit [.env](.env) and set the provider key you want to use. The config currently supports:

- `OPENROUTER_API_KEY`
- `ANTHROPIC_API_KEY`
- `OPENAI_API_KEY`
- `GEMINI_API_KEY`
- `GROK_API_KEY`

Only one provider needs to be active at a time, but you can keep several keys in the file for convenience.

Example:

```env
OPENROUTER_API_KEY=your_openrouter_key_here
GROK_API_KEY=your_grok_key_here
```

### 4. Download optional NLP assets

Some workflows may use spaCy models or other NLP packages. If you see a model error, install the requested model listed in the error message or in `requirements.txt` comments.

## Running The Pipeline

Run a contract through the pipeline with:

```bash
python main.py "tests/LOAN AGREEMENT.pdf" --verbose
```

For detailed trace logging:

```bash
python main.py "tests/LOAN AGREEMENT.pdf" --verbose --trace --trace-log trace.json
```

To save the final output to a file:

```bash
python main.py "tests/LOAN AGREEMENT.pdf" --output result.json
```

### CLI flags

- `--verbose` prints more stage-by-stage progress information.
- `--trace` enables detailed execution tracing in the console.
- `--trace-log` writes the full trace to a JSON file.
- `--output` saves the final analyzed JSON instead of printing it.

## Knowledge Base

The knowledge base is stored locally in `knowledge-base/` and backed by ChromaDB in `knowledge-base/chroma_db/`.

Source JSON files include:

- [baseline_clauses.json](knowledge-base/baseline_clauses.json)
- [clause_types.json](knowledge-base/clause_types.json)
- [expected_clauses.json](knowledge-base/expected_clauses.json)
- [legal_terms.json](knowledge-base/legal_terms.json)
- [playbook.json](knowledge-base/playbook.json)
- [red_flags.json](knowledge-base/red_flags.json)
- [regulations.json](knowledge-base/regulations.json)
- [risk_scoring_rules.json](knowledge-base/risk_scoring_rules.json)

To reload the KB after editing those files:

```bash
python -m scripts.load_knowledge_base
```

To force a clean rebuild of the ChromaDB collections:

```bash
python -m scripts.load_knowledge_base --reset
```

## Output Shape

The final result is a structured JSON object built from the Pydantic models in [models/schema.py](models/schema.py). It typically includes:

- document metadata,
- parties and signatories,
- clause-level analysis,
- financial terms,
- risks,
- missing clauses,
- negotiation points,
- compliance flags,
- and a summary section.

The validator and enrichment steps are there so the output stays consistent even when the model returns partial or uneven data.

## Provider Configuration

The active provider and default model are configured in [core/llm_config.py](core/llm_config.py).

The code currently supports OpenRouter, Anthropic, OpenAI, Gemini, and Grok.

Important notes:

- Grok uses the OpenAI-compatible chat API path at `https://api.x.ai/v1`.
- The default Grok model is set in `core/llm_config.py` and can be changed there without touching the rest of the code.
- If you switch providers, make sure the corresponding API key is present in `.env`.

## Tracing And Debugging

Tracing is the fastest way to verify the pipeline is working.

When enabled, you can inspect:

- input file validation,
- extracted text length and preview,
- segmentation output,
- every LLM prompt and response,
- KB lookups and returned documents,
- validation results,
- and error details when parsing fails.

Example:

```bash
python main.py "tests/LOAN AGREEMENT.pdf" --verbose --trace --trace-log trace.json
```

That produces both console output and a machine-readable trace file.

## Frontend

The `legalvault-ui/` folder contains the Next.js frontend. The most relevant files are:

- `legalvault-ui/app/page.tsx` for the main page,
- `legalvault-ui/app/layout.tsx` for app shell setup,
- `legalvault-ui/app/globals.css` for global styling,
- `legalvault-ui/components/` for UI building blocks.

This frontend is separate from the CLI pipeline, but it can consume the output JSON produced by `main.py` or by future API endpoints.

## Tips For Collaborators

- Start with [services/pipeline.py](services/pipeline.py) if you want to understand runtime behavior.
- Start with [core/llm_config.py](core/llm_config.py) if you want to change model/provider behavior.
- Start with [models/schema.py](models/schema.py) if you want to add or change output fields.
- Start with [services/rag_service.py](services/rag_service.py) if you want to adjust KB retrieval.
- Start with [services/tracing.py](services/tracing.py) if you want to change logging or trace output.

## Notes On Generated Files

The repository ignores local runtime artifacts such as:

- `venv/`
- `.env`
- trace logs
- cache directories
- `knowledge-base/chroma_db/`

That keeps commits focused on source changes rather than local machine state.

## Related Docs

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for a more compact architecture overview.
- [sample_contract.txt](sample_contract.txt) for a simple local test input.

