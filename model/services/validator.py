from __future__ import annotations

from typing import Any

from models.schema import LegalDocumentAnalysis
import re

INVALID_PARTY_PHRASES = (
    "terms of this",
    "this agreement",
    "this amendment",
    "the agreement",
    "submission to jurisdiction",
    "governing law",
    "jurisdiction and venue",
    "party a",
    "party b",
    "borrower",
    "lender",
    "documents",
    "instrument",
    "amount",
    "state of",
)

GENERIC_OBLIGATIONS = (
    "limit liability",
    "terminate on notice",
)

DERIVATIVE_DOCUMENT_SUBTYPES = frozenset({
    "Amendment",
    "Addendum",
    "First Amendment",
    "Second Amendment",
    "Exhibit",
    "Schedule",
    "Attachment",
    "Appendix",
    "Supplement",
    "Rider",
    "Side Letter",
})

AMENDMENT_REQUIRED_CLAUSES = [
    "Governing Law",
    "Ratification",
]

EXHIBIT_REQUIRED_CLAUSES: list[str] = []


def _get_required_clauses_for_document(document_profile: dict[str, Any]) -> list[str]:
    """Return required-clause targets based on standalone vs derivative subtype.

    Derivative documents intentionally bypass full standalone required-clause checks.
    """
    subtype = str(document_profile.get("subtype") or "").strip()
    subtype_lower = subtype.lower()
    if subtype in DERIVATIVE_DOCUMENT_SUBTYPES or any(
        token in subtype_lower for token in ("amendment", "addendum", "exhibit", "schedule", "supplement", "rider", "side letter")
    ):
        if "exhibit" in subtype_lower or "schedule" in subtype_lower:
            return EXHIBIT_REQUIRED_CLAUSES
        return AMENDMENT_REQUIRED_CLAUSES
    return [str(item) for item in (document_profile.get("required_clauses") or []) if str(item).strip()]


def _is_invalid_party_name(name: str | None) -> bool:
    if not name:
        return True
    cleaned = " ".join(name.replace('"', " ").replace("'", " ").split()).strip(" ,.;:()[]{}")
    lowered = cleaned.lower()
    if len(lowered) <= 3:
        return True
    words = [w for w in lowered.split() if w]
    if not words:
        return True

    if len(words) == 1:
        if words[0] in {
            "state",
            "security",
            "instruments",
            "instrument",
            "supplement",
            "agreement",
            "section",
            "article",
            "party",
            "borrower",
            "lender",
        }:
            return True

    if lowered.startswith("the ") and any(
        token in lowered
        for token in (
            "agreement",
            "commitment",
            "maturity date",
            "section",
            "article",
            "loan documents",
            "security",
        )
    ):
        return True

    return any(token in lowered for token in INVALID_PARTY_PHRASES)


def is_valid_party_name(name: str | None) -> bool:
    return not _is_invalid_party_name(name)


def validate_clause_output(clause_json: dict[str, Any]) -> bool:
    required = {"clause_type", "obligations", "rights", "risk_level", "risk_type", "text"}
    if not required.issubset(clause_json.keys()):
        return False

    text_low = str(clause_json.get("text", "")).lower()

    affected_party = clause_json.get("affected_party")
    if affected_party and _is_invalid_party_name(str(affected_party)):
        return False

    obligations = clause_json.get("obligations", []) or []
    if not isinstance(obligations, list):
        return False

    for item in obligations:
        if not isinstance(item, str):
            return False
        low = item.lower().strip()
        if low in GENERIC_OBLIGATIONS and low not in text_low:
            return False
        if low and low not in text_low and not any(v in low for v in ["shall", "must", "required"]):
            return False

    rights = clause_json.get("rights", []) or []
    if not isinstance(rights, list):
        return False

    return True


