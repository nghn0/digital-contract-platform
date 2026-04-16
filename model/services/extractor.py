"""Multi-pass legal extraction pipeline with strict, generalized intelligence output."""

from __future__ import annotations

import asyncio
import json
import re
from datetime import datetime
from typing import Any

from config.runtime_limits import CLAUSE_BATCH_SIZE, MAX_PARALLEL_REQUESTS, PASS_TOKEN_LIMITS, get_batch_token_limit
from core.llm_config import LLM_CONFIG, UnifiedLLMClient, call_llm_async as provider_call_llm_async, get_active_model_name, get_llm_client
from core.prompts import (
    PASS_4_FINANCIAL_LLM,
    PASS_1_METADATA_PARTIES,
    PASS_2_CLAUSES,
    PASS_3_OBLIGATIONS,
    PASS_5_MISSING_DEPS,
    PASS_5_NEGOTIATION,
    PASS_5_RISKS,
    PASS_5_SUMMARY,
    SYSTEM_PROMPT,
)
from models.schema import (
    Clause,
    ClauseCategory,
    ClauseDependency,
    ComplianceFlag,
    DocumentMetadata,
    DocumentProfile,
    DocumentSummary,
    DocumentType,
    FinancialTerms,
    LegalDocumentAnalysis,
    LinkedDocument,
    MissingClause,
    NegotiationPoint,
    Obligation,
    PartiesSection,
    Party,
    PaymentTerms,
    Right,
    RiskItem,
    RiskType,
    RiskLevel,
    Signatory,
    TimelineEvent,
)
from services.extractor_strict_integration import validate_clause_extraction, validate_metadata_extraction, validate_pipeline_stage
from services.rag_service import clear_kb_cache, get_document_template_profile, get_full_pass5_context, initialize_kb, retrieve_context_for_clause
from services.tracing import get_tracer
from services.validator import _get_required_clauses_for_document


def _attempt_local_json_repair(text: str) -> str | None:
    """Attempt lightweight local repairs for malformed JSON output.

    The repair path is intentionally conservative and avoids semantic edits.
    It handles common formatting defects produced by model responses.
    """
    if not text:
        return None

    repaired = text.lstrip("\ufeff")
    repaired = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F]", "", repaired)

    # Remove trailing commas before object/array close.
    repaired = re.sub(r",\s*([}\]])", r"\1", repaired)

    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        pass

    open_braces = repaired.count("{") - repaired.count("}")
    open_brackets = repaired.count("[") - repaired.count("]")
    if open_braces > 0 or open_brackets > 0:
        repaired = repaired.rstrip() + ("}" * max(open_braces, 0)) + ("]" * max(open_brackets, 0))

    try:
        json.loads(repaired)
        return repaired
    except json.JSONDecodeError:
        return None


def _parse_json_from_text(raw_text: str) -> Any:
    text = (raw_text or "").strip()
    if not text:
        raise ValueError("Empty LLM response content")

    text = text.replace("```json", "").replace("```", "").strip()

    candidates = [text]
    start_obj = text.find("{")
    end_obj = text.rfind("}")
    if start_obj != -1 and end_obj != -1 and end_obj > start_obj:
        candidates.append(text[start_obj : end_obj + 1])

    start_arr = text.find("[")
    end_arr = text.rfind("]")
    if start_arr != -1 and end_arr != -1 and end_arr > start_arr:
        candidates.append(text[start_arr : end_arr + 1])

    decoder = json.JSONDecoder()
    last_error: json.JSONDecodeError | None = None
    for candidate in candidates:
        try:
            parsed = json.loads(candidate)
            if isinstance(parsed, (dict, list)):
                return parsed
            raise ValueError("LLM JSON payload must be an object or array")
        except json.JSONDecodeError as exc:
            last_error = exc

            # Accept first decodable JSON object/array even if extra text follows.
            for opener in ("{", "["):
                start = candidate.find(opener)
                while start != -1:
                    try:
                        parsed, _ = decoder.raw_decode(candidate[start:])
                        if isinstance(parsed, (dict, list)):
                            return parsed
                    except json.JSONDecodeError:
                        pass
                    start = candidate.find(opener, start + 1)

            repaired = _attempt_local_json_repair(candidate)
            if repaired is None:
                continue
            try:
                parsed = json.loads(repaired)
                if isinstance(parsed, (dict, list)):
                    return parsed
                raise ValueError("LLM JSON payload must be an object or array")
            except json.JSONDecodeError:
                continue

    if last_error is not None:
        raise last_error
    raise ValueError("Unable to parse LLM JSON payload")


def _normalize_document_type(value: str | None) -> DocumentType | None:
    if not value:
        return None
    normalized = value.strip().lower()
    mapping = {
        "nda": DocumentType.NDA,
        "msa": DocumentType.MSA,
        "sla": DocumentType.SLA,
        "employment": DocumentType.EMPLOYMENT,
        "lease": DocumentType.LEASE,
        "loan": DocumentType.LOAN,
        "partnership": DocumentType.PARTNERSHIP,
        "vendor": DocumentType.VENDOR,
        "consulting": DocumentType.CONSULTING,
        "ip assignment": DocumentType.IP_ASSIGNMENT,
        "other": DocumentType.OTHER,
    }
    return mapping.get(normalized, DocumentType.OTHER)


def _normalize_category(value: Any) -> ClauseCategory:
    if isinstance(value, ClauseCategory):
        return value
    normalized = str(value or "").strip().lower()
    mapping = {
        "obligation": ClauseCategory.OBLIGATION,
        "right": ClauseCategory.RIGHT,
        "prohibition": ClauseCategory.PROHIBITION,
        "condition": ClauseCategory.CONDITION,
        "definition": ClauseCategory.DEFINITION,
        "remedy": ClauseCategory.REMEDY,
        "representation": ClauseCategory.REPRESENTATION,
    }
    return mapping.get(normalized, ClauseCategory.DEFINITION)


def _normalize_risk_level(value: Any) -> RiskLevel:
    if isinstance(value, RiskLevel):
        return value
    normalized = str(value or "LOW").strip().upper()
    mapping = {
        "LOW": RiskLevel.LOW,
        "MEDIUM": RiskLevel.MEDIUM,
        "HIGH": RiskLevel.HIGH,
        "CRITICAL": RiskLevel.CRITICAL,
    }
    return mapping.get(normalized, RiskLevel.LOW)


def _coerce_str_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    return [text] if text else []


def _coerce_optional_text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, list):
        parts = [str(item).strip() for item in value if str(item).strip()]
        return ", ".join(parts) if parts else None
    if isinstance(value, dict):
        parts = [str(item).strip() for item in value.values() if str(item).strip()]
        return ", ".join(parts) if parts else None
    text = str(value).strip()
    return text or None


def _normalize_clause_fingerprint_text(value: str | None) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _dedupe_clauses(clauses: list[Clause]) -> list[Clause]:
    """Remove exact duplicate clauses while preserving the first occurrence and clause IDs."""
    seen: set[tuple[str, str]] = set()
    deduped: list[Clause] = []

    for clause in clauses:
        key = (
            _normalize_clause_fingerprint_text(clause.heading),
            _normalize_clause_fingerprint_text(clause.text),
        )
        if key in seen:
            continue
        seen.add(key)
        deduped.append(clause)

    return deduped


def _infer_clause_type(heading: str | None, text: str | None) -> str:
    hay = f"{heading or ''} {text or ''}".lower()
    if any(k in hay for k in ["fee", "payment", "payable", "invoice"]):
        return "Payment"
    if any(k in hay for k in ["amendment", "ratification", "reaffirmation"]):
        return "Amendment"
    if any(k in hay for k in ["governing law", "jurisdiction"]):
        return "Governing Law"
    if any(k in hay for k in ["waiver", "release", "liability", "indemn"]):
        return "Liability"
    return "Other"


def _infer_source_section(heading: str | None, text: str | None) -> str:
    hay = f"{heading or ''} {text or ''}".lower()
    nda_markers = [
        "non-disclosure",
        "nda",
        "confidential information",
        "disclosing party",
        "receiving party",
        "return or destruction",
    ]
    employment_markers = [
        "internship",
        "employment",
        "roles and responsibilities",
        "code of conduct",
        "reporting to",
        "working hours",
    ]

    nda_score = sum(1 for marker in nda_markers if marker in hay)
    employment_score = sum(1 for marker in employment_markers if marker in hay)

    if nda_score > employment_score and nda_score > 0:
        return "NDA"
    if employment_score > 0:
        return "Employment"
    return "General"


