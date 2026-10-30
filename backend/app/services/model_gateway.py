"""Server-side model provider gateway. No provider credential is sent to clients."""

import logging
from typing import List

import httpx

from app.core.config import get_settings
from app.core.errors import AppErrorCode, AppException, ValidationError
from app.schemas.model import ModelProfile

logger = logging.getLogger(__name__)

MODEL_MAP = {
    "chatgpt": ("openai", "gpt-4o-mini"),
    "gemini": ("google", "gemini-3.5-flash"),
    "claude": ("anthropic", "claude-3-5-haiku-latest"),
    "llama": ("groq", "llama-3.3-70b-versatile"),
    "mistral": ("mistral", "mistral-small-latest"),
    "grok": ("xai", "grok-3-mini"),
}

KEY_ATTR = {
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "groq": "GROQ_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "xai": "XAI_API_KEY",
}


class ModelGatewayService:
    """Gateway for supported provider chat APIs, supporting official SDKs and HTTP clients."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def provider_for(self, model_id: str) -> tuple[str, str, str]:
        model = MODEL_MAP.get(model_id)
        if not model:
            raise ValidationError(f"Unsupported model '{model_id}'. Choose a model in the catalog.")
        provider, api_model = model
        if model_id == "gemini":
            api_model = self.settings.GEMINI_MODEL or api_model

        # OpenRouter smart routing for frontier combatants
        if self.settings.OPENROUTER_API_KEY:
            if model_id == "chatgpt":
                return "openrouter", "openai/gpt-4o-mini", self.settings.OPENROUTER_API_KEY
            if model_id == "llama" and not getattr(self.settings, "GROQ_API_KEY", ""):
                return "openrouter", "meta-llama/llama-3.3-70b-instruct", self.settings.OPENROUTER_API_KEY

        key = getattr(self.settings, KEY_ATTR[provider])
        if not key:
            raise ValidationError(
                f"{provider.title()} is not configured. Add {KEY_ATTR[provider]} to the backend environment.",
                details={"modelId": model_id, "provider": provider, "configuration": KEY_ATTR[provider]},
            )
        return provider, api_model, key

    async def get_active_models(self) -> List[ModelProfile]:
        # Import at call time to avoid a module initialization cycle.
        from app.api.v1.models import MODELS_CATALOG

        result = []
        for model in MODELS_CATALOG:
            provider, api_model = MODEL_MAP[model.id]
            if model.id == "gemini":
                api_model = self.settings.GEMINI_MODEL or api_model
            configured = bool(getattr(self.settings, KEY_ATTR[provider]))
            if self.settings.OPENROUTER_API_KEY:
                if model.id == "chatgpt":
                    configured = True
                    api_model = "gpt-4o-mini"
                elif model.id == "llama" and not bool(getattr(self.settings, KEY_ATTR[provider])):
                    configured = True
                    api_model = "llama-3.3-70b"
            result.append(
                model.model_copy(
                    update={"apiModel": api_model, "modelLabel": api_model, "is_available": configured}
                )
            )
        return result

    async def _complete_gemini(
        self, api_model: str, key: str, system_prompt: str, prompt: str
    ) -> str:
        """Call Google Gemini using the official google-genai SDK, with HTTP fallback."""
        try:
            from google import genai
            from google.genai import errors as genai_errors
            from google.genai import types

            client = genai.Client(api_key=key)
            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                temperature=0.6,
                max_output_tokens=1200,
            )
            response = await client.aio.models.generate_content(
                model=api_model,
                contents=prompt,
                config=config,
            )
            text = response.text or ""
            if text and text.strip():
                return text.strip()
            raise AppException(
                code=AppErrorCode.EMPTY_RESPONSE,
                message="Google Gemini returned an empty response.",
                status_code=502,
                retryable=True,
            )
        except genai_errors.APIError as exc:
            status = exc.code or 502
            raw_msg = exc.message or "Google Gemini provider failure."
            logger.warning("Gemini API error (status %s): %s", status, raw_msg)
            if status == 429:
                raise AppException(
                    code=AppErrorCode.RATE_LIMIT,
                    message=f"Gemini rate limit or quota exhausted: {raw_msg}",
                    status_code=429,
                    retryable=True,
                    details={"provider": "google", "model": api_model, "providerStatus": 429},
                ) from exc
            elif status in (400, 401, 403):
                raise AppException(
                    code=AppErrorCode.AUTH_FAILED if status in (401, 403) else AppErrorCode.VALIDATION_ERROR,
                    message=f"Gemini authentication or request rejected: {raw_msg}",
                    status_code=status,
                    retryable=False,
                    details={"provider": "google", "model": api_model, "providerStatus": status},
                ) from exc
            elif status == 404:
                raise AppException(
                    code=AppErrorCode.NOT_FOUND,
                    message=f"Gemini model '{api_model}' not found or no longer available: {raw_msg}",
                    status_code=404,
                    retryable=False,
                    details={"provider": "google", "model": api_model, "providerStatus": 404},
                ) from exc
            elif status == 503:
                if api_model != "gemini-3.5-flash-lite":
                    try:
                        logger.info("Retrying Gemini with fallback gemini-3.5-flash-lite")
                        res = await client.aio.models.generate_content(
                            model="gemini-3.5-flash-lite",
                            contents=prompt,
                            config=config,
                        )
                        fallback_text = res.text or ""
                        if fallback_text and fallback_text.strip():
                            return fallback_text.strip()
                    except Exception as fallback_exc:
                        logger.warning("Gemini fallback also failed: %s", fallback_exc)
                raise AppException(
                    code=AppErrorCode.SERVICE_UNAVAILABLE,
                    message=f"Gemini is temporarily experiencing high demand: {raw_msg}",
                    status_code=503,
                    retryable=True,
                    details={"provider": "google", "model": api_model, "providerStatus": 503},
                ) from exc
            else:
                raise AppException(
                    code=AppErrorCode.API_FAILURE,
                    message=f"Gemini provider error ({status}): {raw_msg}",
                    status_code=502,
                    retryable=True,
                    details={"provider": "google", "model": api_model, "providerStatus": status},
                ) from exc
        except (AppException, ValidationError):
            raise
        except Exception as exc:
            logger.info("Official GenAI SDK call failed (%s), trying HTTP fallback", exc)

        # Secure HTTP fallback with x-goog-api-key header (never in query params)
        timeout = httpx.Timeout(90, connect=10)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                response = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{api_model}:generateContent",
                    headers={"x-goog-api-key": key},
                    json={
                        "system_instruction": {"parts": [{"text": system_prompt}]},
                        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
                        "generationConfig": {"temperature": 0.6, "maxOutputTokens": 1200},
                    },
                )
                data = response.json()
                response.raise_for_status()
                text = "\n".join(part.get("text", "") for part in data["candidates"][0]["content"]["parts"])
                if text and text.strip():
                    return text.strip()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                err_msg = exc.response.text[:200]
                code = AppErrorCode.RATE_LIMIT if status == 429 else AppErrorCode.API_FAILURE
                raise AppException(
                    code=code,
                    message=f"Gemini request failed ({status}): {err_msg}",
                    status_code=429 if status == 429 else 502,
                    retryable=status in (429, 503),
                    details={"provider": "google", "model": api_model, "providerStatus": status},
                ) from exc
            except httpx.TimeoutException as exc:
                raise AppException(
                    code=AppErrorCode.TIMEOUT,
                    message="Google Gemini timed out. Retry the battle.",
                    status_code=504,
                    retryable=True,
                ) from exc

        raise AppException(
            code=AppErrorCode.EMPTY_RESPONSE,
            message="Google Gemini returned an empty response.",
            status_code=502,
            retryable=True,
        )

    async def complete(self, model_id: str, system_prompt: str, user_message: str, history: str = "") -> str:
        provider, api_model, key = self.provider_for(model_id)
        prompt = f"{history}\n\n{user_message}" if history else user_message

        if provider == "google":
            return await self._complete_gemini(api_model, key, system_prompt, prompt)

        timeout = httpx.Timeout(90, connect=10)
        async with httpx.AsyncClient(timeout=timeout) as client:
            try:
                if provider in {"openai", "groq", "mistral", "xai", "openrouter"}:
                    base = {
                        "openai": "https://api.openai.com/v1/chat/completions",
                        "openrouter": "https://openrouter.ai/api/v1/chat/completions",
                        "groq": "https://api.groq.com/openai/v1/chat/completions",
                        "mistral": "https://api.mistral.ai/v1/chat/completions",
                        "xai": "https://api.x.ai/v1/chat/completions",
                    }[provider]
                    headers = {"Authorization": f"Bearer {key}"}
                    if provider == "openrouter":
                        headers["HTTP-Referer"] = "https://sangramai.tech"
                        headers["X-Title"] = "Sangram AI"
                    response = await client.post(
                        base,
                        headers=headers,
                        json={
                            "model": api_model,
                            "temperature": 0.6,
                            "max_tokens": 1200,
                            "messages": [
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": prompt},
                            ],
                        },
                    )
                    data = response.json()
                    response.raise_for_status()
                    text = data["choices"][0]["message"]["content"]
                elif provider == "anthropic":
                    response = await client.post(
                        "https://api.anthropic.com/v1/messages",
                        headers={"x-api-key": key, "anthropic-version": "2023-06-01"},
                        json={
                            "model": api_model,
                            "max_tokens": 1200,
                            "temperature": 0.6,
                            "system": system_prompt,
                            "messages": [{"role": "user", "content": prompt}],
                        },
                    )
                    data = response.json()
                    response.raise_for_status()
                    text = "\n".join(item.get("text", "") for item in data.get("content", []))
                else:
                    raise ValidationError(f"Unknown provider: {provider}")
            except httpx.TimeoutException as exc:
                raise AppException(
                    code=AppErrorCode.TIMEOUT,
                    message=f"{provider.title()} timed out. Retry the battle.",
                    status_code=504,
                    retryable=True,
                ) from exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                message = f"{provider.title()} request failed. Check API key and quota."
                code = AppErrorCode.RATE_LIMIT if status == 429 else AppErrorCode.API_FAILURE
                raise AppException(
                    code=code,
                    message=message,
                    status_code=429 if status == 429 else 502,
                    retryable=status == 429,
                    details={"provider": provider, "providerStatus": status},
                ) from exc
            except (KeyError, IndexError, TypeError) as exc:
                raise AppException(
                    code=AppErrorCode.EMPTY_RESPONSE,
                    message="The model provider returned no usable answer.",
                    status_code=502,
                    retryable=True,
                ) from exc

        if not isinstance(text, str) or not text.strip():
            raise AppException(
                code=AppErrorCode.EMPTY_RESPONSE,
                message="The model provider returned an empty answer.",
                status_code=502,
                retryable=True,
            )
        return text.strip()
