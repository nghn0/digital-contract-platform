# Consolidated Run Reports

Date: 2026-04-12

This file consolidates the outcomes from recent operational reports to reduce root-level clutter while preserving the key findings.

## Scope Covered
- Multi-document execution status across NDA, placement policy, and loan documents
- Law-agreement diagnosis and execution failure analysis
- Remediation notes for segmentation and encoding-related failure modes

## Consolidated Findings
- The pipeline succeeds on contract-shaped documents such as NDA and loan agreements.
- The loan amendment path is recognized as derivative and now uses derivative-aware missing-clause logic.
- The law agreement input is an administrative circular, not a contract, and causes degraded segmentation and extraction quality.
- Unicode/console-print behavior can fail on non-Latin script when terminal encoding is not UTF-8.

## Recommended Operational Guardrails
1. Reject or route non-contract document classes before full extraction.
2. Keep UTF-8 console/output settings for multilingual document traces.
3. Keep verbose debug traces out of the repo root and stage-debug folders unless actively investigating.

## Archived Source Reports
- Former root file: LAW_AGREEMENT_DIAGNOSIS.md
- Former root file: LAW_AGREEMENT_EXECUTION_REPORT.md
- Former root file: MULTI_DOCUMENT_ANALYSIS.md

These files were moved under docs/reports/archive for cleanliness.