def _detect_document_subtypes(metadata: DocumentMetadata, clauses: list[Clause], contract_text: str) -> list[str]:
    signals: set[str] = set()
    if metadata.document_type and metadata.document_type != DocumentType.OTHER:
        signals.add(metadata.document_type.value)

    hay = f"{contract_text} {' '.join((c.heading or '') + ' ' + (c.text or '') for c in clauses)}".lower()

    if re.search(r"\bnda\b|non[-\s]?disclosure|confidential information|disclosing party|receiving party", hay):
        signals.add(DocumentType.NDA.value)
    if re.search(r"\bemployment\b|\binternship\b|roles and responsibilities|code of conduct", hay):
        signals.add(DocumentType.EMPLOYMENT.value)
    if re.search(r"\bloan\b|\bborrower\b|\blender\b|interest rate", hay):
        signals.add(DocumentType.LOAN.value)
    if re.search(r"\blease\b|\blandlord\b|\btenant\b|\bpremises\b", hay):
        signals.add(DocumentType.LEASE.value)

    preferred_order = [
        DocumentType.EMPLOYMENT.value,
        DocumentType.NDA.value,
        DocumentType.LOAN.value,
        DocumentType.LEASE.value,
        DocumentType.MSA.value,
        DocumentType.SLA.value,
        DocumentType.PARTNERSHIP.value,
        DocumentType.VENDOR.value,
        DocumentType.CONSULTING.value,
        DocumentType.IP_ASSIGNMENT.value,
    ]
    ordered = [item for item in preferred_order if item in signals]
    extras = sorted(item for item in signals if item not in ordered)
    return ordered + extras


def _derive_risk_score(level: RiskLevel, score: int) -> int:
    bounded = max(0, min(100, int(score)))
    if bounded > 0:
        return bounded
    defaults = {
        RiskLevel.LOW: 20,
        RiskLevel.MEDIUM: 45,
        RiskLevel.HIGH: 75,
        RiskLevel.CRITICAL: 92,
    }
    return defaults[level]


def _document_type_text(document_type: DocumentType | None) -> str:
    return document_type.value if document_type else "Other"


def _build_document_profile(metadata: DocumentMetadata, clauses: list[Clause], contract_text: str) -> DocumentProfile:
    template_profile = get_document_template_profile(_document_type_text(metadata.document_type))
    observed_types = sorted({clause.type for clause in clauses if clause.type})
    observed_headings = sorted({clause.heading for clause in clauses if clause.heading})
    subtypes = _detect_document_subtypes(metadata, clauses, contract_text)
    source_sections = sorted({_infer_source_section(clause.heading, clause.text) for clause in clauses if clause.text})

    reasoning = [
        f"Detected type from metadata: {_document_type_text(metadata.document_type)}",
        f"Observed clause types: {', '.join(observed_types[:8]) or 'none'}",
    ]
    if metadata.document_subtype:
        reasoning.append(f"Subtype hint: {metadata.document_subtype}")
    if metadata.parent_agreement_ref:
        reasoning.append(f"Parent agreement reference: {metadata.parent_agreement_ref}")
    if len(subtypes) > 1:
        reasoning.append(f"Hybrid document detected with subtypes: {', '.join(subtypes)}")

    required_clauses = _coerce_str_list(template_profile.get("required_clauses"))
    recommended_clauses = _coerce_str_list(template_profile.get("recommended_clauses"))
    high_risk_clauses = _coerce_str_list(template_profile.get("high_risk_if_missing"))

    extensions = {
        "source": template_profile.get("source"),
        "commonly_missing": _coerce_str_list(template_profile.get("commonly_missing")),
        "observed_clause_types": observed_types,
        "observed_headings": observed_headings[:20],
        "subtypes": subtypes,
        "source_sections": source_sections,
        "detected_type_label": "Hybrid" if len(subtypes) > 1 else _document_type_text(metadata.document_type),
        "jurisdiction": metadata.jurisdiction,
        "governing_law": metadata.governing_law,
        "linked_documents": [
            ref
            for ref in [metadata.parent_agreement_ref, metadata.amendment_number]
            if ref
        ],
    }

    confidence = 0.35
    if metadata.document_type and metadata.document_type != DocumentType.OTHER:
        confidence += 0.25
    if required_clauses:
        confidence += 0.15
    if observed_types:
        confidence += 0.15
    if metadata.document_subtype:
        confidence += 0.05

    return DocumentProfile(
        detected_type=metadata.document_type,
        subtype=(f"Hybrid: {', '.join(subtypes)}" if len(subtypes) > 1 else metadata.document_subtype),
        confidence=min(1.0, confidence),
        reasoning=reasoning,
        required_clauses=required_clauses,
        recommended_clauses=recommended_clauses,
        high_risk_clauses=high_risk_clauses,
        extensions=extensions,
    )


def _derive_risk_labels(risk_type: RiskType, reason: str, clause_text: str = "") -> list[str]:
    labels = {risk_type.value}
    lowered = f"{reason} {clause_text}".lower()

    keyword_map = {
        "liability": "liability",
        "termination": "termination",
        "payment": "payment",
        "privacy": "privacy",
        "data": "data",
        "jurisdiction": "jurisdiction",
        "law": "governing-law",
        "ip": "intellectual-property",
        "indemn": "indemnification",
        "non-compete": "non-compete",
        "renewal": "renewal",
        "force majeure": "force-majeure",
        "default": "default",
        "collateral": "security",
    }
    for needle, label in keyword_map.items():
        if needle in lowered:
            labels.add(label)

    return sorted(labels)


def _build_clause_dependency_graph(clauses: list[Clause], dependencies: list[ClauseDependency]) -> dict[str, Any]:
    nodes = [
        {
            "clause_id": clause.clause_id,
            "heading": clause.heading,
            "type": clause.type,
            "risk_level": clause.risk_level.value,
            "risk_score": clause.risk_score,
        }
        for clause in clauses
    ]
    edges = []
    for dependency in dependencies:
        edges.append(
            {
                "source": dependency.source_clause or dependency.clause_id_1,
                "target": dependency.target_clause or dependency.clause_id_2,
                "relation_type": dependency.relation_type,
                "description": dependency.description,
                "cross_document_reference": dependency.cross_document_reference,
            }
        )

    return {
        "nodes": nodes,
        "edges": edges,
        "node_count": len(nodes),
        "edge_count": len(edges),
    }


def _build_linked_documents(metadata: DocumentMetadata, document_profile: DocumentProfile, clauses: list[Clause]) -> list[LinkedDocument]:
    links: list[LinkedDocument] = []
    parent_ref = metadata.parent_agreement_ref
    if parent_ref:
        links.append(
            LinkedDocument(
                reference_text=parent_ref,
                relation_type="parent_agreement",
                document_type=DocumentType.LOAN if metadata.document_type == DocumentType.LOAN else metadata.document_type,
                confidence=0.9 if metadata.document_type else 0.6,
                notes="Detected from metadata.parent_agreement_ref",
            )
        )

    if metadata.amendment_number:
        links.append(
            LinkedDocument(
                reference_text=metadata.amendment_number,
                relation_type="amendment",
                document_type=metadata.document_type,
                confidence=0.85,
                notes="Detected from metadata.amendment_number",
            )
        )

    for ref in _coerce_str_list(document_profile.extensions.get("linked_documents")):
        if not ref:
            continue
        if any(link.reference_text == ref for link in links):
            continue
        links.append(
            LinkedDocument(
                reference_text=ref,
                relation_type="related_document",
                document_type=metadata.document_type,
                confidence=0.5,
                notes="Detected from document profile extension",
            )
        )

    if not links:
        for clause in clauses:
            for ref in clause.cross_references:
                normalized = ref.strip()
                if normalized and not any(link.reference_text == normalized for link in links):
                    links.append(
                        LinkedDocument(
                            reference_text=normalized,
                            relation_type="cross_reference",
                            document_type=metadata.document_type,
                            confidence=0.35,
                            notes=f"Referenced by clause {clause.clause_id}",
                            source_clause_id=clause.clause_id,
                        )
                    )

    return links


