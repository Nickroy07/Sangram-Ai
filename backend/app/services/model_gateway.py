"""AI Provider Gateway (Developer 3) implementing IModelGatewayService.

Bridges the six friendly catalog model IDs to live provider APIs:

===========  ==================  ==========================================
Catalog ID   Provider            Wire protocol
===========  ==================  ==========================================
chatgpt      OpenAI              OpenAI-compatible chat completions (SSE)
claude       Anthropic           Messages API (SSE)
gemini       Google              Gemini streamGenerateContent (SSE)
llama        Groq                OpenAI-compatible chat completions (SSE)
mistral      Mistral AI          OpenAI-compatible chat completions (SSE)
grok         xAI                 OpenAI-compatible chat completions (SSE)
===========  ==================  ==========================================

Design rules:
- Provider keys are read from settings/environment only; never hardcoded.
- A provider without a key is *unavailable*, not silently mocked. Callers get
  a MISSING_CONFIG error so the UI can explain what is misconfigured.
- Upstream failures are translated into the platform's error taxonomy
  (TIMEOUT, RATE_LIMIT, API_FAILURE) so routers and the SSE stream can react.
- The HTTP transport is injectable, making the parsing logic unit-testable
  without network access.
"""

import asyncio
import json
import logging
import math
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional

import httpx

from app.catalog import MODELS_CATALOG
from app.core.config import Settings, get_settings
from app.core.errors import AppErrorCode, AppException, RateLimitError
from app.schemas.model import ModelProfile

logger = logging.getLogger("sangram_ai.gateway")

ANTHROPIC_VERSION = "2023-06-01"


@dataclass(frozen=True)
class ProviderSpec:
    """Everything needed to reach one catalog model at its real provider."""

    family: str
    api_model: str
    base_url: str
    api_key: str
    transport: str  # "openai" | "anthropic" | "google"
    input_usd_per_million: float
    output_usd_per_million: float


def _specs(settings: Settings) -> Dict[str, ProviderSpec]:
    """Resolves the catalog ID → provider mapping for the current settings."""
    return {
        "chatgpt": ProviderSpec(
            family="openai",
            api_model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_BASE_URL.rstrip("/"),
            api_key=settings.OPENAI_API_KEY,
            transport="openai",
            input_usd_per_million=2.50,
            output_usd_per_million=10.00,
        ),
        "claude": ProviderSpec(
            family="anthropic",
            api_model=settings.ANTHROPIC_MODEL,
            base_url=settings.ANTHROPIC_BASE_URL.rstrip("/"),
            api_key=settings.ANTHROPIC_API_KEY,
            transport="anthropic",
            input_usd_per_million=3.00,
            output_usd_per_million=15.00,
        ),
        "gemini": ProviderSpec(
            family="google",
            api_model=settings.GEMINI_MODEL,
            base_url=settings.GOOGLE_BASE_URL.rstrip("/"),
            api_key=settings.GOOGLE_API_KEY,
            transport="google",
            input_usd_per_million=0.10,
            output_usd_per_million=0.40,
        ),
        "llama": ProviderSpec(
            family="groq",
            api_model=settings.GROQ_MODEL,
            base_url=settings.GROQ_BASE_URL.rstrip("/"),
            api_key=settings.GROQ_API_KEY,
            transport="openai",
            input_usd_per_million=0.59,
            output_usd_per_million=0.79,
        ),
        "mistral": ProviderSpec(
            family="mistral",
            api_model=settings.MISTRAL_MODEL,
            base_url=settings.MISTRAL_BASE_URL.rstrip("/"),
            api_key=settings.MISTRAL_API_KEY,
            transport="openai",
            input_usd_per_million=2.00,
            output_usd_per_million=6.00,
        ),
        "grok": ProviderSpec(
            family="xai",
            api_model=settings.XAI_MODEL,
            base_url=settings.XAI_BASE_URL.rstrip("/"),
            api_key=settings.XAI_API_KEY,
            transport="openai",
            input_usd_per_million=2.00,
            output_usd_per_million=10.00,
        ),
    }


_PROVIDER_ALIASES = {
    "openai": "chatgpt",
    "chatgpt": "chatgpt",
    "anthropic": "claude",
    "claude": "claude",
    "google": "gemini",
    "gemini": "gemini",
    "meta": "llama",
    "llama": "llama",
    "groq": "llama",
    "mistral": "mistral",
    "mistral ai": "mistral",
    "xai": "grok",
    "x.ai": "grok",
    "grok": "grok",
}


