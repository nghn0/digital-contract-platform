from __future__ import annotations

import json
import os
import random
import sys
import time
import asyncio
from dataclasses import dataclass
from typing import Any, Literal
from urllib import error, request

from config.runtime_limits import DEFAULT_MAX_TOKENS, ENABLE_RATE_LIMITING
from core.rate_limit_decorator import enforce_rate_limit
from dotenv import load_dotenv
from utils.rate_limiter import GEMINI_RATE_LIMITER

load_dotenv()

ProviderName = Literal["openrouter", "anthropic", "openai", "gemini", "grok"]
LLMStage = Literal["default", "extraction", "reasoning", "reasoning_fallback"]

CANONICAL_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


def _resolve_provider_from_env() -> ProviderName:
    raw = os.environ.get("LLM_PROVIDER", "gemini").strip().lower()
    if raw in {"openrouter", "anthropic", "openai", "gemini", "grok"}:
        return raw  # type: ignore[return-value]
    return "gemini"


@dataclass(frozen=True)
class ProviderSpec:
    name: ProviderName
    api_key_env: str
    base_url: str
    default_model: str
    api_style: Literal["openai_chat", "anthropic_messages"]


PROVIDER_REGISTRY: dict[ProviderName, ProviderSpec] = {
    "openrouter": ProviderSpec(
        name="openrouter",
        api_key_env="OPENROUTER_API_KEY",
        base_url="https://openrouter.ai/api/v1",
        default_model=CANONICAL_MODEL,
        api_style="openai_chat",
    ),
    "anthropic": ProviderSpec(
        name="anthropic",
        api_key_env="ANTHROPIC_API_KEY",
        base_url="https://api.anthropic.com",
        default_model="claude-3-5-sonnet-20241022",
        api_style="anthropic_messages",
    ),
    "openai": ProviderSpec(
        name="openai",
        api_key_env="OPENAI_API_KEY",
        base_url="https://api.openai.com/v1",
        default_model="gpt-4o-mini",
        api_style="openai_chat",
    ),
    "gemini": ProviderSpec(
        name="gemini",
        api_key_env="GEMINI_API_KEY",
        base_url="https://generativelanguage.googleapis.com/v1beta/openai",
        default_model="models/gemini-3.1-flash-lite-preview",
        api_style="openai_chat",
    ),
    "grok": ProviderSpec(
        name="grok",
        api_key_env="GROK_API_KEY",
        base_url="https://api.x.ai/v1",
        default_model="grok-4.20-reasoning",
        api_style="openai_chat",
    ),
}


@dataclass(frozen=True)
class LLMConfig:
    active_provider: ProviderName
    model: str
    temperature: float
    max_tokens: int
    top_p: float
    stream: bool
    embedding_model: str


LLM_CONFIG = LLMConfig(
    active_provider=_resolve_provider_from_env(),
    model=PROVIDER_REGISTRY[_resolve_provider_from_env()].default_model,
    temperature=0.1,
    max_tokens=1200,
    top_p=1.0,
    stream=False,
    embedding_model="text-embedding-3-small",
)

# Stage model routing stays centralized here so downstream modules don't hardcode model IDs.
STAGE_MODEL_DEFAULTS: dict[LLMStage, str] = {
    "default": CANONICAL_MODEL,
    "extraction": CANONICAL_MODEL,
    "reasoning": CANONICAL_MODEL,
    "reasoning_fallback": CANONICAL_MODEL,
}

STAGE_MODEL_ENV_OVERRIDES: dict[LLMStage, str] = {
    "default": "LLM_MODEL",
    "extraction": "LLM_MODEL_EXTRACTION",
    "reasoning": "LLM_MODEL_REASONING",
    "reasoning_fallback": "LLM_MODEL_REASONING_FALLBACK",
}


@dataclass
class TextBlock:
    text: str


@dataclass
class UnifiedMessageResponse:
    content: list[TextBlock]
    raw: dict[str, Any]


@dataclass
class UnifiedEmbeddingResponse:
    embeddings: list[list[float]]
    raw: dict[str, Any]


def get_provider_spec(provider: ProviderName | None = None) -> ProviderSpec:
    return PROVIDER_REGISTRY[provider or LLM_CONFIG.active_provider]


def get_required_api_key_name(provider: ProviderName | None = None) -> str:
    return get_provider_spec(provider).api_key_env


def has_active_api_key() -> bool:
    return bool(os.environ.get(get_required_api_key_name(), "").strip())