def call_llm(
    system: str,
    user_message: str,
    json_mode: bool = True,
    *,
    max_tokens: int | None = None,
) -> dict[str, Any]:
    """Unified LLM call with strict JSON parsing and one parse-retry."""
    tracer = get_tracer()

    try:
        token_budget = max_tokens if max_tokens is not None else LLM_CONFIG.max_tokens

        tracer.trace_llm_call(
            stage="Extraction",
            system_prompt=system,
            user_message=user_message,
            model=get_active_model_name(),
            temperature=LLM_CONFIG.temperature,
            max_tokens=token_budget,
        )

        client_bundle = get_llm_client()
        client: UnifiedLLMClient = client_bundle["client"]

        response = client.messages.create(
            model=get_active_model_name(),
            max_tokens=token_budget,
            temperature=LLM_CONFIG.temperature,
            messages=[{"role": "user", "content": user_message}],
            system=system,
            top_p=LLM_CONFIG.top_p,
        )

        raw_text = (response.content[0].text if response.content else "").strip()

        if json_mode:
            try:
                parsed = _parse_json_from_text(raw_text)
            except (json.JSONDecodeError, ValueError):
                retry_prompt = user_message + "\n\nReturn ONLY valid JSON. No markdown, no prose."
                retry_response = client.messages.create(
                    model=get_active_model_name(),
                    max_tokens=token_budget,
                    temperature=LLM_CONFIG.temperature,
                    messages=[{"role": "user", "content": retry_prompt}],
                    system=system,
                    top_p=LLM_CONFIG.top_p,
                )
                raw_text = (retry_response.content[0].text if retry_response.content else "").strip()
                parsed = _parse_json_from_text(raw_text)

            tracer.trace_llm_response(stage="Extraction", response_text=raw_text, parsed_json=parsed)
            return parsed

        tracer.trace_llm_response(stage="Extraction", response_text=raw_text)
        return {"text": raw_text}

    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError, KeyError) as e:
        tracer.trace_error("Extraction", str(e), "LLMCallError", {"exception": str(e)})
        raise RuntimeError(f"LLM call failed: {str(e)}")


async def _call_llm_async_json(system: str, user_message: str, *, max_tokens: int) -> Any:
    """Async JSON LLM helper using core async client path with parse-retry."""
    tracer = get_tracer()
    tracer.trace_llm_call(
        stage="Extraction",
        system_prompt=system,
        user_message=user_message,
        model=get_active_model_name(),
        temperature=LLM_CONFIG.temperature,
        max_tokens=max_tokens,
    )

    raw_text = await provider_call_llm_async(
        system,
        user_message,
        max_tokens=max_tokens,
        temperature=LLM_CONFIG.temperature,
        top_p=LLM_CONFIG.top_p,
    )

    try:
        parsed = _parse_json_from_text(raw_text)
    except (json.JSONDecodeError, ValueError):
        retry_prompt = user_message + "\n\nReturn ONLY valid JSON. No markdown, no prose."
        raw_text = await provider_call_llm_async(
            system,
            retry_prompt,
            max_tokens=max_tokens,
            temperature=LLM_CONFIG.temperature,
            top_p=LLM_CONFIG.top_p,
        )
        parsed = _parse_json_from_text(raw_text)

    tracer.trace_llm_response(stage="Extraction", response_text=raw_text, parsed_json=parsed)
    return parsed


def extract_metadata_and_parties(contract_text: str) -> tuple[DocumentMetadata, PartiesSection]:
    prompt = PASS_1_METADATA_PARTIES.format(contract_text=contract_text)
    result = call_llm(
        SYSTEM_PROMPT,
        prompt,
        json_mode=True,
        max_tokens=PASS_TOKEN_LIMITS["pass_1_metadata"],
    )

    meta_raw = result.get("metadata", {})
    metadata = DocumentMetadata(
        document_type=_normalize_document_type(meta_raw.get("document_type")),
        document_subtype=meta_raw.get("document_subtype"),
        title=meta_raw.get("title"),
        effective_date=meta_raw.get("effective_date"),
        execution_date=meta_raw.get("execution_date"),
        expiration_date=meta_raw.get("expiration_date"),
        auto_renewal=meta_raw.get("auto_renewal"),
        renewal_notice_period=meta_raw.get("renewal_notice_period"),
        jurisdiction=meta_raw.get("jurisdiction"),
        governing_law=meta_raw.get("governing_law"),
        venue=meta_raw.get("venue"),
        language=meta_raw.get("language", "English"),
        amendment_number=meta_raw.get("amendment_number"),
        parent_agreement_ref=meta_raw.get("parent_agreement_ref"),
        confidentiality_classification=meta_raw.get("confidentiality_classification"),
    )

    parties_raw = result.get("parties", {})
    parties = PartiesSection(
        parties=[
            Party(
                name=str(p.get("name") or "Unknown"),
                legal_entity_type=p.get("legal_entity_type"),
                role=str(p.get("role") or "Party"),
                address=p.get("address"),
                country=p.get("country"),
                registration_number=p.get("registration_number"),
            )
            for p in parties_raw.get("parties", [])
            if isinstance(p, dict)
        ],
        signatories=[
            Signatory(
                name=str(s.get("name") or "Unknown"),
                company=str(s.get("company") or ""),
                designation=str(s.get("designation") or ""),
                email=s.get("email"),
                signing_date=s.get("signing_date"),
                signing_authority=s.get("signing_authority"),
            )
            for s in parties_raw.get("signatories", [])
            if isinstance(s, dict)
        ],
        beneficiaries=_coerce_str_list(parties_raw.get("beneficiaries")),
        excluded_parties=_coerce_str_list(parties_raw.get("excluded_parties")),
    )

    return metadata, parties


