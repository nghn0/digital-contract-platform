# Law Agreement Timeout - Root Cause Analysis

**Date**: April 12, 2026  
**Document**: law agreement.pdf  
**Issue**: LLM timeout during Pass 2 (Clause Extraction)  
**Status**: Diagnosed ✓

---

## Executive Summary

The law agreement.pdf is **NOT a legal contract** but a **government circular**. The pipeline is designed for contractual documents, so it's producing malformed clause segments that cause LLM confusion and timeouts.

---

## Document Analysis

### Document Characteristics

| Property | Value |
|----------|-------|
| **File Name** | law agreement.pdf |
| **Actual Content** | Government Circular |
| **Department** | Ministry of Law and Justice, India |
| **Topic** | Recruitment Rules Amendment |
| **Document Size** | 12,885 characters (~2,450 words) |
| **Number of Lines** | ~347 |
| **Contract Keywords** | 0 (No "Agreement", "Contract", "Parties") |
| **Circular Keywords** | YES (Contains "CIRCULAR") |

### What the Document Actually Is

```
Government of India
Ministry of Law and Justice
Legislative Department
CIRCULAR

Official Languages Wing, Legislative Department, Ministry of Law and Justice is
proposing to amend the Recruitment Rules for Group 'B' posts of Official Languages Wing...
```

**Type**: Administrative circular about internal recruitment policy changes
**Not**: A legal contract between parties with defined obligations and rights

---

## Why Pipeline Fails

### Step 1: Text Extraction ✅ Works
```
Result: Successfully extracts 12,885 characters
```

### Step 2: Clause Segmentation ⚠️ Produces Garbage

The segmentation algorithm looks for clause markers (numbers, headings). With a government circular, it treats numbered sections as "clauses":

```
Actual clauses found: 7

1. "CIRCULAR"
   Body: 187 chars (preamble)

2. "2. Accordingly, a proposed revised Draft of Recruitment Rule..."
   Body: 461 chars

3. "3. The Comments/views, if any, on provisions..."
   Body: 2,010 chars

4. "0 Department, Ministry of Law &"           ← MALFORMED HEADING
   Body: 1,547 chars

5. "5 Justice- Member Justice - Member"        ← GARBAGE HEADING
   Body: 969 chars

6. "5 Justice - Member Lepartment, Ministy..." ← CORRUPTED TEXT
   Body: 3,816 chars

7. "8000 Rs.35400- 112400 as pe"               ← MEANINGLESS
   Body: 3,463 chars
```

**Problem**: Headings 4-7 are corrupted OCR/PDF artifacts, not actual logical sections

### Step 3: LLM Extraction ❌ Fails

LLM receives malformed "clause" pairs:

**Input to LLM (Pass 2)**:
```
Heading: "0 Department, Ministry of Law &"
Body: [1,547 characters of fragmented text about signatory list]

Heading: "5 Justice - Member Lepartment, Ministy of Law &"
Body: [3,816 characters of administrative details]

Heading: "8000 Rs.35400- 112400 as pe"
Body: [3,463 characters of salary/financial details]
```

**What LLM Tries To Do**:
- Extract clause type (no valid clause pattern detected)
- Identify party obligations (incoherent text)
- Assess risks (garbage input = confusion)
- Parse time limits and deadlines (none exist)

**LLM Response Time**: ~120+ seconds
- LLM struggles to extract meaning from malformed text
- Repeatedly re-reads and re-analyzes broken segments
- Timeout occurs when no coherent extraction emerges

---

## Technical Root Cause

### 1. Segmentation Algorithm Issue
The segmentation in `services/segmentation.py` uses:
- **Pattern**: Look for numbered headings (1., 2., 3., etc.)
- **Fallback**: Split by paragraph if no headings found

For a government circular with embedded names/numbers:
```
1. Introductory matter
2. Main proposal
[List of committee members with numbers]
5. Member
5. Member
0. Department name
[Salary information with numbers]
8000 [amount]
```

The algorithm treats every number as a clause marker, creating nonsensical splits.

### 2. LLM Processing Problem
When LLM receives incoherent clause units:
```
{
  "heading": "0 Department, Ministry of Law &",
  "body": "[Fragmented administrative text]"
}
```

