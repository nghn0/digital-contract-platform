# app/core/prompts.py
# ─────────────────────────────────────────────────────────────────────────────
# DESIGN PRINCIPLE:
# - Each pass extracts ONE category of information
# - Each prompt enforces strict JSON-only output
# - Enums are hardcoded in prompts to prevent hallucination
# - Every prompt ends with: "Return ONLY valid JSON. No commentary."
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert legal contract analyst with 20 years of experience 
in corporate law, risk assessment, and contract negotiation. Your role is to extract 
structured information from legal documents with precision and consistency. 

Rules:
- Return ONLY valid JSON matching the exact schema requested
- Never invent or hallucinate information not present in the text
- Extract ONLY information explicitly present in the provided clause/document text
- You MUST extract ALL clauses from ALL sections of the document, including embedded agreements such as NDAs, annexures, or addendums
- Do NOT ignore sections appearing after the primary agreement body
- Do NOT treat capitalized text alone as evidence of party identity
- A party must be either: (a) a legal entity (e.g., LLC, INC, LTD, BANK, CORPORATION), or (b) a clearly defined contract role (e.g., Borrower, Lender, Bank, Guarantor)
- Do NOT output monetary terms, defined term labels, section headings, or generic uppercase tokens as parties
- Do NOT hallucinate obligations, risks, or clause types
- If unsure, return null for scalar fields and [] for list fields
- Use null for fields you cannot find
- Quote exact text verbatim when extracting clause text
- Be conservative on risk scores: LOW=0-30, MEDIUM=31-60, HIGH=61-85, CRITICAL=86-100"""


# ─── PASS 1: Document Metadata + Parties ─────────────────────────────────────

PASS_1_METADATA_PARTIES = """
Analyze the following legal document and extract document metadata and party information.

CONTRACT TEXT:
{contract_text}

Return a JSON object with EXACTLY this structure (use null for missing fields):
{{
  "metadata": {{
    "document_type": "<one of: NDA|MSA|SLA|Employment|Lease|Loan|Partnership|Vendor|Consulting|IP Assignment|Other>",
    "document_subtype": "<more specific type or null>",
    "title": "<exact title from document or null>",
    "effective_date": "<YYYY-MM-DD or original text>",
    "execution_date": "<date signed>",
    "expiration_date": "<YYYY-MM-DD or original text>",
    "auto_renewal": <true|false|null>,
    "renewal_notice_period": "<e.g. 30 days before expiry>",
    "jurisdiction": "<state/country where enforceable>",
    "governing_law": "<governing law stated in document>",
    "venue": "<dispute forum: court, arbitration, etc.>",
    "language": "English",
    "amendment_number": "<Amendment 1, etc. or null>",
    "parent_agreement_ref": "<references a master agreement?>",
    "confidentiality_classification": "<Confidential/Public/etc.>"
  }},
  "parties": {{
    "parties": [
      {{
        "name": "<full legal name>",
        "legal_entity_type": "<LLC|Corporation|Individual|Partnership|etc.>",
        "role": "<role in this contract e.g. Disclosing Party, Client, Vendor>",
        "address": "<registered address or null>",
        "country": "<country of incorporation>",
        "registration_number": "<CIN/EIN/etc. or null>"
      }}
    ],
    "signatories": [
      {{
        "name": "<full name>",
        "company": "<company name>",
        "designation": "<title/designation>",
        "email": "<email or null>",
        "signing_date": "<date or null>",
        "signing_authority": "<authorized representative wording>"
      }}
    ],
    "beneficiaries": ["<any named third-party beneficiaries>"],
    "excluded_parties": ["<any explicitly excluded parties>"]
  }}
}}

Return ONLY valid JSON. No commentary, no markdown, no explanation.

Before returning, self-check:
- Keep schema exactly unchanged
- Include only real legal entities or clearly defined contract roles as parties
- Remove generic nouns, document component names, currency terms, and malformed/truncated party names
- If uncertain, use null/[] instead of guessing
"""


# ─── PASS 2: Clause Extraction + Risk Classification ─────────────────────────

PASS_2_CLAUSES = """
You are analyzing a legal contract. Extract EVERY clause listed below.

