"""RAG service with domain-aware routing, cache, and Chroma/JSON retrieval modes."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Optional

from config.kb_routing import KB_DOMAIN_ROUTING
from services.tracing import get_tracer

try:
    import chromadb
except ImportError:  # pragma: no cover - optional dependency
    chromadb = None

KB_DIR = Path(__file__).resolve().parent.parent / "knowledge-base"

COLLECTIONS = {
    "clause_types": "kb_clause_types",
    "clause_types_financial": "kb_clause_types_financial",
    "clause_types_employment": "kb_clause_types_employment",
    "clause_types_real_estate": "kb_clause_types_real_estate",
    "risk_rules": "kb_risk_rules",
    "risk_rules_financial": "kb_risk_rules_financial",
    "doc_templates": "kb_document_templates",
    "glossary": "kb_legal_glossary",
    "standard": "kb_standard_clauses",
    "red_flags": "kb_red_flags",
    "negotiation": "kb_negotiation",
    "compliance": "kb_compliance",
}

COLLECTION_TO_FILE = {
    "kb_standard_clauses": "baseline_clauses.json",
    "kb_clause_types": "clause_types.json",
    "kb_clause_types_financial": "clause_types_financial.json",
    "kb_clause_types_employment": "clause_types_employment.json",
    "kb_clause_types_real_estate": "clause_types_real_estate.json",
    "kb_document_templates": "expected_clauses.json",
    "kb_legal_glossary": "legal_terms.json",
    "kb_negotiation": "playbook.json",
    "kb_red_flags": "red_flags.json",
    "kb_compliance": "regulations.json",
    "kb_risk_rules": "risk_scoring_rules.json",
    "kb_risk_rules_financial": "risk_rules_financial.json",
}

# Per-process query cache keyed by (collections, query-prefix-hash)
_kb_cache: dict[tuple[Any, ...], list[dict[str, str]]] = {}
_entry_cache: dict[str, list[dict[str, object]]] = {}
_chroma_client = None


def clear_kb_cache() -> None:
    """Clear per-document retrieval cache to avoid stale context carry-over."""
    _kb_cache.clear()


def _check_chroma_state() -> dict[str, int]:
    """Return collection_name -> document_count for Chroma collections."""
    if chromadb is None:
        return {}
    try:
        client = chromadb.PersistentClient(path=str(KB_DIR / "chroma_db"))
        return {collection.name: collection.count() for collection in client.list_collections()}
    except (RuntimeError, OSError, ValueError):
        return {}


_chroma_collection_counts: dict[str, int] = _check_chroma_state()


def _get_chroma_client():
    """Return cached Chroma client instance when available."""
    global _chroma_client
    if chromadb is None:
        return None
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=str(KB_DIR / "chroma_db"))
    return _chroma_client


def _normalize_document_type(document_type: str | None) -> str:
    lowered = (document_type or "").strip().lower()
    if not lowered:
        return "default"
    if "loan" in lowered or "credit" in lowered or "finance" in lowered:
        return "Loan"
    if "nda" in lowered or "confidential" in lowered:
        return "NDA"
    if "employment" in lowered:
        return "Employment"
    if "service" in lowered or "sow" in lowered or "consult" in lowered:
        return "Service Agreement"
    if "lease" in lowered or "real estate" in lowered:
        return "Lease"
    if "amend" in lowered or "addendum" in lowered or "supplement" in lowered:
        return "Amendment"
    return "default"


def _collections_for_document(document_type: str | None) -> list[str]:
    route_key = _normalize_document_type(document_type)
    return KB_DOMAIN_ROUTING.get(route_key, KB_DOMAIN_ROUTING["default"])


def _load_collection_entries(collection_name: str) -> list[dict[str, object]]:
    if collection_name in _entry_cache:
        return _entry_cache[collection_name]

    filename = COLLECTION_TO_FILE.get(collection_name)
    if not filename:
        _entry_cache[collection_name] = []
        return []

    file_path = KB_DIR / filename
    try:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        entries = payload.get("entries", []) if isinstance(payload, dict) else []
    except (OSError, json.JSONDecodeError):
        entries = []

    _entry_cache[collection_name] = entries
    return entries


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[A-Za-z0-9']+", (text or "").lower()))


def _entry_text(entry: dict[str, object]) -> str:
    text = str(entry.get("text", ""))
    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    metadata_bits: list[str] = []
    for key in ("clause_type", "risk_type", "category", "typical_risk", "description"):
        value = metadata.get(key)
        if value:
            metadata_bits.append(f"{key}: {value}")

    return text if not metadata_bits else f"{text}\n[Metadata] {'; '.join(metadata_bits)}"


def _score_entry(query_tokens: set[str], entry: dict[str, object]) -> float:
    text = str(entry.get("text", ""))
    metadata = entry.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    score = len(query_tokens & _tokenize(text))

    metadata_tokens: set[str] = set()
    for value in metadata.values():
        if isinstance(value, str):
            metadata_tokens |= _tokenize(value)
        elif isinstance(value, list):
            for item in value:
                metadata_tokens |= _tokenize(str(item))
        elif value is not None:
            metadata_tokens |= _tokenize(str(value))

    score += 2 * len(query_tokens & metadata_tokens)

    lowered_text = text.lower()
    for token in query_tokens:
        if token in lowered_text:
            score += 0.5

    return score


def _query_json_fallback(collection_name: str, query_text: str, n_results: int = 3) -> list[str]:
    """Query JSON KB by lightweight token scoring."""
    entries = _load_collection_entries(collection_name)
    query_tokens = _tokenize(query_text)
    scored_entries = [(entry, _score_entry(query_tokens, entry)) for entry in entries]
    scored_entries.sort(key=lambda item: item[1], reverse=True)
    return [_entry_text(entry) for entry, score in scored_entries[:n_results] if score > 0]


def _query_chroma(collection_name: str, query_text: str, n_results: int = 3) -> list[str]:
    """Query ChromaDB collection when populated."""
    client = _get_chroma_client()
    if client is None:
        return []

    try:
        collection = client.get_collection(name=collection_name)
        result = collection.query(query_texts=[query_text], n_results=n_results)
    except (RuntimeError, ValueError):
        return []

    documents = result.get("documents") or []
    if not documents:
        return []

    doc_row = documents[0] if isinstance(documents[0], list) else documents
    return [str(item) for item in doc_row if str(item).strip()]


def _resolve_collection_name(collection_key: str) -> str:
    if collection_key.startswith("kb_"):
        return collection_key
    return COLLECTIONS.get(collection_key, collection_key)


def _query_collection(collection_key: str, query_text: str, n_results: int = 3) -> list[str]:
    """Query one collection via Chroma when available, else JSON fallback."""
    tracer = get_tracer()
    collection_name = _resolve_collection_name(collection_key)

    tracer.trace_kb_query(
        stage="KB Retrieval",
        collection=collection_name,
        query=query_text,
        n_results=n_results,
    )

    chroma_count = _chroma_collection_counts.get(collection_name, 0)
    if chroma_count > 0:
        documents = _query_chroma(collection_name, query_text, n_results)
        mode = "chroma"
    else:
        documents = _query_json_fallback(collection_name, query_text, n_results)
        mode = "json_fallback"

    tracer.trace(
        stage="KB Retrieval",
        event_type="retrieval_mode",
        description=f"KB retrieval mode: {mode}",
        details={"collection": collection_name, "mode": mode, "chroma_count": chroma_count},
    )
    tracer.trace_kb_result(
        stage="KB Retrieval",
        collection=collection_name,
        num_results=len(documents),
        results=documents,
    )

    return documents


def _dedupe_results(results: list[str]) -> list[str]:
    """Deduplicate merged context snippets by deterministic content hash."""
    seen_hashes: set[int] = set()
    deduped: list[str] = []
    for item in results:
        content_hash = hash(item)
        if content_hash in seen_hashes:
            continue
        seen_hashes.add(content_hash)
        deduped.append(item)
    return deduped


def _query_collections(
    collection_names: list[str],
    query_text: str,
    *,
    n_results_per_collection: int,
    use_cache: bool = True,
) -> list[str]:
    """Query multiple collections with optional per-process cache and dedupe."""
    normalized_collections = tuple(collection_names)
    cache_key = (normalized_collections, hash((query_text or "")[:200]))

    if use_cache and cache_key in _kb_cache:
        get_tracer().trace(
            stage="KB Retrieval",
            event_type="cache_hit",
            description="KB multi-collection cache hit",
            details={"collections": list(normalized_collections), "query_prefix": query_text[:100]},
        )
        cached = _kb_cache[cache_key]
        return [item["text"] for item in cached]

    merged: list[str] = []
    for collection_name in collection_names:
        merged.extend(_query_collection(collection_name, query_text, n_results=n_results_per_collection))

    deduped = _dedupe_results(merged)
    if use_cache:
        _kb_cache[cache_key] = [{"text": item} for item in deduped]

    return deduped


def get_clause_classification_context(
    clause_text: str,
    n: int = 3,
    document_type: str = "default",
    use_cache: bool = True,
) -> str:
    """Retrieve clause taxonomy context with domain-aware routing."""
    domain_collections = _collections_for_document(document_type)
    candidates = [
        collection
        for collection in domain_collections
        if "clause_types" in collection or collection == "kb_standard_clauses"
    ]
    if not candidates:
        candidates = ["kb_clause_types", "kb_standard_clauses"]

    docs = _query_collections(
        candidates,
        clause_text,
        n_results_per_collection=n,
        use_cache=use_cache,
    )
    if not docs:
        return ""

    lines = ["RELEVANT CLAUSE TYPE DEFINITIONS:"]
    for idx, doc in enumerate(docs[: n * 2], 1):
        lines.append(f"{idx}. {doc}\n")
    return "\n".join(lines)


def get_risk_scoring_context(
    clause_text: str,
    clause_type: str = "",
    n: int = 4,
    document_type: str = "default",
    use_cache: bool = True,
) -> str:
    """Retrieve risk and red-flag context with domain-aware routing."""
    query = f"{clause_type} {clause_text}" if clause_type else clause_text
    domain_collections = _collections_for_document(document_type)
    candidates = [
        collection
        for collection in domain_collections
        if "risk_rules" in collection or collection == "kb_red_flags"
    ]
    if not candidates:
        candidates = ["kb_risk_rules", "kb_red_flags"]

    docs = _query_collections(
        candidates,
        query,
        n_results_per_collection=n,
        use_cache=use_cache,
    )
    if not docs:
        return ""

    lines = ["APPLICABLE RISK SCORING RULES:"]
    for idx, doc in enumerate(docs[: n * 2], 1):
        lines.append(f"{idx}. {doc}\n")
    return "\n".join(lines)


def get_missing_clauses_context(document_type: str, use_cache: bool = True) -> str:
    """Retrieve expected clause inventory for document type."""
    docs = _query_collections(
        ["kb_document_templates"],
        f"{document_type} agreement required clauses",
        n_results_per_collection=2,
        use_cache=use_cache,
    )
    if not docs:
        return ""
    return f"EXPECTED CLAUSES FOR {document_type.upper()}:\n" + "\n".join(docs)


def get_document_template_profile(document_type: str) -> dict[str, object]:
    """Return best-matching document template metadata from JSON KB."""
    normalized = (document_type or "").strip().lower()
    entries = _load_collection_entries("kb_document_templates")

    best_entry: dict[str, object] | None = None
    best_score = -1.0
    query_tokens = _tokenize(document_type)

    for entry in entries:
        metadata = entry.get("metadata", {})
        if not isinstance(metadata, dict):
            metadata = {}

        candidate_type = str(metadata.get("document_type") or "").strip().lower()
        score = 10.0 if candidate_type and candidate_type == normalized else 0.0
        score += _score_entry(query_tokens, entry)

        if score > best_score:
            best_score = score
            best_entry = entry

    if not best_entry:
        return {
            "document_type": document_type or "Other",
            "required_clauses": [],
            "recommended_clauses": [],
            "commonly_missing": [],
            "high_risk_if_missing": [],
            "description": "",
            "source": None,
        }

    metadata = best_entry.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    return {
        "document_type": metadata.get("document_type") or document_type or "Other",
        "required_clauses": list(metadata.get("required_clauses") or []),
        "recommended_clauses": list(metadata.get("recommended_clauses") or []),
        "commonly_missing": list(metadata.get("commonly_missing") or []),
        "high_risk_if_missing": list(metadata.get("high_risk_if_missing") or []),
        "description": str(best_entry.get("text") or "").strip(),
        "source": best_entry.get("id"),
    }


def get_negotiation_context(risk_type: str, clause_type: str = "", n: int = 3, use_cache: bool = True) -> str:
    """Retrieve negotiation context for identified risks."""
    query = f"{risk_type} {clause_type} negotiation strategy counter-proposal"
    docs = _query_collections(
        ["kb_negotiation"],
        query,
        n_results_per_collection=n,
        use_cache=use_cache,
    )
    if not docs:
        return ""
    return "NEGOTIATION STRATEGIES AND COUNTER-PROPOSALS:\n" + "\n".join(docs)


def get_compliance_context(contract_text_snippet: str, jurisdiction: str = "General", use_cache: bool = True) -> str:
    """Retrieve compliance context based on jurisdiction and content snippet."""
    docs = _query_collections(
        ["kb_compliance"],
        f"{jurisdiction} compliance {contract_text_snippet[:200]}",
        n_results_per_collection=3,
        use_cache=use_cache,
    )
    if not docs:
        return ""
    return f"RELEVANT COMPLIANCE REQUIREMENTS ({jurisdiction}):\n" + "\n".join(docs)


def get_plain_english_context(legal_term: str, use_cache: bool = True) -> str:
    """Retrieve glossary-style plain-English context for a legal term."""
    docs = _query_collections(
        ["kb_legal_glossary"],
        legal_term,
        n_results_per_collection=2,
        use_cache=use_cache,
    )
    if not docs:
        return ""
    return "LEGAL TERM DEFINITIONS:\n" + "\n".join(docs)


def get_full_pass2_context(
    clause_text: str,
    clause_type: str = "",
    document_type: str = "default",
    use_cache: bool = True,
) -> str:
    """Compose pass-2 context from clause classification and risk retrieval."""
    classification_ctx = get_clause_classification_context(
        clause_text,
        document_type=document_type,
        use_cache=use_cache,
    )
    risk_ctx = get_risk_scoring_context(
        clause_text,
        clause_type,
        document_type=document_type,
        use_cache=use_cache,
    )

    parts = [part for part in (classification_ctx, risk_ctx) if part]
    if not parts:
        return ""

    return (
        "\n\n━━━ KNOWLEDGE BASE CONTEXT (use this to improve accuracy) ━━━\n"
        + "\n\n".join(parts)
        + "\n━━━ END KNOWLEDGE BASE CONTEXT ━━━\n"
    )


def get_full_pass5_context(
    contract_text: str,
    document_type: str,
    jurisdiction: str,
    identified_risks: list[str],
    use_cache: bool = True,
) -> str:
    """Compose pass-5 context from missing-clause, negotiation, and compliance retrieval."""
    parts: list[str] = []

    missing_ctx = get_missing_clauses_context(document_type, use_cache=use_cache)
    if missing_ctx:
        parts.append(missing_ctx)

    for risk_type in identified_risks[:5]:
        neg_ctx = get_negotiation_context(risk_type, use_cache=use_cache)
        if neg_ctx:
            parts.append(neg_ctx)
            break

    compliance_ctx = get_compliance_context(contract_text[:300], jurisdiction, use_cache=use_cache)
    if compliance_ctx:
        parts.append(compliance_ctx)

    if not parts:
        return ""

    return (
        "\n\n━━━ KNOWLEDGE BASE CONTEXT (use this to improve accuracy) ━━━\n"
        + "\n\n".join(parts)
        + "\n━━━ END KNOWLEDGE BASE CONTEXT ━━━\n"
    )


def retrieve_context(query_text: str, n_results: int = 5, use_cache: bool = True) -> str:
    """Compatibility helper for legacy callers."""
    parts: list[str] = []
    clause_ctx = get_clause_classification_context(query_text, n=min(3, n_results), use_cache=use_cache)
    if clause_ctx:
        parts.append(clause_ctx)
    risk_ctx = get_risk_scoring_context(query_text, n=min(4, n_results), use_cache=use_cache)
    if risk_ctx:
        parts.append(risk_ctx)
    glossary_ctx = get_plain_english_context(query_text, use_cache=use_cache)
    if glossary_ctx:
        parts.append(glossary_ctx)
    return "\n\n".join(parts)


def retrieve_context_for_clause(
    clause_text: str,
    clause_heading: str,
    document_type: str = "default",
    use_cache: bool = True,
) -> str:
    """Compatibility helper used by clause extraction path."""
    return get_full_pass2_context(
        clause_text=clause_text,
        clause_type=clause_heading,
        document_type=document_type,
        use_cache=use_cache,
    )


def initialize_kb() -> None:
    """Initialize KB status and emit retrieval-mode observability info."""
    tracer = get_tracer()
    total_documents = 0
    print("[OK] Knowledge base initialized")
    for collection_name in COLLECTIONS.values():
        entries = _load_collection_entries(collection_name)
        total_documents += len(entries)
        print(f"  - {collection_name}: {len(entries)} documents")

    print(f"  - total: {total_documents} documents")

    if _chroma_collection_counts and any(count > 0 for count in _chroma_collection_counts.values()):
        tracer.trace(
            stage="KB Initialization",
            event_type="chroma_state",
            description="ChromaDB collection state",
            details={"collections": _chroma_collection_counts},
        )
    else:
        warning = (
            "ChromaDB collections are empty - using JSON fallback retrieval. "
            "Run scripts/build_chroma_kb.py to populate."
        )
        tracer.trace(
            stage="KB Initialization",
            event_type="warning",
            description=warning,
            details={},
        )
        print(f"[WARN] {warning}")