def get_active_model_name(provider: ProviderName | None = None) -> str:
    from_env = os.environ.get("LLM_MODEL", "").strip()
    if from_env:
        return from_env

    selected_provider = provider or LLM_CONFIG.active_provider
    spec = get_provider_spec(selected_provider)
    return spec.default_model


def get_active_embedding_model_name() -> str:
    return LLM_CONFIG.embedding_model


def get_stage_model_name(stage: LLMStage) -> str:
    env_key = STAGE_MODEL_ENV_OVERRIDES[stage]
    from_env = os.environ.get(env_key, "").strip()
    if from_env:
        return from_env
    active_model = get_active_model_name(LLM_CONFIG.active_provider)
    return active_model


def _get_api_key(provider: ProviderName | None = None) -> str:
    key_name = get_required_api_key_name(provider)
    api_key = os.environ.get(key_name, "").strip()
    if not api_key:
        raise RuntimeError(f"{key_name} not found in environment")
    return api_key


def _merge_params(overrides: dict[str, Any] | None = None) -> dict[str, Any]:
    params = {
        "temperature": LLM_CONFIG.temperature,
        "max_tokens": min(LLM_CONFIG.max_tokens, DEFAULT_MAX_TOKENS),
        "top_p": LLM_CONFIG.top_p,
        "stream": LLM_CONFIG.stream,
    }
    if overrides:
        params.update({k: v for k, v in overrides.items() if v is not None})
    try:
        params["max_tokens"] = min(int(params.get("max_tokens", DEFAULT_MAX_TOKENS)), DEFAULT_MAX_TOKENS)
    except Exception:
        params["max_tokens"] = DEFAULT_MAX_TOKENS
    return params


def _build_headers(spec: ProviderSpec, api_key: str) -> dict[str, str]:
    if spec.api_style == "anthropic_messages":
        return {
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }

    headers = {
        "content-type": "application/json",
        "authorization": f"Bearer {api_key}",
        "user-agent": "LegalT/1.0 (+https://local.legalt)",
    }
    if spec.name == "openrouter":
        headers["http-referer"] = "https://local.legalt"
        headers["x-title"] = "LegalT Contract Intelligence"
    return headers


def _http_timeout_seconds() -> float:
    raw = os.environ.get("LLM_HTTP_TIMEOUT_SECONDS", "120").strip()
    try:
        value = float(raw)
        return value if value > 0 else 60.0
    except ValueError:
        return 60.0


def _http_max_retries() -> int:
    raw = os.environ.get("LLM_HTTP_MAX_RETRIES", "3").strip()
    try:
        value = int(raw)
        return value if value >= 0 else 2
    except ValueError:
        return 2


def _http_retry_delay_seconds() -> float:
    raw = os.environ.get("LLM_HTTP_RETRY_DELAY_SECONDS", "1").strip()
    try:
        value = float(raw)
        return value if value > 0 else 1.0
    except ValueError:
        return 1.0


def build_llm_request(
    messages: list[dict[str, Any]],
    *,
    system: str | None = None,
    model: str | None = None,
    overrides: dict[str, Any] | None = None,
    provider: ProviderName | None = None,
) -> dict[str, Any]:
    spec = get_provider_spec(provider)
    api_key = _get_api_key(spec.name)
    merged = _merge_params(overrides)
    selected_model = model or get_active_model_name(spec.name) or spec.default_model
    headers = _build_headers(spec, api_key)

    if spec.api_style == "anthropic_messages":
        url = f"{spec.base_url.rstrip('/')}/v1/messages"
        payload: dict[str, Any] = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": merged["max_tokens"],
            "temperature": merged["temperature"],
            "top_p": merged["top_p"],
            "stream": merged["stream"],
        }
        if system:
            payload["system"] = system
    else:
        url = f"{spec.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": selected_model,
            "messages": messages if not system else [{"role": "system", "content": system}, *messages],
            "max_tokens": merged["max_tokens"],
            "temperature": merged["temperature"],
            "top_p": merged["top_p"],
            "stream": merged["stream"],
        }
        if spec.name == "gemini":
            payload["response_format"] = {"type": "json_object"}

    return {
        "provider": spec.name,
        "model": selected_model,
        "base_url": spec.base_url,
        "headers": headers,
        "payload": payload,
        "url": url,
    }


