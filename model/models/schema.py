# app/models/schema.py
from pydantic import BaseModel, Field
from typing import Any, Optional, List
from enum import Enum

# ─── ENUMS (deterministic, prevents hallucination) ────────────────────────────

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ClauseCategory(str, Enum):
    OBLIGATION    = "Obligation"
    RIGHT         = "Right"
    PROHIBITION   = "Prohibition"
    CONDITION     = "Condition"
    DEFINITION    = "Definition"
    REMEDY        = "Remedy"
    REPRESENTATION = "Representation"

class DocumentType(str, Enum):
    NDA           = "NDA"
    MSA           = "MSA"          # Master Service Agreement
    SLA           = "SLA"          # Service Level Agreement
    EMPLOYMENT    = "Employment"
    LEASE         = "Lease"
    LOAN          = "Loan"
    PARTNERSHIP   = "Partnership"
    VENDOR        = "Vendor"
    CONSULTING    = "Consulting"
    IP_ASSIGNMENT = "IP Assignment"
    OTHER         = "Other"

class RiskType(str, Enum):
    UNLIMITED_LIABILITY    = "Unlimited Liability"
    ONE_SIDED_TERMINATION  = "One-sided Termination"
    BROAD_IP_ASSIGNMENT    = "Broad IP Assignment"
    AUTO_RENEWAL           = "Auto Renewal Trap"
    PENALTY_CLAUSE         = "Penalty Clause"
    DATA_PRIVACY           = "Data Privacy Risk"
    JURISDICTION_RISK      = "Jurisdiction Risk"
    AMBIGUOUS_LANGUAGE     = "Ambiguous Language"
    MISSING_CLAUSE         = "Missing Standard Clause"
    INDEMNIFICATION        = "Broad Indemnification"
    NON_COMPETE            = "Non-Compete Risk"
    PAYMENT_RISK           = "Payment Risk"
    FORCE_MAJEURE_ABSENT   = "Force Majeure Absent"


# ─── A. DOCUMENT METADATA ─────────────────────────────────────────────────────

class DocumentMetadata(BaseModel):
    document_type: Optional[DocumentType] = None
    document_subtype: Optional[str] = None        # e.g. "Bilateral NDA"
    title: Optional[str] = None
    effective_date: Optional[str] = None          # ISO 8601 preferred
    execution_date: Optional[str] = None          # Date of signing
    expiration_date: Optional[str] = None
    auto_renewal: Optional[bool] = None
    renewal_notice_period: Optional[str] = None   # "30 days before expiry"
    jurisdiction: Optional[str] = None
    governing_law: Optional[str] = None
    venue: Optional[str] = None                   # Dispute resolution forum
    language: str = "English"
    amendment_number: Optional[str] = None        # "Amendment 2"
    parent_agreement_ref: Optional[str] = None    # Links to MSA, etc.
    confidentiality_classification: Optional[str] = None


class DocumentProfile(BaseModel):
    detected_type: Optional[DocumentType] = None
    subtype: Optional[str] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: List[str] = Field(default_factory=list)
    required_clauses: List[str] = Field(default_factory=list)
    recommended_clauses: List[str] = Field(default_factory=list)
    high_risk_clauses: List[str] = Field(default_factory=list)
    extensions: dict[str, Any] = Field(default_factory=dict)


# ─── B. PARTIES & ROLES ───────────────────────────────────────────────────────

class Party(BaseModel):
    name: str
    legal_entity_type: Optional[str] = None       # LLC, Corporation, Individual
    role: str                                      # "Disclosing Party", "Client"
    address: Optional[str] = None
    country: Optional[str] = None
    registration_number: Optional[str] = None     # CIN, EIN, etc.

class Signatory(BaseModel):
    name: str
    company: str
    designation: str
    email: Optional[str] = None
    signing_date: Optional[str] = None
    signing_authority: Optional[str] = None       # "duly authorized representative"

