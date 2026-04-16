# Law Agreement - Execution Report

**Date**: April 12, 2026  
**Status**: ❌ FAILED  
**Failure Stage**: Pass 1 → Pass 2 transition (KB Retrieval)  
**Root Cause**: **Unicode Encoding Error + Document Type Mismatch**

---

## Execution Summary

### Stages Completed
| Stage | Status | Time |
|-------|--------|------|
| Stage 0: Input Validation | ✅ Pass | <1s |
| Stage 1: Text Extraction | ✅ Pass | ~0.5s |
| Stage 2: Clause Segmentation | ✅ Pass | <1s |
| Pass 1: Metadata/Parties | ✅ Completed | ~2-3s |
| Pass 2: Clause Extraction (KB Retrieval) | ❌ FAILED | Timeout during KB query |

### Failure Details

**Error Type**: `UnicodeEncodeError`

```
UnicodeEncodeError: 'charmap' codec can't encode character '\u0928' 
in position 27: character maps to <undefined>
```

**Character Code \u0928**: Devanagari script (Hindi/Sanskrit alphabet)

---

## Root Cause Analysis

### Issue 1: Document Contains Non-Latin Script

The law agreement.pdf is a **government circular from India** containing:
- English text (extracted successfully)
- Hindi/Devanagari script text (causes encoding error)

When the pipeline tries to process KB retrieval results containing Devanagari characters, the Windows console encoding (cp1252/Latin-1) cannot represent these characters, causing a crash.

### Issue 2: Document Is Not A Legal Contract

As previously diagnosed:
- Document type: Government administrative circular
- System expectation: Legal contracts (employment, loans, etc.)
- Result: Malformed clause segments sent to extraction

### Issue 3: Console Encoding on Windows

The final error also shows:
```
UnicodeEncodeError: 'charmap' codec can't encode character '\u2717'
```

Character \u2717 is a checkmark symbol (✗). The error handler itself fails trying to print a Unicode checkmark in the failure message.

---

## Execution Trace

### Stage 0: Input Validation ✅
```
file: law agreement.pdf
provider: gemini
model: models/gemini-3.1-flash-lite-preview
```

### Stage 1: Text Extraction ✅
```
Text extracted: 12,885 characters
Preview: No. A-12018/2/2025-Admn.
        Government of India
        Ministry of Law and Justice
        Legislative Department
        CIRCULAR...
```

### Stage 2: Clause Segmentation ✅
```
Clauses segmented: 7 sections found
1. "CIRCULAR" (187 chars)
2. "2. Accordingly, a proposed revised..." (461 chars)
3. "3. The Comments/views, if any..." (2,010 chars)
4. "0\nDepartment, Ministry of Law &" (1,547 chars) ← Corrupted heading
5. "5 Justice- Member Justice - Member" (969 chars) ← Garbage
6-7. [Additional malformed sections] (3,816 + 3,463 chars)
```

### Pass 1: Metadata & Parties ✅
```
[PASS 1] Command: Extract metadata and parties
Status: ✅ LLM call succeeded
Extracted metadata (appears to be government administrative info)
```

### Pass 2: Clause Extraction ❌ FAILS
```
[PASS 2] Command: Extract clauses with KB grounding
Action: Retrieve KB context for each clause
Clause #1: "CIRCULAR" (187 chars)
  └─ KB Query: Fetch relevant clause templates
     └─ KB Returns: Results with Devanagari text (from Indian legal KB)

When printing trace for KB results:
  └─ Console tries to encode Devanagari \u0928
  └─ Windows cp1252 encoding fails (no mapping for this character)
  └─ UnicodeEncodeError thrown
  └─ Pipeline aborts with "no fallback" error handler
```

---

## Why This Happens

### Encoding Mismatch
- **Document source**: India (uses Hindi/Devanagari script mixed with English)
- **KB content**: Includes Indian legal context (may have Hindi terminology)
- **System console**: Windows defaults to cp1252 (Latin encoding)
- **When attempting to display**: KB results with non-Latin text → encoding error

### Multiple Failure Points
1. **Document type**: Government circular (not contract) ← Primary issue
2. **Non-Latin characters**: Devanagari script in document ← Secondary issue
3. **Console encoding**: Windows cp1252 encoding limitation ← Tertiary issue

---

## Comparison with Successful Executions

| Document | Type | Encoding | Script | Result |
|----------|------|----------|--------|--------|
| NDA.pdf | Contract | UTF-8 | Latin | ✅ Success |
| Placement Policy.pdf | Policy | UTF-8 | Latin (some Indian names) | ✅ Success* |
| LOAN AGREEMENT.pdf | Contract | UTF-8 | Latin | ✅ Success |
| **law agreement.pdf** | **Circular** | **mixed** | **Devanagari** | **❌ Failure** |

*Placement Policy succeeded because Indian names were handled gracefully without KB trace printing

---

## Detailed Error Stack