def build_embedding_request(
    inputs: list[str],
    *,
    model: str | None = None,
    provider: ProviderName | None = None,
) -> dict[str, Any]:
    spec = get_provider_spec(provider)
    if spec.api_style != "openai_chat":
        raise RuntimeError(f"Embeddings are not supported for provider '{spec.name}' in this adapter")

    api_key = _get_api_key(spec.name)
    selected_model = model or get_active_embedding_model_name()
    headers = _build_headers(spec, api_key)
    url = f"{spec.base_url.rstrip('/')}/embeddings"
    payload = {"model": selected_model, "input": inputs}

    return {
        "provider": spec.name,
        "model": selected_model,
        "base_url": spec.base_url,
        "headers": headers,
        "payload": payload,
        "url": url,
    }


def _extract_text_from_response(provider: ProviderName, response_data: dict[str, Any]) -> str:
    if provider == "anthropic":
        content = response_data.get("content") or []
        if content and isinstance(content, list):
            first = content[0]
            if isinstance(first, dict):
                return str(first.get("text", ""))
        return ""

    choices = response_data.get("choices") or []
    if choices and isinstance(choices, list):
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message", {})
            if isinstance(message, dict):
                content = message.get("content", "")
                if isinstance(content, str):
                    return content
                if isinstance(content, list):
                    text_parts: list[str] = []
                    for part in content:
                        if isinstance(part, dict):
                            text = part.get("text")
                            if text:
                                text_parts.append(str(text))
                    if text_parts:
                        return "".join(text_parts)
                reasoning = message.get("reasoning")
                if reasoning:
                    return str(reasoning)
                tool_calls = message.get("tool_calls")
                if tool_calls:
                    return json.dumps(tool_calls)
            text = first.get("text")
            if text:
                return str(text)
    return ""


def _model_fallback_candidates(provider: ProviderName, model: str) -> list[str]:
    fallback_raw = os.environ.get("LLM_MODEL_FALLBACKS", "").strip()
    fallbacks: list[str] = []

    if fallback_raw:
        fallbacks.extend([candidate.strip() for candidate in fallback_raw.split(",") if candidate.strip()])
    elif provider == "openrouter":
        # Intentionally avoid paid-model defaults.
        # Users can opt in explicitly via LLM_MODEL_FALLBACKS.
        fallbacks.extend([])

    ordered: list[str] = []
    for candidate in [model, *fallbacks]:
        if candidate and candidate not in ordered:
            ordered.append(candidate)
    return ordered