class PartiesSection(BaseModel):
    parties: List[Party] = Field(default_factory=list)
    signatories: List[Signatory] = Field(default_factory=list)
    beneficiaries: List[str] = Field(default_factory=list)                 # Named third-party beneficiaries
    excluded_parties: List[str] = Field(default_factory=list)


# ─── C. FINANCIAL & COMMERCIAL TERMS ─────────────────────────────────────────

class PaymentTerms(BaseModel):
    currency: Optional[str] = None
    total_contract_value: Optional[str] = None
    payment_schedule: Optional[str] = None        # "Monthly", "Milestone-based"
    amount_per_period: Optional[str] = None
    due_days: Optional[int] = None
    payment_method: Optional[str] = None
    advance_payment: Optional[str] = None
    late_payment_interest: Optional[str] = None
    invoice_period: Optional[str] = None

class FinancialTerms(BaseModel):
    payment_terms: Optional[PaymentTerms] = None
    penalties: List[str] = Field(default_factory=list)
    liability_cap: Optional[str] = None           # "$100,000" or "null = unlimited"
    indemnification_cap: Optional[str] = None
    liquidated_damages: Optional[str] = None
    revenue_share: Optional[str] = None
    equity_terms: Optional[str] = None


# ─── D. CLAUSE-LEVEL EXTRACTION ───────────────────────────────────────────────
# This is the CORE of the system — one object per clause

class Clause(BaseModel):
    clause_id: str                                 # "1", "2a", etc.
    section_number: Optional[str] = None          # "Section 5.2"
    heading: Optional[str] = None                 # Original section title
    text: str                                      # Full clause text verbatim
    plain_english: str                             # LLM plain-language translation
    type: str                                      # "Confidentiality", "Termination"
    category: ClauseCategory
    risk_level: RiskLevel
    risk_score: int = Field(ge=0, le=100)          # 0-100 numeric score
    risk_justification: str                        # WHY this risk score was given
    affected_party: Optional[str] = None          # Who bears the risk
    obligations: List[str] = Field(default_factory=list)                    # Action items extracted
    rights: List[str] = Field(default_factory=list)                         # Entitlements extracted
    deadlines: List[str] = Field(default_factory=list)                      # Time-bound elements
    is_unilateral: bool = False                    # Only one party bears burden
    is_mutual: bool = False
    is_standard: bool = True                       # False = unusual / non-standard
    is_ambiguous: bool = False
    ambiguity_reason: Optional[str] = None        # Why it's ambiguous
    tags: List[str] = Field(default_factory=list)                           # ["confidentiality", "IP"]
    cross_references: List[str] = Field(default_factory=list)              # "See Section 8.1"


# ─── E. RISK INTELLIGENCE ─────────────────────────────────────────────────────

class RiskItem(BaseModel):
    clause_id: Optional[str] = None
    risk_type: RiskType
    severity: RiskLevel
    reason: str                                    # Explanation of the risk
    impacted_party: Optional[str] = None
    risk_sentence: Optional[str] = None           # The exact sentence causing risk
    suggestion: str                                # What to do to fix/negotiate it
    legal_precedent: Optional[str] = None         # Brief reference if applicable
    risk_labels: List[str] = Field(default_factory=list)
    risk_context: Optional[str] = None


# ─── F. OBLIGATIONS & RIGHTS ──────────────────────────────────────────────────

class Obligation(BaseModel):
    party: str
    action: str
    clause_id: Optional[str] = None
    deadline: Optional[str] = None
    consequence_of_breach: Optional[str] = None
    is_recurring: bool = False

class Right(BaseModel):
    party: str
    right: str
    clause_id: Optional[str] = None
    conditions: Optional[str] = None             # "only if X fails to..."
    is_exclusive: bool = False


# ─── G. TIMELINE & EVENTS ─────────────────────────────────────────────────────

