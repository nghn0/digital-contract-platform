# PDF Comparison Test Suite

Generalized metrics and testing framework for validating LegalT extraction accuracy against actual PDF content.

## Overview

The PDF comparison suite provides:
- **Unified metrics extraction** from PDF files and extraction JSON outputs
- **Reusable comparison framework** that works with any document type
- **Quality validation checks** to ensure extraction completeness and accuracy
- **Pytest test suite** for automated validation
- **Report generation** for visual comparison of PDF vs extracted output

## Files

### Core Modules
- `pdf_metrics.py` - Main metrics extraction and comparison framework
  - `PDFMetrics` - Stores PDF document metrics
  - `ExtractionMetrics` - Stores extraction output metrics
  - `PDFComparator` - Core comparison engine
  - `compare_pdf_and_extraction()` - Convenience function

- `test_pdf_extraction_metrics.py` - Comprehensive pytest test suite
  - Tests PDF metric extraction
  - Tests JSON parsing and metrics
  - Tests text coverage calculation
  - Tests section tagging
  - Tests validation checks
  - Tests hybrid document detection
  - Tests clause extraction completeness
  - Parametrized tests for multiple document types

- `__init__.py` - Package initialization and exports

### Standalone Reports
- `pdf_comparison_report.py` (in this folder) - Standalone report generator
  - Can be run with default files or custom PDF/JSON paths
  - Generates human-readable comparison report
  - Shows validation results and quality assessment

## Usage

### As a Test Suite (Recommended)

Run all PDF comparison tests:
```bash
pytest tests/pdf_comparison/test_pdf_extraction_metrics.py -v
```

Run specific test:
```bash
pytest tests/pdf_comparison/test_pdf_extraction_metrics.py::TestPDFExtractionMetrics::test_text_coverage_metric -v
```

Run with different document:
```bash
pytest tests/pdf_comparison/test_pdf_extraction_metrics.py -v -k "parametrize"
```

### As a Library

```python
from tests.pdf_comparison.pdf_metrics import PDFComparator

# Create comparator
comparator = PDFComparator()

# Extract metrics
pdf_metrics = comparator.extract_pdf_metrics('path/to/document.pdf')
extraction_metrics = comparator.extract_json_metrics('path/to/output.json')

# Print summary
comparator.print_summary()

# Get detailed report
report = comparator.generate_report(include_clauses=True)
print(report)
```

### Standalone Report Generator

```bash
# Default (NDA example)
python tests/pdf_comparison/pdf_comparison_report.py

# Custom files
python tests/pdf_comparison/pdf_comparison_report.py tests/input/LOAN AGREEMENT.pdf logs/loan_output.json
```

## Key Metrics

### PDF Metrics
- **Total Pages** - Number of pages in the PDF
- **Total Characters** - Complete text size
- **Page Contents** - Text extracted per page
- **Total Text** - Full concatenated text

### Extraction Metrics
- **Total Clauses** - Number of clauses extracted
- **Document Type** - Classified document type
- **Document Subtype** - Specific classification (e.g., "Hybrid: Employment, NDA")
- **Text Coverage %** - Percentage of PDF text captured in clauses
- **Average Clause Length** - Mean characters per clause
- **Clause Tags Distribution** - Count by section type (Employment, NDA, General, etc.)

### Validation Checks

The framework performs these quality checks:

1. **Content Coverage** ✓
   - Validates text coverage is ≥ 90%
   - Ensures no significant content is lost

2. **Clause Count Reasonable** ✓
   - Validates at least 3 clauses extracted
   - Ensures document is properly segmented

3. **Sections Tagged** ✓
   - Validates clauses have source section tags
   - Ensures categorization is applied

4. **Document Classified** ✓
   - Validates document has a type classification
   - Ensures metadata extraction worked

5. **Hybrid Detected** ✓
   - For mixed documents, validates "Hybrid" flag present
   - Ensures multi-type documents are recognized

## Examples

### NDA.pdf Extraction
```
Document: NDA.pdf
Pages: 4
Total Characters: 6,463
Clauses Extracted: 15
Document Type: Hybrid: Employment, NDA
Text Coverage: 97.2%

Section Breakdown:
  Employment: 8 clauses
  NDA: 4 clauses
  General: 3 clauses

Validation: 5/5 checks passed ✓
```

### LOAN AGREEMENT.pdf Extraction
```
Document: LOAN AGREEMENT.pdf
Pages: (extracted dynamically)
Clauses Extracted: (varies)
Text Coverage: (varies)

Validation: Checks pass based on extraction quality
```

## Adding New Tests

To add tests for a new document type:

1. Add fixture to `TestPDFExtractionMetrics`:
```python
@pytest.fixture
def new_doc_files(self):
    return {
        "pdf": "tests/input/NewDoc.pdf",
        "json": "logs/new_output.json"
    }
```

2. Create test method using fixture:
```python
def test_new_doc_specific_checks(self, new_doc_files):
    comparator = PDFComparator()
    comparator.extract_pdf_metrics(new_doc_files["pdf"])
    metrics = comparator.extract_json_metrics(new_doc_files["json"])
    
    # Custom assertions for this document type
    assert metrics.total_clauses >= expected_count
```

## Extending the Framework

The framework is extensible. To add new metrics:

1. **Add field to `ExtractionMetrics`** dataclass
2. **Update `extract_json_metrics()`** to calculate new metric
3. **Add validation check** in `_validate_extraction()`
4. **Add test** in `test_pdf_extraction_metrics.py`

## Performance Notes

- PDF extraction speed depends on document complexity
- Typical small document (~5 pages): < 1 second
- JSON parsing is instant (< 100ms)
- Comparison report generation: < 500ms

## Dependencies

- `pdfplumber` - PDF text extraction
- `pytest` - Test framework
- `json` - JSON parsing (stdlib)
- `pathlib` - Path handling (stdlib)

## Common Issues

### "pdfplumber required"
Install with: `pip install pdfplumber`

### "JSON file not found"
Ensure extraction has been run and output file exists at specified path

### "Coverage < 90%"
May indicate incomplete extraction. Check:
- PDF is not OCR-required
- Extraction prompts are comprehensive
- LLM call succeeded (check logs for errors)

---

**Generalized PDF Comparison Framework for LegalT Contract Analysis**