def extract_clauses(clauses_with_headings: list[tuple[str, str]], metadata: DocumentMetadata, parties: PartiesSection) -> list[Clause]:
    tracer = get_tracer()
    parties_json = json.dumps({"parties": [{"name": p.name, "role": p.role} for p in parties.parties]}, ensure_ascii=True)
    document_profile_hint = json.dumps(
        {
            "document_type": _document_type_text(metadata.document_type),
            "document_subtype": metadata.document_subtype,
            "parent_agreement_ref": metadata.parent_agreement_ref,
            "amendment_number": metadata.amendment_number,
            "jurisdiction": metadata.jurisdiction,
            "governing_law": metadata.governing_law,
        },
        ensure_ascii=True,
    )

    def _to_clause(result: dict[str, Any], clause_id: str, heading: str, clause_text: str) -> Clause:
        normalized_level = _normalize_risk_level(result.get("risk_level"))
        normalized_type = str(result.get("type") or "").strip() or _infer_clause_type(heading, clause_text)
        normalized_score = _derive_risk_score(normalized_level, int(result.get("risk_score") or 0))
        risk_justification = str(result.get("risk_justification") or "").strip()
        if not risk_justification:
            risk_justification = f"Risk inferred from clause language in '{heading or clause_id}'."

        source_section = _infer_source_section(heading, clause_text)
        tags = _coerce_str_list(result.get("tags"))
        section_tag = f"source_section:{source_section}"
        if section_tag not in tags:
            tags.append(section_tag)

        return Clause(
            clause_id=str(result.get("clause_id") or clause_id),
            section_number=result.get("section_number"),
            heading=result.get("heading") or heading,
            text=str(clause_text),
            plain_english=str(result.get("plain_english") or clause_text[:280]),
            type=normalized_type,
            category=_normalize_category(result.get("category")),
            risk_level=normalized_level,
            risk_score=normalized_score,
            risk_justification=risk_justification,
            affected_party=_coerce_optional_text(result.get("affected_party")),
            obligations=_coerce_str_list(result.get("obligations")),
            rights=_coerce_str_list(result.get("rights")),
            deadlines=_coerce_str_list(result.get("deadlines")),
            is_unilateral=bool(result.get("is_unilateral", False)),
            is_mutual=bool(result.get("is_mutual", False)),
            is_standard=bool(result.get("is_standard", True)),
            is_ambiguous=bool(result.get("is_ambiguous", False)),
            ambiguity_reason=result.get("ambiguity_reason"),
            tags=tags,
            cross_references=_coerce_str_list(result.get("cross_references")),
        )

    async def _extract_batch(
        semaphore: asyncio.Semaphore,
        batch_start: int,
        batch: list[tuple[str, str]],
    ) -> list[Clause]:
        batch_contexts: list[str] = []
        clauses_block_lines: list[str] = []

        for offset, (heading, clause_text) in enumerate(batch, 1):
            clause_id = str(batch_start + offset)
            kb_context = retrieve_context_for_clause(
                clause_text,
                heading,
                document_type=_document_type_text(metadata.document_type),
            )
            if kb_context:
                batch_contexts.append(kb_context)
            clauses_block_lines.append(
                f"---CLAUSE {offset}---\nCLAUSE ID: {clause_id}\nHEADING: {heading}\nBODY: {clause_text}\n"
            )

        rag_context = "\n\n".join(batch_contexts[:6])
        prompt = PASS_2_CLAUSES.format(
            document_profile_json=document_profile_hint,
            parties_json=parties_json,
            rag_context=rag_context,
            clauses_block="\n".join(clauses_block_lines),
            expected_count=len(batch),
        )

        tracer.trace(
            stage="Stage 3",
            event_type="batch_dispatch",
            description="Dispatching pass-2 clause batch",
            details={"batch_start": batch_start, "batch_size": len(batch)},
        )

        async with semaphore:
            try:
                parsed = await _call_llm_async_json(
                    SYSTEM_PROMPT,
                    prompt,
                    max_tokens=get_batch_token_limit(len(batch)),
                )
            except (RuntimeError, json.JSONDecodeError, ValueError) as error:
                validate_clause_extraction(
                    stage="extract_clauses_batch",
                    error=error,
                    clause_text="\n".join(text for _, text in batch),
                    llm_output=None,
                )
                return []

        items = parsed if isinstance(parsed, list) else [parsed]
        clauses_out: list[Clause] = []
        for offset, (heading, clause_text) in enumerate(batch, 1):
            clause_id = str(batch_start + offset)
            item = items[offset - 1] if offset - 1 < len(items) and isinstance(items[offset - 1], dict) else {}
            clauses_out.append(_to_clause(item, clause_id, heading, clause_text))

        return clauses_out

    async def _extract_all() -> list[Clause]:
        semaphore = asyncio.Semaphore(MAX_PARALLEL_REQUESTS)
        tasks: list[asyncio.Task[list[Clause]]] = []
        for start in range(0, len(clauses_with_headings), CLAUSE_BATCH_SIZE):
            batch = clauses_with_headings[start : start + CLAUSE_BATCH_SIZE]
            tasks.append(asyncio.create_task(_extract_batch(semaphore, start, batch)))
        results = await asyncio.gather(*tasks)
        extracted = [clause for batch in results for clause in batch]
        extracted.sort(key=lambda clause: int(clause.clause_id) if clause.clause_id.isdigit() else 10_000)
        return extracted

    return asyncio.run(_extract_all())


def _extract_obligations_rights_timelines(contract_text: str, parties: PartiesSection, clauses: list[Clause]) -> tuple[list[Obligation], list[Right], list[TimelineEvent]]:
    clause_refs = [{"clause_id": c.clause_id, "heading": c.heading, "text": c.text[:500]} for c in clauses]
    document_profile_hint = json.dumps(
        {
            "observed_clause_types": sorted({c.type for c in clauses if c.type}),
            "observed_headings": [c.heading for c in clauses[:20] if c.heading],
            "linked_document_refs": sorted({ref for c in clauses for ref in c.cross_references}),
        },
        ensure_ascii=True,
    )
    prompt = PASS_3_OBLIGATIONS.format(
        contract_text=contract_text,
        parties_json=json.dumps([{"name": p.name, "role": p.role} for p in parties.parties], ensure_ascii=True),
        document_profile_json=document_profile_hint,
        clause_ids_json=json.dumps(clause_refs, ensure_ascii=True),
    )

    parsed = call_llm(
        SYSTEM_PROMPT,
        prompt,
        json_mode=True,
        max_tokens=PASS_TOKEN_LIMITS["pass_3_obligations"],
    )
    obligations_raw = parsed.get("obligations", [])
    rights_raw = parsed.get("rights", [])
    timelines_raw = parsed.get("timelines", [])

    obligations = [
        Obligation(
            party=str(item.get("party") or "Unknown"),
            action=str(item.get("action") or ""),
            clause_id=item.get("clause_id"),
            deadline=item.get("deadline"),
            consequence_of_breach=item.get("consequence_of_breach"),
            is_recurring=bool(item.get("is_recurring", False)),
        )
        for item in obligations_raw
        if isinstance(item, dict) and str(item.get("action") or "").strip()
    ]

    rights = [
        Right(
            party=str(item.get("party") or "Unknown"),
            right=str(item.get("right") or ""),
            clause_id=item.get("clause_id"),
            conditions=item.get("conditions"),
            is_exclusive=bool(item.get("is_exclusive", False)),
        )
        for item in rights_raw
        if isinstance(item, dict) and str(item.get("right") or "").strip()
    ]

    timelines = [
        TimelineEvent(
            event=str(item.get("event") or ""),
            timeframe=str(item.get("timeframe") or ""),
            trigger=item.get("trigger"),
            party_responsible=item.get("party_responsible"),
            clause_id=item.get("clause_id"),
            is_hard_deadline=bool(item.get("is_hard_deadline", False)),
        )
        for item in timelines_raw
        if isinstance(item, dict) and str(item.get("event") or "").strip() and str(item.get("timeframe") or "").strip()
    ]

    # Keep outputs complete for dashboard fields without contract-type assumptions.
    if not obligations:
        obligations = [
            Obligation(
                party=c.affected_party or "Unknown",
                action=text,
                clause_id=c.clause_id,
                deadline=None,
                consequence_of_breach=None,
                is_recurring=False,
            )
            for c in clauses
            for text in c.obligations
            if text
        ]

    if not rights:
        rights = [
            Right(
                party=c.affected_party or "Unknown",
                right=text,
                clause_id=c.clause_id,
                conditions=None,
                is_exclusive=False,
            )
            for c in clauses
            for text in c.rights
            if text
        ]

    if not timelines:
        timelines = [
            TimelineEvent(
                event=f"Deadline from {c.heading or c.clause_id}",
                timeframe=deadline,
                trigger=None,
                party_responsible=c.affected_party,
                clause_id=c.clause_id,
                is_hard_deadline=True,
            )
            for c in clauses
            for deadline in c.deadlines
            if deadline
        ]

    return obligations, rights, timelines


def _score_clause_match(reference_text: str, clause: Clause) -> int:
    hay = f"{clause.heading or ''} {clause.type or ''} {clause.text or ''}".lower()
    tokens = set(re.findall(r"[a-z0-9']+", (reference_text or "").lower()))
    if not tokens:
        return 0
    return sum(1 for token in tokens if len(token) > 2 and token in hay)


def _normalize_clause_references(
    obligations: list[Obligation],
    rights: list[Right],
    timelines: list[TimelineEvent],
    clauses: list[Clause],
) -> tuple[list[Obligation], list[Right], list[TimelineEvent]]:
    """Ensure extracted cross-sections always point to valid clause_ids."""
    if not clauses:
        return obligations, rights, timelines

    valid_ids = {clause.clause_id for clause in clauses}

    def _best_clause_id(reference_text: str) -> str:
        ranked = sorted(clauses, key=lambda clause: _score_clause_match(reference_text, clause), reverse=True)
        if ranked and _score_clause_match(reference_text, ranked[0]) > 0:
            return ranked[0].clause_id
        return clauses[0].clause_id

    for item in obligations:
        if not item.clause_id or item.clause_id not in valid_ids:
            item.clause_id = _best_clause_id(f"{item.action} {item.party}")

    for item in rights:
        if not item.clause_id or item.clause_id not in valid_ids:
            item.clause_id = _best_clause_id(f"{item.right} {item.party}")

    for item in timelines:
        if not item.clause_id or item.clause_id not in valid_ids:
            item.clause_id = _best_clause_id(f"{item.event} {item.timeframe} {item.party_responsible or ''}")

    return obligations, rights, timelines