class _MessagesAdapter:
    def __init__(self, parent: "UnifiedLLMClient") -> None:
        self._parent = parent

    def create(
        self,
        *,
        model: str,
        max_tokens: int,
        temperature: float,
        messages: list[dict[str, Any]],
        system: str | None = None,
        top_p: float | None = None,
        stream: bool | None = None,
    ) -> UnifiedMessageResponse:
        if self._parent.provider == "gemini" and ENABLE_RATE_LIMITING:
            estimated_tokens = max_tokens + (len(str(messages)) // 4)
            try:
                GEMINI_RATE_LIMITER.acquire(estimated_tokens)
            except RuntimeError as exc:
                if "Daily Gemini request limit" in str(exc):
                    print("[STOP] Gemini limit reached safely")
                    raise SystemExit(0)
                raise

        candidates = _model_fallback_candidates(self._parent.provider, model)
        max_retries = _http_max_retries()
        retry_delay = _http_retry_delay_seconds()
        timeout_seconds = _http_timeout_seconds()
        last_error: Exception | None = None

        for candidate_index, candidate_model in enumerate(candidates):
            req = build_llm_request(
                messages,
                system=system,
                model=candidate_model,
                overrides={
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "top_p": top_p,
                    "stream": stream,
                },
                provider=self._parent.provider,
            )

            body = json.dumps(req["payload"]).encode("utf-8")
            http_request = request.Request(req["url"], data=body, headers=req["headers"], method="POST")

            for attempt in range(max_retries + 1):
                try:
                    with request.urlopen(http_request, timeout=timeout_seconds) as response:
                        raw = response.read().decode("utf-8")
                    response_data = json.loads(raw)
                    text = _extract_text_from_response(req["provider"], response_data)
                    if text.strip():
                        if candidate_index > 0:
                            print(f"[LLM MODEL FALLBACK] {model} -> {candidate_model}")
                        return UnifiedMessageResponse(content=[TextBlock(text=text)], raw=response_data)

                    last_error = RuntimeError("LLM API returned an empty message body")
                    break
                except error.HTTPError as exc:
                    detail = exc.read().decode("utf-8", errors="replace")
                    last_error = RuntimeError(f"LLM API call failed ({exc.code}): {detail}")
                    if exc.code in (429, 503) and attempt < max_retries:
                        wait = retry_delay * (2**attempt) + random.uniform(0, 0.2)
                        time.sleep(wait)
                        continue
                    break
                except error.URLError as exc:
                    last_error = RuntimeError(f"LLM API call failed: {exc.reason}")
                    if attempt < max_retries:
                        time.sleep(retry_delay * (attempt + 1))
                        continue
                    break

        if last_error is not None:
            raise last_error
        raise RuntimeError("LLM API call failed after retries")


class _EmbeddingsAdapter:
    def __init__(self, parent: "UnifiedLLMClient") -> None:
        self._parent = parent

    def create(self, *, model: str, inputs: list[str]) -> UnifiedEmbeddingResponse:
        req = build_embedding_request(inputs, model=model, provider=self._parent.provider)
        body = json.dumps(req["payload"]).encode("utf-8")
        http_request = request.Request(req["url"], data=body, headers=req["headers"], method="POST")
        timeout_seconds = _http_timeout_seconds()

        try:
            with request.urlopen(http_request, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8")
        except error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Embedding API call failed ({exc.code}): {detail}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"Embedding API call failed: {exc.reason}") from exc

        response_data = json.loads(raw)
        items = response_data.get("data", [])
        if not isinstance(items, list):
            items = []
        ordered = sorted([item for item in items if isinstance(item, dict)], key=lambda item: int(item.get("index", 0)))
        vectors = [item.get("embedding", []) for item in ordered]
        return UnifiedEmbeddingResponse(embeddings=vectors, raw=response_data)


class UnifiedLLMClient:
    def __init__(self, provider: ProviderName) -> None:
        self.provider = provider
        self.messages = _MessagesAdapter(self)
        self.embeddings = _EmbeddingsAdapter(self)


def get_llm_client(provider: ProviderName | None = None) -> dict[str, Any]:
    spec = get_provider_spec(provider)
    api_key = _get_api_key(spec.name)
    template = build_llm_request(messages=[{"role": "user", "content": ""}], provider=spec.name)
    return {
        "provider": spec.name,
        "model": get_active_model_name(spec.name) or spec.default_model,
        "embedding_model": get_active_embedding_model_name(),
        "base_url": spec.base_url,
        "headers": template["headers"],
        "payload": template["payload"],
        "client": UnifiedLLMClient(spec.name),
        "api_key_env": spec.api_key_env,
        "api_key_loaded": bool(api_key),
    }


def get_embedding_vectors(
    texts: list[str],
    *,
    model: str | None = None,
    provider: ProviderName | None = None,
) -> list[list[float]]:
    if not texts:
        return []
    selected_provider = provider or LLM_CONFIG.active_provider
    try:
        client_bundle = get_llm_client(selected_provider)
        client: UnifiedLLMClient = client_bundle["client"]
        selected_model = model or get_active_embedding_model_name()
        response = client.embeddings.create(model=selected_model, inputs=texts)
        return response.embeddings
    except Exception:
        return []


@enforce_rate_limit()
def call_llm(
    system_prompt: str,
    user_message: str,
    *,
    max_tokens: int = 1200,
    temperature: float = 0.1,
    top_p: float = 1.0,
    model: str | None = None,
    provider: ProviderName | None = None,
) -> str:
    """Execute one synchronous LLM completion and return plain text content."""
    selected_provider = provider or LLM_CONFIG.active_provider
    client_bundle = get_llm_client(selected_provider)
    client: UnifiedLLMClient = client_bundle["client"]

    response = client.messages.create(
        model=model or get_active_model_name(selected_provider),
        max_tokens=max_tokens,
        temperature=temperature,
        messages=[{"role": "user", "content": user_message}],
        system=system_prompt,
        top_p=top_p,
    )
    return (response.content[0].text if response.content else "").strip()


async def call_llm_async(
    system_prompt: str,
    user_message: str,
    *,
    max_tokens: int = 1200,
    temperature: float = 0.1,
    top_p: float = 1.0,
    model: str | None = None,
    provider: ProviderName | None = None,
) -> str:
    """Async wrapper over call_llm using a worker thread to avoid loop blocking."""
    return await asyncio.to_thread(
        call_llm,
        system_prompt,
        user_message,
        max_tokens=max_tokens,
        temperature=temperature,
        top_p=top_p,
        model=model,
        provider=provider,
    )