You MUST extract ALL clauses from ALL sections of the document, including embedded agreements such as NDAs, annexures, or addendums. Do NOT ignore sections after the primary agreement.

DOCUMENT PROFILE: {document_profile_json}
PARTIES IN CONTRACT: {parties_json}
KNOWLEDGE BASE CONTEXT: {rag_context}

CLAUSES TO EXTRACT:
{clauses_block}

Return ONLY a valid JSON array with exactly {expected_count} clause objects.

Each object in the array must follow this exact schema:
{{
  "clause_id": "<clause id>",
  "section_number": "<e.g. 5.2 or null>",
  "heading": "<section heading>",
  "text": "<verbatim clause text>",
  "plain_english": "<clear, simple 1-2 sentence explanation what this clause means>",
  "type": "<primary type: Confidentiality|Termination|Liability|Payment|Indemnification|IP|Non-Compete|Warranty|Governing Law|Dispute Resolution|Force Majeure|Amendment|Notice|Assignment|Severability|Entire Agreement|Other>",
  "category": "<one of: Obligation|Right|Prohibition|Condition|Definition|Remedy|Representation>",
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "risk_score": <0-100 integer>,
  "risk_justification": "<why this risk score? specific reasoning>",
  "affected_party": "<which party bears the risk, or null>",
  "obligations": ["<specific actions required>"],
  "rights": ["<entitlements granted>"],
  "deadlines": ["<any time constraints>"],
  "is_unilateral": <true if only one party bears burden>,
  "is_mutual": <true if both parties equally bound>,
  "is_standard": <true if this is a typical clause, false if unusual>,
  "is_ambiguous": <true if wording is vague>,
  "ambiguity_reason": "<why it's ambiguous or null>",
  "tags": ["<2-5 keywords>"],
  "cross_references": ["<references to other sections>"]
}}

RISK SCORING GUIDE:
- LOW (0-30): Standard boilerplate, industry-normal terms, balanced obligations
- MEDIUM (31-60): One-sided but common, minor unusual terms, standard penalties
- HIGH (61-85): Significant exposure, unlimited liability, broad IP assignment
- CRITICAL (86-100): Extreme exposure, unconscionable terms, illegal provisions

Grounding rules (strict):
- Use clause text as the primary source; do not infer missing facts
- Do NOT classify as Liability or Payment unless explicit trigger language exists in the clause text
- If no explicit obligation language exists, obligations must be []
- Do not output generic obligations (for example, "limit liability") unless those exact obligations are explicit in the clause text
- If uncertain about type, risk, or affected party, use Other/UNKNOWN/null rather than guessing

Return ONLY valid JSON array. No commentary.

Before returning, self-check:
- Obligations and deadlines are complete phrases/sentences, not truncated fragments
- Parties are real entities/roles from the text, not defined terms or currency terms
- If any extracted field is unsupported by text, replace it with null/[]
"""


# ─── PASS 3: Obligations, Rights, Timelines ───────────────────────────────────

PASS_3_OBLIGATIONS = """
Analyze the full contract text and extract all obligations, rights, and timeline events.

CONTRACT TEXT:
{contract_text}

PARTIES: {parties_json}
DOCUMENT PROFILE: {document_profile_json}
CLAUSES ALREADY IDENTIFIED: {clause_ids_json}

Return a JSON object with EXACTLY this structure:
{{
  "obligations": [
    {{
      "party": "<party name>",
      "action": "<specific action they must take>",
      "clause_id": "<clause reference>",
      "deadline": "<when they must do it, or null>",
      "consequence_of_breach": "<what happens if violated>",
      "is_recurring": <true if ongoing obligation>
    }}
  ],
  "rights": [
    {{
      "party": "<party name>",
      "right": "<entitlement or permission>",
      "clause_id": "<clause reference>",
      "conditions": "<conditions required to exercise this right>",
      "is_exclusive": <true if exclusive right>
    }}
  ],
  "timelines": [
    {{
      "event": "<what happens>",
      "timeframe": "<when, e.g. 30 days from invoice>",
      "trigger": "<what starts the clock>",
      "party_responsible": "<who must act>",
      "clause_id": "<clause reference>",
      "is_hard_deadline": <true if non-negotiable deadline>
    }}
  ]
}}