def _build_financial_terms_fallback(clauses: list[Clause]) -> FinancialTerms:
    """Fallback regex/rule financial synthesis when LLM output is unavailable."""
    combined = "\n".join(c.text for c in clauses)
    money_values = re.findall(r"(?:\$|USD\s?)\s?[\d,]+(?:\.\d{2})?", combined, flags=re.IGNORECASE)
    due_days = re.search(r"(\d+)\s+days?", combined, flags=re.IGNORECASE)
    interest = re.search(r"(\d+(?:\.\d+)?)\s*%\s*(?:per\s*annum|per\s*year|per\s*month)", combined, flags=re.IGNORECASE)
    payment_method = "Wire transfer" if re.search(r"wire|available funds|electronic transfer", combined, re.IGNORECASE) else None

    payment_terms = PaymentTerms(
        currency="USD" if "$" in combined.upper() or "USD" in combined.upper() else None,
        total_contract_value=money_values[0] if money_values else None,
        payment_schedule="Periodic" if re.search(r"monthly|quarterly|annually|per month|per quarter", combined, re.IGNORECASE) else None,
        amount_per_period=money_values[1] if len(money_values) > 1 else (money_values[0] if money_values else None),
        due_days=int(due_days.group(1)) if due_days else None,
        payment_method=payment_method,
        advance_payment=None,
        late_payment_interest=f"{interest.group(1)}%" if interest else None,
        invoice_period="As invoiced" if re.search(r"invoice", combined, re.IGNORECASE) else None,
    )

    penalties = [
        c.heading or c.clause_id
        for c in clauses
        if re.search(r"penalt|default|interest|late fee|liquidated", c.text, re.IGNORECASE)
    ]

    liability_cap = None
    cap_match = re.search(r"liability[^\n]{0,120}not exceed[^\n]{0,180}", combined, re.IGNORECASE)
    if cap_match:
        liability_cap = cap_match.group(0).strip()

    return FinancialTerms(
        payment_terms=payment_terms,
        penalties=penalties[:10],
        liability_cap=liability_cap,
        indemnification_cap=None,
        liquidated_damages=None,
        revenue_share=None,
        equity_terms=None,
    )


def _build_financial_terms(clauses: list[Clause]) -> FinancialTerms:
    """Build financial terms using LLM extraction with regex fallback."""
    contract_text = "\n\n".join(f"{clause.heading or clause.clause_id}\n{clause.text}" for clause in clauses)
    prompt = PASS_4_FINANCIAL_LLM.format(contract_text=contract_text)

    try:
        parsed = call_llm(
            SYSTEM_PROMPT,
            prompt,
            json_mode=True,
            max_tokens=PASS_TOKEN_LIMITS["pass_4_financial"],
        )
    except RuntimeError:
        return _build_financial_terms_fallback(clauses)

    if not isinstance(parsed, dict):
        return _build_financial_terms_fallback(clauses)

    financial_raw = parsed.get("financial_terms") or {}
    if not isinstance(financial_raw, dict):
        return _build_financial_terms_fallback(clauses)

    payment_raw = financial_raw.get("payment_terms") or {}
    if not isinstance(payment_raw, dict):
        payment_raw = {}

    total_value = payment_raw.get("total_contract_value")
    if total_value and not re.search(r"(?:\$|USD\s?)\s?[\d,]+", str(total_value), flags=re.IGNORECASE):
        total_value = None

    penalties_raw = financial_raw.get("penalties") or []
    penalties = [
        str(item).strip()
        for item in penalties_raw
        if str(item).strip() and not re.match(r"^(?:\d+\.|Section\s+\d)", str(item).strip(), flags=re.IGNORECASE)
    ]

    return FinancialTerms(
        payment_terms=PaymentTerms(
            currency=payment_raw.get("currency"),
            total_contract_value=total_value,
            payment_schedule=payment_raw.get("payment_schedule"),
            amount_per_period=payment_raw.get("amount_per_period"),
            due_days=payment_raw.get("due_days") if isinstance(payment_raw.get("due_days"), int) else None,
            payment_method=payment_raw.get("payment_method"),
            advance_payment=payment_raw.get("advance_payment"),
            late_payment_interest=payment_raw.get("late_payment_interest"),
            invoice_period=payment_raw.get("invoice_period"),
        ),
        penalties=penalties[:10],
        liability_cap=financial_raw.get("liability_cap"),
        indemnification_cap=financial_raw.get("indemnification_cap"),
        liquidated_damages=financial_raw.get("liquidated_damages"),
        revenue_share=financial_raw.get("revenue_share"),
        equity_terms=financial_raw.get("equity_terms"),
    )


