"""
Token estimation and processing mode selection utilities.

Provides functions to estimate token count from text and select the optimal
processing mode (full_doc, hybrid, batched) based on document size.
"""

from config.runtime_limits import BATCH_SIZE

# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS (module-level)
# ─────────────────────────────────────────────────────────────────────────────

FULL_DOC_MAX_TOKENS = 8_000      # Send full document in one LLM call
HYBRID_MAX_TOKENS = 30_000       # Extract structure first, then batch-process clauses
CHARS_PER_TOKEN = 4              # Heuristic for Gemini models


def estimate_tokens(text: str) -> int:
    """
    Estimate token count using heuristic (4 chars per token).
    
    For Gemini models, actual tokenization differs slightly, but this
    heuristic is sufficient for mode selection decisions.
    
    Args:
        text: Input text to estimate
        
    Returns:
        Estimated token count (0 if text is None or not a string)
    """
    if not text or not isinstance(text, str):
        return 0
    return len(text) // CHARS_PER_TOKEN


def choose_processing_mode(text: str) -> str:
    """
    Select pipeline execution mode based on estimated token count.
    
    Returns:
        "full_doc"  — document fits in single LLM context window (< 8k tokens)
        "hybrid"    — extract structure first, then batch-process clauses (< 30k tokens)
        "batched"   — chunk document before any processing (>= 30k tokens)
    """
    tokens = estimate_tokens(text)

    if tokens < FULL_DOC_MAX_TOKENS:
        return "full_doc"
    elif tokens < HYBRID_MAX_TOKENS:
        return "hybrid"
    else:
        return "batched"


def get_mode_config(mode: str) -> dict:
    """
    Return execution parameters for the selected processing mode.
    
    Args:
        mode: One of "full_doc", "hybrid", "batched"
        
    Returns:
        Configuration dict with keys:
        - max_tokens_per_call: Token limit per LLM call
        - clauses_per_batch: Number of clauses per batch (None if not batched)
        - chunk_size: Characters per document chunk (None if not needed)
        - description: Human-readable mode description
        
    Raises:
        ValueError: If mode is not recognized
    """
    configs = {
        "full_doc": {
            "max_tokens_per_call": FULL_DOC_MAX_TOKENS,
            "clauses_per_batch": None,
            "chunk_size": None,
            "description": "Full document fits in single context window",
        },
        "hybrid": {
            "max_tokens_per_call": 4000,
            "clauses_per_batch": BATCH_SIZE,
            "chunk_size": None,
            "description": "Extract structure first, then batch-process clauses",
        },
        "batched": {
            "max_tokens_per_call": 4000,
            "clauses_per_batch": BATCH_SIZE,
            "chunk_size": 6000,
            "description": "Chunk document before processing",
        },
    }

    if mode not in configs:
        raise ValueError(
            f"Unknown processing mode: {mode!r}. "
            f"Valid modes are: {', '.join(configs.keys())}"
        )

    return configs[mode]