Return ONLY valid JSON. No commentary.

Before returning, self-check:
- obligations[].action and rights[].right must be complete, non-truncated statements
- party values must be real legal entities or clearly defined roles from the contract
- if unsupported by text, return [] instead of speculative entries
"""


# ─── PASS 4: Financial Terms ───────────────────────────────────────────────────

PASS_4_FINANCIAL = """
Extract all financial, commercial, and monetary terms from this contract.

CONTRACT TEXT:
{contract_text}

Return a JSON object with EXACTLY this structure:
{{
  "financial_terms": {{
    "payment_terms": {{
      "currency": "<USD/INR/EUR/etc.>",
      "total_contract_value": "<total value or null>",
      "payment_schedule": "<One-time|Monthly|Quarterly|Milestone-based|etc.>",
      "amount_per_period": "<amount per payment period>",
      "due_days": <integer number of days or null>,
      "payment_method": "<wire transfer/check/etc.>",
      "advance_payment": "<upfront payment required?> ",
      "late_payment_interest": "<penalty rate or null>",
      "invoice_period": "<how often invoices are sent>"
    }},
    "penalties": ["<list every penalty clause verbatim>"],
    "liability_cap": "<max liability amount, or 'Unlimited' if uncapped>",
    "indemnification_cap": "<cap on indemnification or null>",
    "liquidated_damages": "<predefined damages amount or null>",
    "revenue_share": "<if applicable, else null>",
    "equity_terms": "<if applicable, else null>"
  }}
}}

Return ONLY valid JSON. No commentary.

Before returning, self-check:
- keep monetary values exact and non-truncated
- do not invent financial fields not supported in text
- if unsupported, return null/[]
"""


PASS_4_FINANCIAL_LLM = """
Extract financial, commercial, and lending terms from this contract and return ONLY valid JSON.

CONTRACT TEXT:
{contract_text}

Return EXACTLY this JSON object:
{{
  "financial_terms": {{
    "payment_terms": {{
      "currency": "<USD/INR/EUR/etc. or null>",
      "total_contract_value": "<principal/total amount or null>",
      "payment_schedule": "<lump sum|periodic|milestone|other|null>",
      "amount_per_period": "<periodic amount or null>",
      "due_days": <integer or null>,
      "payment_method": "<wire/check/ACH/etc. or null>",
      "advance_payment": "<upfront payment terms or null>",
      "late_payment_interest": "<rate or null>",
      "invoice_period": "<invoice cadence or null>"
    }},
    "penalties": ["<narrative penalty with trigger condition>"] ,
    "liability_cap": "<cap amount or null>",
    "indemnification_cap": "<cap amount or null>",
    "liquidated_damages": "<amount/formula or null>",
    "revenue_share": "<formula or null>",
    "equity_terms": "<equity terms or null>"
  }}
}}

You MUST include when present:
- currency
- principal/total contract value
- payment schedule type
- fee amounts and fee types (origination, amendment, commitment)
- penalty structures with trigger conditions (not section headings)
- interest rates and basis (fixed/variable)
- collateral values if explicitly stated

Return ONLY valid JSON. No markdown or commentary.
"""


# ─── PASS 5: Intelligence Layer ────────────────────────────────────────────────

PASS_5_INTELLIGENCE = """
You are performing deep legal intelligence analysis on this contract.

CONTRACT TEXT:
{contract_text}

DOCUMENT TYPE: {document_type}
DOCUMENT PROFILE: {document_profile_json}
PARTIES: {parties_json}
CLAUSE SUMMARY: {clause_summary_json}