def _extract_pass5_intelligence(contract_text: str, metadata: DocumentMetadata, document_profile: DocumentProfile, parties: PartiesSection, clauses: list[Clause], obligations: list[Obligation], rights: list[Right], timelines: list[TimelineEvent]) -> dict[str, Any]:
    tracer = get_tracer()
    doc_type = metadata.document_type.value if metadata.document_type else "Other"
    jurisdiction = metadata.jurisdiction or metadata.governing_law or "General"
    identified_risks = sorted({c.type for c in clauses if c.risk_level in {RiskLevel.HIGH, RiskLevel.CRITICAL}})

    rag_context = get_full_pass5_context(
        contract_text=contract_text,
        document_type=doc_type,
        jurisdiction=jurisdiction,
        identified_risks=identified_risks,
    )

    compact_clauses = [
        {
            "clause_id": c.clause_id,
            "heading": c.heading,
            "type": c.type,
            "risk_level": c.risk_level.value,
            "risk_score": c.risk_score,
            "text": c.text[:280],
        }
        for c in clauses[:40]
    ]

    common_block = (
        "DOCUMENT INTELLIGENCE INPUT\n"
        + f"document_type: {doc_type}\n"
        + f"jurisdiction: {jurisdiction}\n"
        + "document_profile: "
        + json.dumps(document_profile.model_dump(), ensure_ascii=True)
        + "\n"
        + "parties: "
        + json.dumps([{"name": p.name, "role": p.role} for p in parties.parties], ensure_ascii=True)
        + "\n"
        + "clauses: "
        + json.dumps(compact_clauses, ensure_ascii=True)
        + "\n"
        + "obligations: "
        + json.dumps([{"party": o.party, "action": o.action, "clause_id": o.clause_id} for o in obligations[:30]], ensure_ascii=True)
        + "\n"
        + "rights: "
        + json.dumps([{"party": r.party, "right": r.right, "clause_id": r.clause_id} for r in rights[:30]], ensure_ascii=True)
        + "\n"
        + "timelines: "
        + json.dumps([{"event": t.event, "timeframe": t.timeframe, "clause_id": t.clause_id} for t in timelines[:30]], ensure_ascii=True)
    )
    if rag_context:
        common_block += "\n\nKB CONTEXT:\n" + rag_context[:5000]

    async def _run_task(prompt: str, token_key: str) -> dict[str, Any] | Exception:
        try:
            return await _call_llm_async_json(
                SYSTEM_PROMPT,
                prompt,
                max_tokens=PASS_TOKEN_LIMITS[token_key],
            )
        except (RuntimeError, json.JSONDecodeError, ValueError) as exc:
            return exc

    async def _run_all() -> tuple[Any, Any, Any, Any]:
        tracer.trace(
            stage="Stage 3",
            event_type="parallel_dispatch",
            description="Dispatching pass-5 tasks in parallel",
            details={"tasks": ["risks", "missing_deps", "negotiation", "summary"]},
        )
        risks_task = _run_task(PASS_5_RISKS.format(common_block=common_block), "pass_5_risks")
        missing_task = _run_task(PASS_5_MISSING_DEPS.format(common_block=common_block), "pass_5_missing_deps")
        negotiation_task = _run_task(PASS_5_NEGOTIATION.format(common_block=common_block), "pass_5_negotiation")
        summary_task = _run_task(PASS_5_SUMMARY.format(common_block=common_block), "pass_5_summary")
        return await asyncio.gather(
            risks_task,
            missing_task,
            negotiation_task,
            summary_task,
            return_exceptions=True,
        )

    risks_part, missing_part, negotiation_part, summary_part = asyncio.run(_run_all())

    def _safe_dict(value: Any, section: str) -> dict[str, Any]:
        if isinstance(value, Exception):
            tracer.trace_error(
                stage="Stage 3",
                error_message=str(value),
                error_type="Pass5TaskError",
                context={"section": section},
            )
            return {}
        if isinstance(value, dict):
            return value
        tracer.trace_error(
            stage="Stage 3",
            error_message=f"Unexpected pass-5 output type: {type(value).__name__}",
            error_type="Pass5TaskTypeError",
            context={"section": section},
        )
        return {}

    risks_part = _safe_dict(risks_part, "risks")
    missing_part = _safe_dict(missing_part, "missing")
    negotiation_part = _safe_dict(negotiation_part, "negotiation")
    summary_part = _safe_dict(summary_part, "summary")

    intelligence = {
        "risks": risks_part.get("risks", []),
        "missing_clauses": missing_part.get("missing_clauses", []),
        "clause_dependencies": missing_part.get("clause_dependencies", []),
        "negotiation_points": negotiation_part.get("negotiation_points", []),
        "compliance_flags": negotiation_part.get("compliance_flags", []),
        "summary": summary_part.get("summary", {}),
    }

    def _normalize_label(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _apply_heuristic_fill() -> None:
        clause_type_labels = {_normalize_label(c.type) for c in clauses if c.type}

        if not intelligence.get("risks"):
            candidate_clauses = sorted(clauses, key=lambda c: c.risk_score, reverse=True)
            for clause in candidate_clauses:
                if clause.risk_score < 35 and clause.risk_level not in {RiskLevel.HIGH, RiskLevel.CRITICAL}:
                    continue
                intelligence["risks"].append(
                    {
                        "clause_id": clause.clause_id,
                        "risk_type": clause.type or "Ambiguous Language",
                        "severity": clause.risk_level.value,
                        "reason": clause.risk_justification or f"Potential risk in clause {clause.clause_id}.",
                        "impacted_party": clause.affected_party,
                        "risk_sentence": clause.text[:220],
                        "suggestion": f"Review and negotiate clause {clause.clause_id} ({clause.heading or clause.type}).",
                    }
                )
                if len(intelligence["risks"]) >= 3:
                    break
            if not intelligence.get("risks") and clauses:
                clause = clauses[0]
                intelligence["risks"] = [
                    {
                        "clause_id": clause.clause_id,
                        "risk_type": clause.type or "Ambiguous Language",
                        "severity": clause.risk_level.value,
                        "reason": clause.risk_justification or "Potential legal ambiguity detected.",
                        "impacted_party": clause.affected_party,
                        "risk_sentence": clause.text[:220],
                        "suggestion": f"Clarify language in clause {clause.clause_id}.",
                    }
                ]

        if not intelligence.get("missing_clauses"):
            required = _get_required_clauses_for_document(document_profile.model_dump())
            missing = [label for label in required if _normalize_label(label) not in clause_type_labels]
            for label in missing[:3]:
                intelligence["missing_clauses"].append(
                    {
                        "clause_type": label,
                        "importance": "MEDIUM",
                        "reason_needed": f"Expected for {doc_type} agreements but not clearly present.",
                        "suggested_language": None,
                    }
                )
            if not intelligence.get("missing_clauses"):
                intelligence["missing_clauses"] = [
                    {
                        "clause_type": "Operational Clarification",
                        "importance": "LOW",
                        "reason_needed": "Add clarifying operational language for enforceability.",
                        "suggested_language": None,
                    }
                ]

        if not intelligence.get("negotiation_points"):
            for risk in intelligence.get("risks", [])[:3]:
                intelligence["negotiation_points"].append(
                    {
                        "issue": f"{risk.get('risk_type', 'Risk')}: {risk.get('reason', 'Potential contractual risk.')}",
                        "clause_id": risk.get("clause_id"),
                        "favorable_to": None,
                        "disadvantaged_party": risk.get("impacted_party"),
                        "leverage": risk.get("reason", "Balance allocation of risk."),
                        "suggested_counter": risk.get("suggestion", "Propose balanced alternative language."),
                    }
                )

        if not intelligence.get("summary"):
            intelligence["summary"] = {
                "executive_summary": f"{doc_type} analysis generated from {len(clauses)} extracted clauses.",
                "overall_risk_score": int(sum(c.risk_score for c in clauses) / max(1, len(clauses))),
                "risk_distribution": {
                    "LOW": sum(1 for c in clauses if c.risk_level == RiskLevel.LOW),
                    "MEDIUM": sum(1 for c in clauses if c.risk_level == RiskLevel.MEDIUM),
                    "HIGH": sum(1 for c in clauses if c.risk_level == RiskLevel.HIGH),
                    "CRITICAL": sum(1 for c in clauses if c.risk_level == RiskLevel.CRITICAL),
                },
                "recommended_actions": [
                    point.get("suggested_counter")
                    for point in intelligence.get("negotiation_points", [])
                    if isinstance(point, dict) and point.get("suggested_counter")
                ][:5],
            }

    # Retry once if critical pass-5 outputs are empty.
    critical_keys = ["risks", "missing_clauses", "negotiation_points"]
    if any(not intelligence.get(key) for key in critical_keys):
        retry_prompt = (
            "Return JSON with keys risks, missing_clauses, negotiation_points."
            " Each key must contain at least one item, fully grounded in provided clauses.\n\n"
            + common_block
        )
        try:
            retry = call_llm(
                SYSTEM_PROMPT,
                retry_prompt,
                json_mode=True,
                max_tokens=PASS_TOKEN_LIMITS["pass_5_missing_deps"],
            )
            for key in critical_keys:
                if not intelligence.get(key):
                    intelligence[key] = retry.get(key, [])
        except RuntimeError as exc:
            tracer.trace_error(
                stage="Stage 3",
                error_message=str(exc),
                error_type="Pass5RetryError",
                context={"action": "heuristic_fill"},
            )

    if any(not intelligence.get(key) for key in critical_keys):
        _apply_heuristic_fill()

    return intelligence


def _materialize_intelligence(intelligence: dict[str, Any], clauses: list[Clause], document_profile: DocumentProfile) -> tuple[list[RiskItem], list[MissingClause], list[ClauseDependency], list[NegotiationPoint], list[ComplianceFlag], DocumentSummary]:
    clause_by_id = {c.clause_id: c for c in clauses}

    def _normalized(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _normalize_risk_type(value: Any, fallback_text: str = "") -> RiskType:
        raw = str(value or "").strip().lower()
        mapping = {
            "unlimited liability": RiskType.UNLIMITED_LIABILITY,
            "liability": RiskType.UNLIMITED_LIABILITY,
            "one-sided termination": RiskType.ONE_SIDED_TERMINATION,
            "termination": RiskType.ONE_SIDED_TERMINATION,
            "broad ip assignment": RiskType.BROAD_IP_ASSIGNMENT,
            "ip assignment": RiskType.BROAD_IP_ASSIGNMENT,
            "auto renewal trap": RiskType.AUTO_RENEWAL,
            "auto renewal": RiskType.AUTO_RENEWAL,
            "penalty clause": RiskType.PENALTY_CLAUSE,
            "data privacy risk": RiskType.DATA_PRIVACY,
            "privacy": RiskType.DATA_PRIVACY,
            "jurisdiction risk": RiskType.JURISDICTION_RISK,
            "ambiguous language": RiskType.AMBIGUOUS_LANGUAGE,
            "missing standard clause": RiskType.MISSING_CLAUSE,
            "broad indemnification": RiskType.INDEMNIFICATION,
            "indemnification": RiskType.INDEMNIFICATION,
            "non-compete risk": RiskType.NON_COMPETE,
            "payment risk": RiskType.PAYMENT_RISK,
            "force majeure absent": RiskType.FORCE_MAJEURE_ABSENT,
        }
        if raw in mapping:
            return mapping[raw]

        text = fallback_text.lower()
        if "liability" in text:
            return RiskType.UNLIMITED_LIABILITY
        if "termination" in text:
            return RiskType.ONE_SIDED_TERMINATION
        if "payment" in text or "fee" in text:
            return RiskType.PAYMENT_RISK
        if "indemn" in text:
            return RiskType.INDEMNIFICATION
        if "jurisdiction" in text or "governing law" in text:
            return RiskType.JURISDICTION_RISK
        return RiskType.AMBIGUOUS_LANGUAGE

    risks: list[RiskItem] = []
    for raw in intelligence.get("risks", []):
        if not isinstance(raw, dict):
            continue
        clause_id = str(raw.get("clause_id") or "") or None
        clause = clause_by_id.get(clause_id or "")
        risk_sentence = str(raw.get("risk_sentence") or (clause.text[:220] if clause else "")).strip() or None
        reason = str(raw.get("reason") or raw.get("risk_reason") or "").strip()
        if not reason and clause is not None:
            reason = clause.risk_justification or f"Risk identified in clause {clause.clause_id}."
        suggestion = str(raw.get("suggestion") or raw.get("recommendation") or "").strip()
        if not suggestion and clause is not None:
            suggestion = f"Review and negotiate clause {clause.clause_id}."
        if not reason or not suggestion:
            continue

        risks.append(
            RiskItem(
                clause_id=clause_id,
                risk_type=_normalize_risk_type(raw.get("risk_type"), f"{reason} {risk_sentence or ''}"),
                severity=_normalize_risk_level(raw.get("severity")),
                reason=reason,
                impacted_party=raw.get("impacted_party") or (clause.affected_party if clause else None),
                risk_sentence=risk_sentence,
                suggestion=suggestion,
                legal_precedent=raw.get("legal_precedent"),
                risk_labels=_derive_risk_labels(
                    _normalize_risk_type(raw.get("risk_type"), f"{reason} {risk_sentence or ''}"),
                    reason,
                    clause.text if clause else risk_sentence or "",
                ),
                risk_context=str(raw.get("risk_context") or (clause.heading if clause else "") or "").strip() or None,
            )
        )

    missing_clauses: list[MissingClause] = []
    for raw in intelligence.get("missing_clauses", []):
        if isinstance(raw, str):
            clause_type_text = raw.strip()
            if clause_type_text:
                missing_clauses.append(
                    MissingClause(
                        clause_type=clause_type_text,
                        importance=RiskLevel.MEDIUM,
                        reason_needed="Expected clause not clearly found in the analyzed document.",
                        suggested_language=None,
                    )
                )
            continue
        if not isinstance(raw, dict):
            continue
        clause_type = str(raw.get("clause_type") or raw.get("name") or raw.get("clause") or "").strip()
        if not clause_type:
            continue
        importance = _normalize_risk_level(raw.get("importance") or raw.get("severity") or "MEDIUM")
        reason_needed = str(raw.get("reason_needed") or raw.get("reason") or raw.get("description") or "").strip()
        if not reason_needed:
            reason_needed = f"This clause helps manage legal and operational risk for the agreement."
        suggested_language = str(raw.get("suggested_language") or raw.get("suggestion") or "").strip() or None
        missing_clauses.append(
            MissingClause(
                clause_type=clause_type,
                importance=importance,
                reason_needed=reason_needed,
                suggested_language=suggested_language,
            )
        )

    observed_text = "\n".join([f"{c.type} {c.heading} {c.text[:200]}" for c in clauses]).lower()
    observed_key_text = _normalized(observed_text)
    profile_dict = document_profile.model_dump()
    profile_required = _get_required_clauses_for_document(profile_dict)
    profile_high_risk = _coerce_str_list(document_profile.high_risk_clauses)
    profile_commonly_missing = _coerce_str_list(document_profile.extensions.get("commonly_missing"))
    subtype_lower = str(document_profile.subtype or "").lower()
    is_derivative_doc = any(
        token in subtype_lower
        for token in ("amendment", "addendum", "exhibit", "schedule", "supplement", "rider", "side letter")
    )

    if is_derivative_doc:
        required_norm = {_normalized(item) for item in profile_required if item}

        def _is_allowed_derivative_missing(clause_name: str) -> bool:
            normalized = _normalized(clause_name)
            return any(req in normalized or normalized in req for req in required_norm)

        missing_clauses = [
            item
            for item in missing_clauses
            if item.clause_type == "_note" or _is_allowed_derivative_missing(item.clause_type)
        ]

    existing_missing = {_normalized(item.clause_type) for item in missing_clauses if item.clause_type}
    candidate_clauses = profile_required if is_derivative_doc else (profile_required + profile_high_risk + profile_commonly_missing)
    seen_candidates: set[str] = set()
    for clause_type in candidate_clauses:
        key = _normalized(clause_type)
        if not key or key in seen_candidates:
            continue
        seen_candidates.add(key)
        if key in observed_key_text or key in existing_missing:
            continue

        importance = RiskLevel.CRITICAL if clause_type in profile_high_risk else RiskLevel.HIGH if clause_type in profile_required else RiskLevel.MEDIUM
        reason_needed = f"This clause is expected for a {document_profile.detected_type.value if document_profile.detected_type else 'this'} agreement and reduces ambiguity, loss allocation, or enforcement risk."
        if clause_type in profile_required:
            reason_needed = f"This clause is part of the required template for {document_profile.detected_type.value if document_profile.detected_type else 'this'} agreements."
        if clause_type in profile_high_risk:
            reason_needed = f"This clause is high-risk when missing because the KB flags it as important for {document_profile.detected_type.value if document_profile.detected_type else 'this'} agreements."

        missing_clauses.append(
            MissingClause(
                clause_type=clause_type,
                importance=importance,
                reason_needed=reason_needed,
                suggested_language=None,
            )
        )

    if not missing_clauses:
        baseline_checks = [
            (
                "Governing Law",
                ["governing law", "jurisdiction", "venue"],
                RiskLevel.MEDIUM,
                "A governing-law/jurisdiction clause clarifies legal forum and reduces dispute ambiguity.",
            ),
            (
                "Liability Limitation",
                ["liability", "limit of liability", "damages cap"],
                RiskLevel.MEDIUM,
                "A liability-limitation clause helps control financial exposure if disputes occur.",
            ),
        ]
        for clause_type, markers, importance, reason_needed in baseline_checks:
            if not any(marker in observed_text for marker in markers):
                missing_clauses.append(
                    MissingClause(
                        clause_type=clause_type,
                        importance=importance,
                        reason_needed=reason_needed,
                        suggested_language=None,
                    )
                )

    if is_derivative_doc:
        missing_clauses.append(
            MissingClause(
                clause_type="_note",
                importance=RiskLevel.LOW,
                reason_needed=(
                    "This is an Amendment document. Missing clause analysis applies only to "
                    "amendment-specific requirements. Parent agreement clauses are incorporated "
                    "by reference."
                ),
                suggested_language=None,
            )
        )

    dependencies: list[ClauseDependency] = []
    for raw in intelligence.get("clause_dependencies", []):
        if not isinstance(raw, dict):
            continue
        c1 = str(raw.get("source_clause") or raw.get("clause_id_1") or "").strip()
        c2 = str(raw.get("target_clause") or raw.get("clause_id_2") or "").strip()
        if not c1 or not c2:
            continue
        dependencies.append(
            ClauseDependency(
                source_clause=c1,
                target_clause=c2,
                clause_id_1=c1,
                clause_id_2=c2,
                relation_type=str(raw.get("relation_type") or "linked_to"),
                description=str(raw.get("description") or f"Clause {c1} is related to clause {c2}."),
                cross_document_reference=str(raw.get("cross_document_reference") or raw.get("cross_ref") or "").strip() or None,
            )
        )

    if not dependencies:
        seen_pairs: set[tuple[str, str]] = set()
        for clause in clauses:
            if clause.cross_references:
                for ref in clause.cross_references:
                    target = re.sub(r"[^0-9A-Za-z]+", "", ref).strip()
                    if not target or target == clause.clause_id:
                        continue
                    pair = (clause.clause_id, target)
                    if pair in seen_pairs:
                        continue
                    seen_pairs.add(pair)
                    dependencies.append(
                        ClauseDependency(
                            source_clause=clause.clause_id,
                            target_clause=target,
                            clause_id_1=clause.clause_id,
                            clause_id_2=target,
                            relation_type="linked_to",
                            description=f"Clause {clause.clause_id} cross-references clause {target}.",
                            cross_document_reference=ref,
                        )
                    )

    negotiation_points: list[NegotiationPoint] = []
    for raw in intelligence.get("negotiation_points", []):
        if not isinstance(raw, dict):
            continue
        issue = str(raw.get("issue") or raw.get("concern") or "").strip()
        leverage = str(raw.get("leverage") or raw.get("reason") or "").strip()
        counter = str(raw.get("suggested_counter") or raw.get("counter_proposal") or raw.get("recommendation") or "").strip()
        if not issue or not leverage or not counter:
            continue
        negotiation_points.append(
            NegotiationPoint(
                issue=issue,
                clause_id=raw.get("clause_id"),
                favorable_to=raw.get("favorable_to"),
                disadvantaged_party=raw.get("disadvantaged_party"),
                leverage=leverage,
                suggested_counter=counter,
            )
        )

    compliance_flags: list[ComplianceFlag] = []
    for raw in intelligence.get("compliance_flags", []):
        if not isinstance(raw, dict):
            continue
        regulation = str(raw.get("regulation") or raw.get("framework") or "").strip()
        issue = str(raw.get("issue") or raw.get("risk") or "").strip()
        recommendation = str(raw.get("recommendation") or raw.get("suggestion") or "").strip()
        if not regulation or not issue or not recommendation:
            continue
        compliance_flags.append(
            ComplianceFlag(
                regulation=regulation,
                clause_id=raw.get("clause_id"),
                issue=issue,
                severity=_normalize_risk_level(raw.get("severity") or "MEDIUM"),
                recommendation=recommendation,
            )
        )

    if not negotiation_points:
        for risk in risks[:5]:
            issue = f"{risk.risk_type.value}: {risk.reason}"
            leverage = risk.reason
            counter = risk.suggestion
            if issue and leverage and counter:
                negotiation_points.append(
                    NegotiationPoint(
                        issue=issue,
                        clause_id=risk.clause_id,
                        favorable_to=None,
                        disadvantaged_party=risk.impacted_party,
                        leverage=leverage,
                        suggested_counter=counter,
                    )
                )

    summary_raw = intelligence.get("summary", {}) if isinstance(intelligence.get("summary"), dict) else {}
    if not summary_raw.get("risk_distribution"):
        risk_distribution = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for clause in clauses:
            risk_distribution[clause.risk_level.value] += 1
        summary_raw["risk_distribution"] = risk_distribution

    recommended_actions = _coerce_str_list(summary_raw.get("recommended_actions"))
    if not recommended_actions:
        recommended_actions = [point.suggested_counter for point in negotiation_points if point.suggested_counter][:5]
    if not recommended_actions:
        recommended_actions = [risk.suggestion for risk in risks if risk.suggestion][:5]

    computed_overall = int(summary_raw.get("overall_risk_score") or 0)
    if computed_overall <= 0:
        computed_overall = int(sum(c.risk_score for c in clauses) / max(1, len(clauses)))

    summary = DocumentSummary(
        executive_summary=str(summary_raw.get("executive_summary") or f"The document contains {len(clauses)} clauses."),
        key_points=_coerce_str_list(summary_raw.get("key_points")),
        red_flags=_coerce_str_list(summary_raw.get("red_flags")),
        favorable_clauses=_coerce_str_list(summary_raw.get("favorable_clauses")),
        unusual_clauses=_coerce_str_list(summary_raw.get("unusual_clauses")),
        favorable_to=summary_raw.get("favorable_to"),
        overall_risk_score=max(0, min(100, computed_overall)),
        risk_distribution=summary_raw.get("risk_distribution") or {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
        recommended_actions=recommended_actions,
    )

    return risks, missing_clauses, dependencies, negotiation_points, compliance_flags, summary


def _enforce_completeness(document: LegalDocumentAnalysis) -> None:
    required_sections = {
        "clauses": document.clauses,
        "risks": document.risks,
        "obligations": document.obligations,
        "rights": document.rights,
        "timelines": document.timelines,
        "missing_clauses": document.missing_clauses,
        "negotiation_points": document.negotiation_points,
    }

    empty = [name for name, value in required_sections.items() if not value]
    if empty:
        raise RuntimeError(f"Pipeline incomplete: empty required sections: {', '.join(empty)}")

    if not document.summary.recommended_actions:
        raise RuntimeError("Pipeline incomplete: summary.recommended_actions is empty")


def _filter_missing_clauses_for_derivative_docs(
    missing_clauses: list[MissingClause],
    document_profile: DocumentProfile,
) -> list[MissingClause]:
    """Restrict missing-clause output for derivative docs to amendment requirements."""
    subtype_lower = str(document_profile.subtype or "").lower()
    is_derivative_doc = any(
        token in subtype_lower
        for token in ("amendment", "addendum", "exhibit", "schedule", "supplement", "rider", "side letter")
    )
    if not is_derivative_doc:
        return missing_clauses

    required_norm = {
        re.sub(r"[^a-z0-9]+", " ", item.lower()).strip()
        for item in _get_required_clauses_for_document(document_profile.model_dump())
        if item
    }

    def _normalized(text: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()

    filtered = []
    for item in missing_clauses:
        if item.clause_type == "_note":
            filtered.append(item)
            continue
        normalized = _normalized(item.clause_type)
        if any(req in normalized or normalized in req for req in required_norm):
            filtered.append(item)

    has_note = any(item.clause_type == "_note" for item in filtered)
    if not has_note:
        filtered.append(
            MissingClause(
                clause_type="_note",
                importance=RiskLevel.LOW,
                reason_needed=(
                    "This is an Amendment document. Missing clause analysis applies only to "
                    "amendment-specific requirements. Parent agreement clauses are incorporated "
                    "by reference."
                ),
                suggested_language=None,
            )
        )

    return filtered


def run_full_extraction(contract_text: str, segmented_clauses: list[tuple[str, str]]) -> LegalDocumentAnalysis:
    """Run the complete generalized extraction pipeline."""
    try:
        clear_kb_cache()
        print("[Init] Initializing knowledge base...")
        initialize_kb()

        print("\n[PASS 1] Extracting metadata and parties...")
        try:
            metadata, parties = extract_metadata_and_parties(contract_text)
        except (RuntimeError, ValueError, TypeError, json.JSONDecodeError, KeyError) as exc:
            validate_metadata_extraction(stage="metadata_extraction", error=exc, contract_text=contract_text)

        print("[PASS 2] Extracting clauses with KB grounding...")
        clauses = extract_clauses(segmented_clauses, metadata, parties)
        clauses = _dedupe_clauses(clauses)
        if not clauses:
            raise RuntimeError("No clauses extracted")

        print("[PASS 3] Extracting obligations, rights, and timelines...")
        obligations, rights, timelines = _extract_obligations_rights_timelines(contract_text, parties, clauses)
        obligations, rights, timelines = _normalize_clause_references(obligations, rights, timelines, clauses)

        print("[PASS 4] Aggregating financial terms...")
        financial_terms = _build_financial_terms(clauses)

        document_profile = _build_document_profile(metadata, clauses, contract_text)

        print("[PASS 5] Building intelligence layers (risks, dependencies, missing clauses, negotiation, compliance, summary)...")
        intelligence = _extract_pass5_intelligence(
            contract_text=contract_text,
            metadata=metadata,
            document_profile=document_profile,
            parties=parties,
            clauses=clauses,
            obligations=obligations,
            rights=rights,
            timelines=timelines,
        )
        risks, missing_clauses, clause_dependencies, negotiation_points, compliance_flags, summary = _materialize_intelligence(
            intelligence,
            clauses,
            document_profile,
        )
        missing_clauses = _filter_missing_clauses_for_derivative_docs(missing_clauses, document_profile)

        dependency_graph = _build_clause_dependency_graph(clauses, clause_dependencies)
        linked_documents = _build_linked_documents(metadata, document_profile, clauses)

        print("[PASS 6] Finalizing output...")
        document = LegalDocumentAnalysis(
            document_id=f"doc_{datetime.now().timestamp()}",
            filename="contract.pdf",
            analyzed_at=datetime.now().isoformat(),
            metadata=metadata,
            document_profile=document_profile,
            parties=parties,
            financial_terms=financial_terms,
            linked_documents=linked_documents,
            clauses=clauses,
            risks=risks,
            obligations=obligations,
            rights=rights,
            timelines=timelines,
            clause_dependencies=clause_dependencies,
            missing_clauses=missing_clauses,
            negotiation_points=negotiation_points,
            compliance_flags=compliance_flags,
            dependency_graph=dependency_graph,
            summary=summary,
        )

        _enforce_completeness(document)
        return document

    except (RuntimeError, ValueError, TypeError, json.JSONDecodeError, KeyError) as exc:
        validate_pipeline_stage(
            stage="full_extraction_pipeline",
            error=exc,
            stage_input=contract_text[:1000],
        )
        raise