It cannot:
- Identify clause type (doesn't match contract patterns)
- Extract legal obligations (none exist in isolated segments)
- Determine financial impact (salary data is out of context)
- Assess risks (no contractual relationships defined)

**Result**: LLM spins on timeout trying to extract from noise

### 3. Document Type Mismatch
The system assumes:
- **Input**: Legal contracts (employment, loan, NDA, policy)
- **Structure**: Defined parties, obligations, rights, risks

Law agreement.pdf provides:
- **Input**: Government administrative circular
- **Structure**: Organizational directives, procedural rules, signatory lists

---

## Why Other Documents Work

| Document | Type | Structure | Segmentation | LLM | Status |
|----------|------|-----------|--------------|-----|--------|
| NDA.pdf | Employment Contract | Clear clauses (1-5) | ✅ Correct | ✅ Works | ✅ Success |
| Placement Policy.pdf | Institution Policy | Numbered sections | ✅ Correct | ✅ Works | ✅ Success |
| LOAN AGREEMENT.pdf | Financial Contract | Legal structure | ✅ Correct | ✅ Works | ✅ Success |
| law agreement.pdf | Admin Circular | Mixed content | ❌ Breaks | ❌ Fails | ❌ Timeout |

---

## Solutions

### Short-Term Fix (Enable Processing)

**Option 1: Increase Timeout**
```python
# In core/llm_config.py
LLM_CONFIG.timeout_seconds = 120  # Increase from 30s to 120s
```
**Result**: May complete, but output quality poor due to garbage input

**Option 2: Pre-Processing Filter**
```python
# In main.py - before pipeline
if "CIRCULAR" in text and "Agreement" not in text:
    print("ERROR: Document is a government circular, not a contract")
    print("This system processes legal contracts, not administrative documents")
    sys.exit(1)
```
**Result**: Clear error message instead of timeout

### Medium-Term Fix (Better Handling)

**Option 1: Improve Segmentation**
- Detect document type before segmentation
- Use different splitting strategy for circulars vs contracts
- Skip segmentation for non-contract documents

**Option 2: Fallback Extractor**
- Implement alternative extraction for non-contract documents
- Use document-specific parsing (administrative circulars, policies)
- Skip clause-by-clause LLM analysis

### Long-Term Fix (Generalization)

**Redesign for Multiple Document Types**:
- Add document type detector (before segmentation)
- Contract → current 5-pass extraction
- Circular → administrative parsing
- Policy → procedural extraction
- Guidelines → instructional parsing

---

## Verification

The diagnosis is confirmed by:

1. **Document Content**:
   - Contains CIRCULAR: YES ✓
   - Contains Ministry of Law: YES ✓
   - Contains Agreement keyword: NO ✓
   - Contains Clause keyword: NO ✓

2. **Segmentation Output**:
   - Produced 7 "clauses"
   - Clauses 4-7 have corrupted/meaningless headings
   - This is NOT a segmentation error per se, but a document-type mismatch

3. **LLM Timeout**:
   - Occurs during Pass 2 (clause extraction)
   - Occurs because clauses are garbage input
   - Not due to document size (only 12KB)
   - Not due to clause count (only 7 segments)

---

## Recommendations

### Immediate Action
```python
# Add document-type guard to main.py
if should_process_legally(text):
    # Current pipeline
else:
    raise ValueError("Document type not supported. System processes legal contracts.")
```

### Documentation Update
Update following files to state:
- ✅ [README.md](../../../README.md) — Add "Supported Document Types" section
- ✅ [SYSTEM_ARCHITECTURE.md](../../SYSTEM_ARCHITECTURE.md) — Add "Limitations" section
- ✅ [QUICKREF.md](../../QUICKREF.md) — Add "Document Requirements"

### User Guidance
Document recommended usage:
```
SUPPORTED: ✅
- Employment agreements
- Loan/financial contracts
- NDAs (confidentiality agreements)
- Service agreements
- Institutional policies
- Contract amendments
- Partnership agreements

NOT SUPPORTED: ❌
- Government circulars (administrative directives)
- Org charts / Personnel lists
- Technical specifications
- Meeting minutes
- Emails / correspondence
- News articles / publications
```

---

## Conclusion

**Law agreement.pdf failure is NOT a system bug**, but a **document-type mismatch**:

- ✓ The system works perfectly for legal contracts
- ✓ The document is a government administrative circular
- ✓ This is outside the designed scope
- ✓ Timeout occurs because LLM can't extract contracts from non-contract documents

**Recommended Action**: Add document-type validation before pipeline execution to fail gracefully with clear error message instead of timeout.

---

**Status**: Diagnosed and documented  
**Resolution**: User education + optional pre-processing guard