Return a JSON object with EXACTLY this structure:
{{
  "risks": [
    {{
      "clause_id": "<reference or null>",
      "risk_type": "<one of: Unlimited Liability|One-sided Termination|Broad IP Assignment|Auto Renewal Trap|Penalty Clause|Data Privacy Risk|Jurisdiction Risk|Ambiguous Language|Missing Standard Clause|Broad Indemnification|Non-Compete Risk|Payment Risk|Force Majeure Absent>",
      "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "reason": "<clear explanation of why this is risky>",
      "impacted_party": "<who is at risk>",
      "risk_sentence": "<exact sentence causing risk>",
      "suggestion": "<concrete fix or negotiation language>",
      "legal_precedent": "<brief reference if applicable>",
      "risk_labels": ["<optional secondary labels>"],
      "risk_context": "<optional short note linking the risk to a clause or theme>"
    }}
  ],
  "missing_clauses": [
    {{
      "clause_type": "<e.g. Force Majeure, Dispute Resolution, IP Ownership>",
      "importance": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "reason_needed": "<why this clause matters for this document type>",
      "suggested_language": "<brief template text to add>"
    }}
  ],
  "clause_dependencies": [
    {{
      "clause_id_1": "<clause>",
      "clause_id_2": "<clause>",
      "relation_type": "<modifies|triggers|conflicts_with|supersedes|linked_to>",
      "description": "<how they relate>"
    }}
  ],
  "negotiation_points": [
    {{
      "issue": "<what is problematic>",
      "clause_id": "<reference>",
      "favorable_to": "<which party benefits>",
      "disadvantaged_party": "<who is harmed>",
      "leverage": "<argument to make in negotiation>",
      "suggested_counter": "<counter-proposal language>"
    }}
  ],
  "compliance_flags": [
    {{
      "regulation": "<GDPR|CCPA|Indian IT Act|HIPAA|etc.>",
      "clause_id": "<reference>",
      "issue": "<what the compliance concern is>",
      "severity": "<LOW|MEDIUM|HIGH|CRITICAL>",
      "recommendation": "<what to change>"
    }}
  ],
  "summary": {{
    "executive_summary": "<3-4 sentence plain-English overview of what this contract does>",
    "key_points": ["<top 5 most important facts about this contract>"],
    "red_flags": ["<critical issues requiring immediate attention>"],
    "favorable_clauses": ["<clauses that protect the reviewing party>"],
    "unusual_clauses": ["<non-standard or uncommon terms>"],
    "favorable_to": "<Party A name|Party B name|Neither|Both>",
    "overall_risk_score": <0-100 integer>,
    "risk_distribution": {{"LOW": <n>, "MEDIUM": <n>, "HIGH": <n>, "CRITICAL": <n>}},
    "recommended_actions": ["<top 3-5 concrete actions before signing>"]
  }}
}}

Return ONLY valid JSON. No commentary.

Before returning, self-check:
- do not create risks without explicit trigger phrases in text
- if evidence is weak/absent, lower severity or omit the item
- keep all extracted snippets complete and non-truncated
"""


PASS_5_RISKS = """
Generate risks JSON only.
Return EXACT object with key "risks" containing a non-empty array of RiskItem-compatible objects.

{common_block}

Return ONLY valid JSON.
"""


PASS_5_MISSING_DEPS = """
Generate missing clauses and dependencies JSON only.
Return EXACT object with keys "missing_clauses" and "clause_dependencies".

{common_block}

Return ONLY valid JSON.
"""


PASS_5_NEGOTIATION = """
Generate negotiation and compliance JSON only.
Return EXACT object with keys "negotiation_points" and "compliance_flags".

{common_block}

Return ONLY valid JSON.
"""


PASS_5_SUMMARY = """
Generate summary JSON only.
Return EXACT object with key "summary" and full DocumentSummary fields.

{common_block}

You MUST populate ALL of the following with substantive content:
- executive_summary: 3-5 sentence narrative (NOT "The document contains N clauses")
- key_points: 3-7 most important terms, obligations, or facts
- red_flags: include all HIGH and CRITICAL risk items found
- favorable_clauses: clauses protecting the weaker/reviewing party
- unusual_clauses: non-standard, one-sided, or atypical provisions
- recommended_actions: 3-6 concrete and specific reviewer actions

