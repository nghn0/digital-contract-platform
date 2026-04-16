"""
Rate limit enforcement decorator for LLM calls.

Provides a decorator to enforce per-provider rate limiting on LLM call functions,
preventing quota exhaustion and API throttling.

Usage:
    @enforce_rate_limit()  # Auto-detect from LLM_CONFIG
    def my_llm_extraction():
        ...

    @enforce_rate_limit("gemini")  # Explicit provider
    def my_llm_extraction():
        ...
"""

from functools import wraps
from typing import Callable, Optional
import warnings

from config.runtime_limits import ENABLE_RATE_LIMITING
from utils.rate_limiter import GEMINI_RATE_LIMITER


def enforce_rate_limit(provider: Optional[str] = None) -> Callable:
    """
    Decorator to enforce rate limiting on LLM call functions.

    When applied to a function that makes LLM calls, this decorator will call
    the appropriate rate limiter's wait_if_needed() method before executing
    the function, preventing quota exhaustion.

    Args:
        provider: LLM provider name. If None, auto-detects from LLM_CONFIG.active_provider.
                 Valid values: 'gemini', 'openrouter', 'openai', 'grok', 'groq', 'anthropic'

    Returns:
        Decorated function that enforces rate limiting before execution.

    Example:
        @enforce_rate_limit()
        def _pass1_extract_clause_facts(clause_id, heading, text):
            # This will check rate limits before executing
            return call_llm(prompt, ...)
    """

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs):
            # Skip rate limiting if disabled globally
            if not ENABLE_RATE_LIMITING:
                return fn(*args, **kwargs)

            # Resolve provider lazily to avoid circular imports during module load.
            if provider is None:
                from core.llm_config import LLM_CONFIG  # Local import avoids import cycle.
                active_provider = LLM_CONFIG.active_provider
            else:
                active_provider = provider

            # Apply rate limiter (all providers use the same rate limiter currently)
            if active_provider in ("gemini", "openrouter", "openai", "grok", "groq", "anthropic"):
                GEMINI_RATE_LIMITER.acquire()  # Using acquire() which enforces limits
            else:
                # Unknown provider: warn and proceed without rate limiting
                warnings.warn(
                    f"No rate limiter configured for provider: {active_provider}. "
                    f"Proceeding without rate limiting. This may cause quota exhaustion.",
                    RuntimeWarning,
                    stacklevel=2
                )

            # Execute the original function
            return fn(*args, **kwargs)

        return wrapper

    return decorator
