# core/__init__.py
"""
Core module for LegalT - contains LLM config and prompts
"""
from .llm_config import (
    LLM_CONFIG,
    call_llm,
    call_llm_async,
    get_llm_client,
    get_embedding_vectors,
    has_active_api_key,
    get_active_model_name,
    get_active_embedding_model_name,
)

__all__ = [
    "LLM_CONFIG",
    "call_llm",
    "call_llm_async",
    "get_llm_client",
    "get_embedding_vectors",
    "has_active_api_key",
    "get_active_model_name",
    "get_active_embedding_model_name",
]