Return ONLY valid JSON.
"""


# Two-pass grounded pipeline prompts
SYSTEM_PROMPT_FACTS = """You are a legal fact extractor.
Task: return ONE strict JSON object only.
Hard rules:
- Output must start with { and end with }
- No markdown, no code fences, no prose, no preface
- Use double-quoted JSON keys and string values
- If a field has no value, return [] for arrays and keep all required keys
- Never add keys not requested
- Do not classify, infer risk, or infer obligations/rights
- Extract only what is explicitly present in clause text
- A party is valid only if it is a legal entity name or a clearly defined contract role
- Ignore defined terms, monetary/currency terms, section labels, and generic uppercase tokens
- If uncertain, return [] rather than guessing
"""


PASS_1_FACT_EXTRACTION = """
Extract facts from this single legal clause.

CLAUSE ID: {clause_id}
SECTION HEADING: {section_heading}
CLAUSE TEXT:
{clause_text}

Return ONLY this JSON object:
{{
  "parties": ["<only legal entity names explicitly present in text>"],
  "monetary_values": ["<money amounts exactly as written>"],
  "dates": ["<dates exactly as written>"],
  "actions": ["<explicit action phrases from text>"],
  "raw_text": "<exact clause text>"
}}

Rules:
- No clause type
- No risk scoring
- No obligations or rights inference
- No extra keys
- Extract parties ONLY if they are legal entities or clearly defined contract roles
- Ignore monetary terms (USD, Dollars), defined terms (for example Revolver Commitment Amount), and generic uppercase tokens (for example STATE, LOAN, SECURITY)
- Actions must be complete, non-truncated phrases directly present in text
- raw_text must be the exact clause text, unchanged
- If nothing found for a list field, return []
- Do not include null in list fields
- Output must be valid JSON parseable by json.loads
- First character must be {{ and last character must be }}

Before returning, self-check:
- every party is a real entity/role supported by text
- no action is truncated
- no guessed items are present
"""


SYSTEM_PROMPT_REASONING = """You are a legal reasoning assistant.
Task: return ONE strict JSON object only.
Hard rules:
- Output must start with { and end with }
- No markdown, no code fences, no prose
- Use only provided clause text and extracted facts
- If unsupported, return UNKNOWN or []
- Never invent party names or obligations not in text
- Never add keys not requested
- Do not infer risk without explicit trigger phrases in the clause text
- Do not over-classify: do not default to Liability or Payment unless explicit support exists
- If uncertain, choose Definition/Other and LOW risk
"""


PASS_2_REASONING = """
Reason over one clause using grounded facts only.

CLAUSE ID: {clause_id}
SECTION HEADING: {section_heading}
CLAUSE TEXT:
{clause_text}

EXTRACTED FACTS:
{facts_json}

Return ONLY this JSON object:
{{
  "clause_type": "<known type or UNKNOWN>",
  "category": "<obligation|right|prohibition|condition|definition|remedy|representation>",
  "obligations": ["<must be directly grounded in clause text>"],
  "rights": ["<must be directly grounded in clause text>"],
  "risk_level": "<LOW|MEDIUM|HIGH|CRITICAL>",
  "risk_type": "<known risk or UNKNOWN>",
  "risk_justification": "<one sentence grounded in text>",
  "affected_party": "<party name from extracted facts or null>"
}}

Rules:
- If obligation is not explicit in text, return empty list
- If unsure about type/risk_type, return UNKNOWN
- Do not invent parties not in extracted facts
- No extra keys
- category must be one of: obligation, right, prohibition, condition, definition, remedy, representation
- risk_level must be one of: LOW, MEDIUM, HIGH, CRITICAL
- Output must be valid JSON parseable by json.loads
- First character must be {{ and last character must be }}

Obligation rules (strict):
- Each obligation must contain explicit obligation language such as "shall", "must", or "agree to"
- Each obligation must be a complete sentence/phrase from the clause text, not truncated
- If no explicit obligation phrase exists, obligations must be []

Clause type rules:
- If clause is introductory, recital, signature block, or definition-focused, prefer "Definition" or "Other"
- Do NOT classify as Liability or Payment unless explicit triggering language exists in the clause text

Risk rules:
- Assign HIGH only when explicit language indicates liability, penalty, indemnity, or waiver exposure
- Otherwise default to LOW
- Do NOT infer risk without explicit trigger phrases

Before returning, self-check:
- obligations/rights are grounded and non-truncated
- affected_party is from extracted facts or null
- unsupported fields are set to UNKNOWN/null/[] rather than guessed
"""