class TimelineEvent(BaseModel):
    event: str                                    # "Payment due"
    timeframe: str                                # "30 days from invoice"
    trigger: Optional[str] = None                # What starts the clock
    party_responsible: Optional[str] = None
    clause_id: Optional[str] = None
    is_hard_deadline: bool = False


# ─── H. CLAUSE RELATIONSHIPS ──────────────────────────────────────────────────

class ClauseDependency(BaseModel):
    source_clause: Optional[str] = None
    target_clause: Optional[str] = None
    relation_type: str = "linked_to"         # "modifies", "triggers", "conflicts_with", "supersedes"
    description: str
    clause_id_1: Optional[str] = None
    clause_id_2: Optional[str] = None
    cross_document_reference: Optional[str] = None


class LinkedDocument(BaseModel):
    reference_text: str
    relation_type: str
    document_type: Optional[DocumentType] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    notes: Optional[str] = None
    source_clause_id: Optional[str] = None


# ─── I. MISSING CLAUSES ───────────────────────────────────────────────────────

class MissingClause(BaseModel):
    clause_type: str           # "Force Majeure", "Dispute Resolution"
    importance: RiskLevel
    reason_needed: str         # Why this matters for this document type
    suggested_language: Optional[str] = None  # Brief template text


# ─── J. NEGOTIATION INTELLIGENCE ─────────────────────────────────────────────

class NegotiationPoint(BaseModel):
    issue: str                 # "Liability is unlimited for Vendor"
    clause_id: Optional[str] = None
    favorable_to: Optional[str] = None
    disadvantaged_party: Optional[str] = None
    leverage: str              # How to argue for change
    suggested_counter: str     # What language to propose instead


# ─── K. COMPLIANCE FLAGS ──────────────────────────────────────────────────────

class ComplianceFlag(BaseModel):
    regulation: str            # "GDPR", "CCPA", "Indian IT Act"
    clause_id: Optional[str] = None
    issue: str
    severity: RiskLevel
    recommendation: str


# ─── L. SUMMARY / INSIGHTS ────────────────────────────────────────────────────

class DocumentSummary(BaseModel):
    executive_summary: str     # 3-4 sentence plain-English overview
    key_points: List[str] = Field(default_factory=list) # Top 5 most important facts
    red_flags: List[str] = Field(default_factory=list)  # Critical issues that need immediate attention
    favorable_clauses: List[str] = Field(default_factory=list)  # What's good
    unusual_clauses: List[str] = Field(default_factory=list)    # Non-standard terms
    favorable_to: Optional[str] = None  # "Party A", "Neither", "Both"
    overall_risk_score: int = Field(ge=0, le=100)
    risk_distribution: dict = Field(default_factory=dict)   # {"LOW": 5, "MEDIUM": 3, "HIGH": 2}
    recommended_actions: List[str] = Field(default_factory=list)


# ─── MASTER DOCUMENT (Final Output) ──────────────────────────────────────────

class LegalDocumentAnalysis(BaseModel):
    document_id: str
    filename: str
    analyzed_at: str           # ISO timestamp
    metadata: DocumentMetadata
    document_profile: DocumentProfile = Field(default_factory=DocumentProfile)
    parties: PartiesSection
    financial_terms: FinancialTerms
    linked_documents: List[LinkedDocument] = Field(default_factory=list)
    clauses: List[Clause] = Field(default_factory=list)
    risks: List[RiskItem] = Field(default_factory=list)
    obligations: List[Obligation] = Field(default_factory=list)
    rights: List[Right] = Field(default_factory=list)
    timelines: List[TimelineEvent] = Field(default_factory=list)
    clause_dependencies: List[ClauseDependency] = Field(default_factory=list)
    missing_clauses: List[MissingClause] = Field(default_factory=list)
    negotiation_points: List[NegotiationPoint] = Field(default_factory=list)
    compliance_flags: List[ComplianceFlag] = Field(default_factory=list)
    dependency_graph: dict[str, Any] = Field(default_factory=dict)
    summary: DocumentSummary