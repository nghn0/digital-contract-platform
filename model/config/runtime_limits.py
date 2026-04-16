from __future__ import annotations

import os


def _is_true(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


SAFE_TEST_MODE = _is_true(os.environ.get("SAFE_TEST_MODE"))
ENABLE_RATE_LIMITING = _is_true(os.environ.get("ENABLE_RATE_LIMITING", "true"))

MAX_PARALLEL_REQUESTS = 2 if SAFE_TEST_MODE else 3

# Clause extraction batching defaults. Size 4 balances throughput and response stability.
CLAUSE_BATCH_SIZE = 2 if SAFE_TEST_MODE else 4
BATCH_SIZE = CLAUSE_BATCH_SIZE

# Centralized pass-level output budgets to avoid under-filled structured sections.
PASS_TOKEN_LIMITS: dict[str, int] = {
    "pass_1_metadata": 900 if SAFE_TEST_MODE else 1200,
    "pass_2_clause_single": 700 if SAFE_TEST_MODE else 800,
    "pass_2_clause_batch_4": 1800 if SAFE_TEST_MODE else 2800,
    "pass_2_clause_batch_6": 2600 if SAFE_TEST_MODE else 4000,
    "pass_3_obligations": 1400 if SAFE_TEST_MODE else 2000,
    "pass_4_financial": 1200 if SAFE_TEST_MODE else 1800,
    "pass_5_risks": 1400 if SAFE_TEST_MODE else 1800,
    "pass_5_missing_deps": 1400 if SAFE_TEST_MODE else 1800,
    "pass_5_negotiation": 1400 if SAFE_TEST_MODE else 1800,
    "pass_5_summary": 2000 if SAFE_TEST_MODE else 3000,
}


def get_batch_token_limit(batch_size: int) -> int:
    """Return a bounded output-token budget for a clause extraction batch.

    Args:
        batch_size: Number of clauses in the current batch.

    Returns:
        Integer token limit with a hard upper cap to avoid oversized responses.
    """
    per_clause = 500 if SAFE_TEST_MODE else 700
    hard_cap = 3500 if SAFE_TEST_MODE else 6000
    return min(max(batch_size, 1) * per_clause, hard_cap)


# Backward-compatible default for modules that still consume a single token limit.
DEFAULT_MAX_TOKENS = PASS_TOKEN_LIMITS["pass_1_metadata"]
