"""Tests for Google Gemini API integration and Model Gateway Service."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.config import Settings
from app.core.errors import AppErrorCode, AppException, ValidationError
from app.services.model_gateway import ModelGatewayService


def test_gemini_settings_defaults():
    settings = Settings(
        SECRET_KEY="test-key-minimum-32-chars-long-for-testing!!",
        ENVIRONMENT="development",
    )
    assert hasattr(settings, "GOOGLE_API_KEY")
    assert hasattr(settings, "GEMINI_MODEL")
    assert settings.GEMINI_MODEL == "gemini-3.5-flash"


def test_gemini_model_configuration_override():
    settings = Settings(
        SECRET_KEY="test-key-minimum-32-chars-long-for-testing!!",
        ENVIRONMENT="development",
        GEMINI_MODEL="gemini-3.8-flash",
    )
    assert settings.GEMINI_MODEL == "gemini-3.8-flash"


def test_provider_for_gemini_success():
    gateway = ModelGatewayService()
    gateway.settings.GOOGLE_API_KEY = "test-api-key"
    gateway.settings.GEMINI_MODEL = "gemini-3.5-flash"

    provider, model, key = gateway.provider_for("gemini")
    assert provider == "google"
    assert model == "gemini-3.5-flash"
    assert key == "test-api-key"


def test_provider_for_gemini_missing_key():
    gateway = ModelGatewayService()
    gateway.settings.GOOGLE_API_KEY = ""

    with pytest.raises(ValidationError) as exc_info:
        gateway.provider_for("gemini")
    assert "Google is not configured" in str(exc_info.value.message)
    assert exc_info.value.details["configuration"] == "GOOGLE_API_KEY"


@pytest.mark.asyncio
async def test_get_active_models_includes_gemini():
    gateway = ModelGatewayService()
    gateway.settings.GOOGLE_API_KEY = "test-google-key"
    gateway.settings.GEMINI_MODEL = "gemini-3.5-flash"

    models = await gateway.get_active_models()
    gemini_profile = next((m for m in models if m.id == "gemini"), None)
    assert gemini_profile is not None
    assert gemini_profile.is_available is True
    assert gemini_profile.apiModel == "gemini-3.5-flash"


@pytest.mark.asyncio
async def test_gemini_sdk_completion_success():
    gateway = ModelGatewayService()
    gateway.settings.GOOGLE_API_KEY = "test-key"
    gateway.settings.GEMINI_MODEL = "gemini-3.5-flash"

    mock_response = MagicMock()
    mock_response.text = "This is a genuine response from Gemini."

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("google.genai.Client", return_value=mock_client):
        result = await gateway.complete("gemini", "System role", "What is AI arena?")
        assert result == "This is a genuine response from Gemini."


@pytest.mark.asyncio
async def test_gemini_empty_response_handling():
    gateway = ModelGatewayService()
    gateway.settings.GOOGLE_API_KEY = "test-key"

    mock_response = MagicMock()
    mock_response.text = ""

    mock_client = MagicMock()
    mock_client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    with patch("google.genai.Client", return_value=mock_client):
        with pytest.raises(AppException) as exc_info:
            await gateway.complete("gemini", "System role", "Prompt")
        assert exc_info.value.code == AppErrorCode.EMPTY_RESPONSE


@pytest.mark.asyncio
async def test_multi_model_availability_openai_and_gemini():
    gateway = ModelGatewayService()
    gateway.settings.OPENAI_API_KEY = "test-openai-key"
    gateway.settings.GOOGLE_API_KEY = "test-google-key"

    models = await gateway.get_active_models()
    model_dict = {m.id: m for m in models}

    assert model_dict["chatgpt"].is_available is True
    assert model_dict["gemini"].is_available is True