def _normalise_history(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Normalises tolerant history input to {'role','content'} entries."""
    cleaned: List[Dict[str, str]] = []
    for turn in history or []:
        role = str(turn.get("role", "user")).lower()
        if role not in {"user", "assistant", "system"}:
            continue
        content = turn.get("content", turn.get("text", ""))
        if content:
            cleaned.append({"role": role, "content": str(content)})
    return cleaned


def _merge_alternating(history: List[Dict[str, str]]) -> List[Dict[str, str]]:
    """Anthropic requires alternating roles; merge consecutive same-role turns."""
    merged: List[Dict[str, str]] = []
    for turn in history:
        if merged and merged[-1]["role"] == turn["role"]:
            merged[-1]["content"] += "\n\n" + turn["content"]
        else:
            merged.append(dict(turn))
    return merged


class ModelGatewayService:
    """Live multi-provider streaming gateway."""

    def __init__(
        self,
        settings: Optional[Settings] = None,
        transport: Optional[httpx.AsyncBaseTransport] = None,
    ) -> None:
        self.settings = settings or get_settings()
        self._transport = transport
        self._specs = _specs(self.settings)

    # ------------------------------------------------------------------ helpers
    def _resolve(self, model_id: str) -> ProviderSpec:
        spec = self._specs.get((model_id or "").lower())
        if spec is None:
            raise AppException(
                code=AppErrorCode.VALIDATION_ERROR,
                message=f"Model '{model_id}' is not part of the Sangram AI catalog.",
                status_code=422,
                retryable=False,
                details={"availableModels": list(self._specs)},
            )
        return spec

    def _require_key(self, spec: ProviderSpec, model_id: str) -> None:
        if not spec.api_key.strip():
            raise AppException(
                code=AppErrorCode.MISSING_CONFIG,
                message=(
                    f"The {spec.family} provider is not configured, so '{model_id}' "
                    "cannot run. Add its API key to the backend environment."
                ),
                status_code=400,
                retryable=False,
                details={"provider": spec.family, "modelId": model_id},
            )

    def _client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            timeout=httpx.Timeout(
                self.settings.AI_REQUEST_TIMEOUT_SECONDS,
                connect=self.settings.AI_CONNECT_TIMEOUT_SECONDS,
            ),
            transport=self._transport,
        )

    async def _fail_for_status(self, response: httpx.Response, spec: ProviderSpec) -> None:
        """Maps an upstream non-2xx response onto the platform error taxonomy."""
        body = (await response.aread()).decode("utf-8", errors="replace")[:500]
        status = response.status_code
        logger.warning(
            "Provider %s returned %s: %s", spec.family, status, body.replace("\n", " ")
        )
        if status == 429:
            raise RateLimitError(
                message=f"The {spec.family} provider is rate limiting requests. Please retry shortly.",
                details={"provider": spec.family, "upstreamStatus": status},
            )
        retryable = status >= 500 or status in {408, 409}
        raise AppException(
            code=AppErrorCode.API_FAILURE,
            message=f"The {spec.family} provider rejected the request (HTTP {status}).",
            status_code=502,
            retryable=retryable,
            details={"provider": spec.family, "upstreamStatus": status},
        )

    def _map_transport_error(self, exc: Exception, spec: ProviderSpec) -> AppException:
        if isinstance(exc, (httpx.TimeoutException, asyncio.TimeoutError)):
            return AppException(
                code=AppErrorCode.TIMEOUT,
                message=f"The {spec.family} provider timed out. Please retry.",
                status_code=504,
                retryable=True,
                details={"provider": spec.family},
            )
        if isinstance(exc, httpx.HTTPError):
            return AppException(
                code=AppErrorCode.API_FAILURE,
                message=f"Could not reach the {spec.family} provider.",
                status_code=502,
                retryable=True,
                details={"provider": spec.family},
            )
        return AppException(
            code=AppErrorCode.API_FAILURE,
            message=f"The {spec.family} provider failed unexpectedly.",
            status_code=502,
            retryable=True,
            details={"provider": spec.family},
        )

    # ------------------------------------------------------------ IModelGateway
    async def stream_argument(
        self,
        model_id: str,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        """Streams text deltas from the provider that backs ``model_id``."""
        spec = self._resolve(model_id)
        self._require_key(spec, model_id)
        history = _normalise_history(conversation_history)

        try:
            if spec.transport == "anthropic":
                async for chunk in self._stream_anthropic(
                    spec, system_prompt, user_message, history, temperature, max_tokens
                ):
                    yield chunk
            elif spec.transport == "google":
                async for chunk in self._stream_google(
                    spec, system_prompt, user_message, history, temperature, max_tokens
                ):
                    yield chunk
            else:
                async for chunk in self._stream_openai_compatible(
                    spec, system_prompt, user_message, history, temperature, max_tokens
                ):
                    yield chunk
        except AppException:
            raise
        except Exception as exc:  # transport/protocol failures -> taxonomy
            raise self._map_transport_error(exc, spec) from exc

    async def _stream_openai_compatible(
        self,
        spec: ProviderSpec,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        payload = {
            "model": spec.api_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "Authorization": f"Bearer {spec.api_key}",
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        async with self._client() as client:
            async with client.stream(
                "POST", f"{spec.base_url}/chat/completions", json=payload, headers=headers
            ) as response:
                if response.status_code >= 300:
                    await self._fail_for_status(response, spec)
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        break
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    choices = event.get("choices") or []
                    if not choices:
                        continue
                    delta = choices[0].get("delta") or {}
                    text = delta.get("content")
                    if text:
                        yield text

    async def _stream_anthropic(
        self,
        spec: ProviderSpec,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        turns = _merge_alternating(
            [t for t in history if t["role"] in {"user", "assistant"}]
            + [{"role": "user", "content": user_message}]
        )
        payload = {
            "model": spec.api_model,
            "system": system_prompt,
            "messages": turns,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }
        headers = {
            "x-api-key": spec.api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
            "Accept": "text/event-stream",
        }
        async with self._client() as client:
            async with client.stream(
                "POST", f"{spec.base_url}/messages", json=payload, headers=headers
            ) as response:
                if response.status_code >= 300:
                    await self._fail_for_status(response, spec)
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    if event.get("type") == "content_block_delta":
                        delta = event.get("delta") or {}
                        text = delta.get("text")
                        if text:
                            yield text
                    elif event.get("type") == "error":
                        error = event.get("error") or {}
                        raise AppException(
                            code=AppErrorCode.API_FAILURE,
                            message=f"Anthropic stream error: {error.get('message', 'unknown error')}",
                            status_code=502,
                            retryable=True,
                            details={"provider": spec.family},
                        )

    async def _stream_google(
        self,
        spec: ProviderSpec,
        system_prompt: str,
        user_message: str,
        history: List[Dict[str, str]],
        temperature: float,
        max_tokens: int,
    ) -> AsyncGenerator[str, None]:
        contents = []
        for turn in history:
            if turn["role"] == "system":
                continue
            contents.append(
                {
                    "role": "model" if turn["role"] == "assistant" else "user",
                    "parts": [{"text": turn["content"]}],
                }
            )
        contents.append({"role": "user", "parts": [{"text": user_message}]})
        payload = {
            "systemInstruction": {"parts": [{"text": system_prompt}]},
            "contents": contents,
            "generationConfig": {
                "temperature": temperature,
                "maxOutputTokens": max_tokens,
            },
        }
        url = (
            f"{spec.base_url}/models/{spec.api_model}:streamGenerateContent"
            f"?alt=sse&key={spec.api_key}"
        )
        async with self._client() as client:
            async with client.stream(
                "POST", url, json=payload, headers={"Accept": "text/event-stream"}
            ) as response:
                if response.status_code >= 300:
                    await self._fail_for_status(response, spec)
                async for line in response.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if not data or data == "[DONE]":
                        continue
                    try:
                        event = json.loads(data)
                    except json.JSONDecodeError:
                        continue
                    for candidate in event.get("candidates") or []:
                        for part in (candidate.get("content") or {}).get("parts") or []:
                            text = part.get("text")
                            if text:
                                yield text

    async def check_provider_health(self, provider: str) -> bool:
        """Pings the provider's credentials; returns False instead of raising."""
        model_id = _PROVIDER_ALIASES.get((provider or "").strip().lower())
        if model_id is None:
            return False
        spec = self._specs[model_id]
        if not spec.api_key.strip():
            return False

        try:
            async with self._client() as client:
                if spec.transport == "google":
                    url = f"{spec.base_url}/models?key={spec.api_key}"
                    response = await client.get(url)
                elif spec.transport == "anthropic":
                    response = await client.get(
                        f"{spec.base_url}/models",
                        headers={
                            "x-api-key": spec.api_key,
                            "anthropic-version": ANTHROPIC_VERSION,
                        },
                    )
                else:
                    response = await client.get(
                        f"{spec.base_url}/models",
                        headers={"Authorization": f"Bearer {spec.api_key}"},
                    )
                return response.status_code < 300
        except httpx.HTTPError as exc:
            logger.warning("Health check for %s failed: %s", spec.family, exc)
            return False

    async def estimate_token_cost(
        self, model_id: str, input_tokens: int, estimated_output_tokens: int
    ) -> int:
        """Returns an estimated provider cost in integer USD cents (rounded up)."""
        spec = self._resolve(model_id)
        input_tokens = max(0, int(input_tokens))
        estimated_output_tokens = max(0, int(estimated_output_tokens))
        usd = (
            input_tokens * spec.input_usd_per_million
            + estimated_output_tokens * spec.output_usd_per_million
        ) / 1_000_000
        if usd <= 0:
            return 0
        return max(1, math.ceil(usd * 100))

    async def get_active_models(self) -> List[ModelProfile]:
        """Returns the catalog annotated with provider mapping and availability."""
        models: List[ModelProfile] = []
        for profile in MODELS_CATALOG:
            spec = self._specs.get(profile.id)
            models.append(
                profile.model_copy(
                    update={
                        "apiModel": spec.api_model if spec else None,
                        "is_available": bool(spec and spec.api_key.strip()),
                    }
                )
            )
        return models