def validate_analysis_output(output: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    parties = (((output.get("parties") or {}).get("parties")) or [])
    for party in parties:
        name = str(party.get("name", ""))
        if _is_invalid_party_name(name):
            errors.append(f"Invalid party name detected: {name}")

    clauses = output.get("clauses", []) or []
    if not isinstance(clauses, list) or not clauses:
        errors.append("No clauses present in final output")
        return errors

    profile = output.get("document_profile") or {}
    metadata = output.get("metadata") or {}
    document_type = str((metadata.get("document_type") if isinstance(metadata, dict) else "") or "").strip().lower()
    subtype_text = str((profile.get("subtype") if isinstance(profile, dict) else "") or "")
    title_text = str((metadata.get("title") if isinstance(metadata, dict) else "") or "")
    required_clauses = _get_required_clauses_for_document(profile if isinstance(profile, dict) else {})
    missing_clause_types = {
        str(item.get("clause_type") or "").strip().lower()
        for item in (output.get("missing_clauses", []) or [])
        if isinstance(item, dict)
    }

    def _normalize(value: str) -> str:
        return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()

    def _required_clause_variants(value: str) -> list[str]:
        normalized = _normalize(value)
        if not normalized:
            return []

        variants = {normalized}
        for separator in ("/", "&", ",", ";"):
            if separator in value:
                for part in value.split(separator):
                    part_normalized = _normalize(part)
                    if part_normalized:
                        variants.add(part_normalized)
        if " and " in normalized:
            variants.update(piece for piece in normalized.split(" and ") if piece)
        return sorted(variants, key=len, reverse=True)

    clause_text_blobs = [
        _normalize(" ".join(
            str(clause.get(key, "")) for key in ("type", "heading", "text")
        ))
        for clause in clauses
        if isinstance(clause, dict)
    ]

    policy_like_markers = (
        "policy",
        "guideline",
        "handbook",
        "code of conduct",
        "circular",
        "notice",
        "regulation",
        "manual",
    )
    profile_text = f"{subtype_text} {title_text}".lower()
    is_policy_like = any(marker in profile_text for marker in policy_like_markers)

    enforce_required_clause_coverage = document_type not in {"", "other"} and not is_policy_like
    if enforce_required_clause_coverage:
        for required in required_clauses:
            variants = _required_clause_variants(str(required))
            if not variants:
                continue
            if any(any(variant in blob for variant in variants) for blob in clause_text_blobs):
                continue
            if not any(variant in missing_clause_types for variant in variants):
                errors.append(f"Missing required clause coverage for: {required}")

    for clause in clauses:
        if "clause_id" not in clause:
            errors.append("Clause missing clause_id")
        if "text" not in clause:
            errors.append("Clause missing text")
        if "type" not in clause:
            errors.append("Clause missing type")

    return errors


def validate_and_clean(raw: dict[str, Any]) -> LegalDocumentAnalysis:
    if not raw.get("summary"):
        raw["summary"] = {
            "executive_summary": "Analysis could not generate summary.",
            "key_points": [],
            "red_flags": [],
            "favorable_clauses": [],
            "unusual_clauses": [],
            "favorable_to": None,
            "overall_risk_score": 0,
            "risk_distribution": {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0},
            "recommended_actions": [],
        }

    clauses = raw.get("clauses", []) or []
    if clauses and not raw["summary"].get("risk_distribution", {}).get("LOW"):
        dist = {"LOW": 0, "MEDIUM": 0, "HIGH": 0, "CRITICAL": 0}
        for clause in clauses:
            level = clause.get("risk_level", "LOW")
            if level in dist:
                dist[level] += 1
        raw["summary"]["risk_distribution"] = dist

    required_non_empty = [
        "clauses",
        "risks",
        "obligations",
        "rights",
        "timelines",
        "negotiation_points",
    ]
    for field in required_non_empty:
        value = raw.get(field, []) or []
        if not isinstance(value, list) or len(value) == 0:
            raise ValueError(f"Validation failed: {field} is empty")

    summary = raw.get("summary") or {}
    if not summary.get("recommended_actions"):
        raise ValueError("Validation failed: summary.recommended_actions is empty")

    dependency_graph = raw.get("dependency_graph") or {}
    if dependency_graph and not isinstance(dependency_graph, dict):
        raise ValueError("Validation failed: dependency_graph must be an object")

    issues = validate_analysis_output(raw)
    if issues:
        raise ValueError("Validation failed: " + "; ".join(issues[:5]))

    try:
        return LegalDocumentAnalysis(**raw)
    except Exception as e:
        raise ValueError(f"Schema validation failed: {str(e)}")