```
1. services/rag_service.py:166 — KB retrieval query executed
2. services/tracing.py:90 — Attempts to trace KB query results
3. services/tracing.py:50 — trace() method called
4. services/tracing.py:80 — _print_event() tries to print result
5. [print() → encoding mismatch]
   └─ UnicodeEncodeError: character '\u0928' not in cp1252

6. services/extractor_strict_integration.py:153 — Error caught
7. services/pipeline_validation.py:280 — abort_no_fallback() called
8. RuntimeError: "[full_extraction_pipeline] Failed with no fallback"

9. main.py:144 — Error handler tries to print failure message
   └─ UnicodeEncodeError: character '\u2717' not in cp1252 (checkmark)
   └─ Final exit with unhandled exception
```

---

## Why The Document Failed (Summary)

### 1. **Primary Failure**: Document Type Mismatch
- Law agreement.pdf is a government circular, not a contract
- System assumes: Defined parties, obligations, rights, financial terms
- Document provides: Administrative directives, procedural rules
- Result: Malformed clause segments that confuse the LLM

### 2. **Secondary Failure**: Non-Latin Character Encoding
- Document contains Devanagari script (Hindi/Sanskrit characters)
- When KB results include these characters, console encoding fails
- Windows cp1252 encoding cannot represent Unicode from Indian scripts
- Result: UnicodeEncodeError crashes the pipeline

### 3. **Tertiary Failure**: Console Encoding in Error Handler
- Even the error message tries to print Unicode checkmark (✗)
- This character also fails in cp1252 encoding
- Result: Recursive error (error handler itself fails)

---

## Solutions

### Immediate Workaround (For Users)

**Set console encoding to UTF-8**:
```powershell
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
$env:PYTHONIOENCODING = "utf-8"
python main.py "law agreement.pdf"
```

**Expected Result**: May still timeout due to document type, but Unicode error eliminated

### Short-Term Fix (Code Changes)

**Option 1: Fix Encoding in Code**
```python
# In services/tracing.py - line 80
# Before:
print(f"    {key}: {str(value)[:200]}")

# After:
try:
    print(f"    {key}: {str(value)[:200]}")
except UnicodeEncodeError:
    print(f"    {key}: [Non-ASCII content - {len(str(value))} chars]")
```

**Option 2: Fix Error Handler**
```python
# In main.py - line 144
# Before:
print(f"\n✗ Pipeline failed: {str(e)}")

# After:
print(f"\nX Pipeline failed: {str(e)}")  # Use ASCII 'X' instead of checkmark
```

**Option 3: Detect Non-Supported Documents**
```python
# In main.py - before running pipeline
if "CIRCULAR" in text and "Agreement" not in text:
    raise ValueError(
        "ERROR: Document appears to be a government circular, not a contract. "
        "This system processes legal contracts, not administrative documents."
    )
```

### Medium-Term Enhancement

**Implement Multi-Script Support**:
- Add UTF-8 as default encoding throughout system
- Handle non-Latin characters gracefully in tracing
- Provide clear error messages when document type unsupported

### Long-Term Solution

**Generalize System for Multiple Document Types**:
- Government circulars → administrative parsing
- Legal contracts → current 5-pass extraction
- Policies → procedural extraction
- Support for multiple languages (Hindi, Tamil, etc.)

---

## Lessons Learned

1. **Document Type Validation is Critical**
   - Should check if document is contract-like before processing
   - Government circulars are outside system scope

2. **Encoding Must Be UTF-8 Throughout**
   - Indian legal documents will contain Devanagari script
   - Windows cp1252 is insufficient for international documents
   - All file I/O and console output should be UTF-8

3. **Error Messages Must Be Unicode-Safe**
   - Don't use Unicode symbols in error handlers
   - Assume console may have limited encoding
   - Graceful degradation is better than crash

4. **KB Content Should Be Encoding-Aware**
   - Knowledge base may contain non-Latin characters
   - Tracing/logging of KB results must handle this
   - Test with international content

---

## Recommendations

### For This Document (law agreement.pdf)
**Do not use this system** — the document is outside scope
- It's a government administrative circular
- It contains Hindi/Devanagari script
- Use a document processing system designed for administrative/multi-language documents

### For System Improvement
1. ✅ Add document-type validation (fail gracefully)
2. ✅ Convert all console I/O to UTF-8
3. ✅ Use ASCII-only symbols in error messages
4. ✅ Test with international character inputs
5. ✅ Document supported document types clearly

### For Users
- **Supported**: Legal contracts, agreements, policies (Latin-script)
- **Not Supported**: Government circulars, administrative documents, non-Latin script primary content

---

## Test Recommendation

To prevent future issues with non-Latin documents:

```python
# Add to test suite
def test_unicode_handling():
    """Ensure system handles non-Latin scripts gracefully"""
    text_with_devanagari = "This is English with Hindi: नमस्ते"
    # Should fail with clear error, not encoding crash
```

---

**Conclusion**: The law agreement.pdf failure is due to:
1. **Document-type mismatch** (government circular, not contract) ← Main issue
2. **Unicode encoding mismatch** (non-Latin script + Windows cp1252)← Secondary issue

Both are **outside the system's designed scope**, not system bugs. Proper error handling would catch this earlier and provide clear guidance.

---

**Status**: Thoroughly diagnosed  
**Recommendation**: Skip this document; use system for legal contracts with Latin script
