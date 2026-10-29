"""Unit tests for the Developer 3 AI gateway and pure debate-engine helpers."""

import json

import httpx
import pytest

from app.core.config import Settings
from app.core.errors import AppException, RateLimitError
from app.services.battle_engine import (
    build_system_prompt,
    build_turn_prompt,
    compute_agreement,
    default_archetype_for_model,
    derive_turn_metadata,
    summarize_round,
)
from app.services.model_gateway import ModelGatewayService


def _gateway(handler, **settings_overrides) -> ModelGatewayService:
    base = dict(
        ENVIRONMENT="test",
        OPENAI_API_KEY="openai-test-key",
        ANTHROPIC_API_KEY="anthropic-test-key",
        GOOGLE_API_KEY="google-test-key",
        GROQ_API_KEY="groq-test-key",
        MISTRAL_API_KEY="mistral-test-key",
        XAI_API_KEY="xai-test-key",
    )
    base.update(settings_overrides)
    return ModelGatewayService(
        settings=Settings(**base),
        transport=httpx.MockTransport(handler),
    )


async def _collect(generator):
    return "".join([chunk async for chunk in generator])


@pytest.mark.asyncio
async def test_openai_compatible_streaming_parsing():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        captured["auth"] = request.headers["authorization"]
        body = (
            'data: {"choices":[{"delta":{"content":"Hello "}}]}\n\n'
            'data: {"choices":[{"delta":{"content":"arena"}}]}\n\n'
            "data: [DONE]\n\n"
        )
        return httpx.Response(200, content=body.encode(), headers={"content-type": "text/event-stream"})

    gateway = _gateway(handler)
    text = await _collect(
        gateway.stream_argument(
            "chatgpt",
            system_prompt="system",
            user_message="user",
            conversation_history=[{"role": "assistant", "content": "earlier"}],
        )
    )
    assert text == "Hello arena"
    assert captured["path"] == "/v1/chat/completions"
    assert captured["auth"] == "Bearer openai-test-key"
    assert captured["body"]["stream"] is True
    assert captured["body"]["messages"][0] == {"role": "system", "content": "system"}
    assert captured["body"]["messages"][-1] == {"role": "user", "content": "user"}


@pytest.mark.asyncio
async def test_anthropic_streaming_parsing():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["body"] = json.loads(request.content)
        body = (
            'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"Claude "}}\n\n'
            'event: content_block_delta\ndata: {"type":"content_block_delta","delta":{"type":"text_delta","text":"speaks"}}\n\n'
            'event: message_stop\ndata: {"type":"message_stop"}\n\n'
        )
        return httpx.Response(200, content=body.encode(), headers={"content-type": "text/event-stream"})

    gateway = _gateway(handler)
    text = await _collect(
        gateway.stream_argument(
            "claude",
            system_prompt="system",
            user_message="user",
            conversation_history=[],
        )
    )
    assert text == "Claude speaks"
    assert captured["path"] == "/v1/messages"
    assert captured["body"]["system"] == "system"
    assert captured["body"]["messages"] == [{"role": "user", "content": "user"}]


@pytest.mark.asyncio
async def test_gemini_streaming_parsing():
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        captured["key"] = request.url.params.get("key")
        captured["alt"] = request.url.params.get("alt")
        body = (
            'data: {"candidates":[{"content":{"parts":[{"text":"Gemini "},{"text":"replies"}]}}]}\n\n'
            'data: {"candidates":[{"content":{"parts":[{"text":" here"}]}}]}\n\n'
        )
        return httpx.Response(200, content=body.encode(), headers={"content-type": "text/event-stream"})

    gateway = _gateway(handler)
    text = await _collect(
        gateway.stream_argument(
            "gemini",
            system_prompt="system",
            user_message="user",
            conversation_history=[],
        )
    )
    assert text == "Gemini replies here"
    assert captured["path"].endswith(":streamGenerateContent")
    assert captured["key"] == "google-test-key"
    assert captured["alt"] == "sse"


@pytest.mark.asyncio
async def test_missing_provider_key_is_config_error_not_silent_mock():
    gateway = ModelGatewayService(settings=Settings(ENVIRONMENT="test", OPENAI_API_KEY=""))
    with pytest.raises(AppException) as exc:
        await _collect(
            gateway.stream_argument("chatgpt", "s", "u", [])
        )
    assert exc.value.code.value == "MISSING_CONFIG"


@pytest.mark.asyncio
async def test_unknown_model_rejected():
    gateway = ModelGatewayService(settings=Settings(ENVIRONMENT="test"))
    with pytest.raises(AppException) as exc:
        await _collect(gateway.stream_argument("not-a-model", "s", "u", []))
    assert exc.value.code.value == "VALIDATION_ERROR"


@pytest.mark.asyncio
async def test_upstream_rate_limit_maps_to_rate_limit_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": "slow down"})

    gateway = _gateway(handler)
    with pytest.raises(RateLimitError):
        await _collect(gateway.stream_argument("chatgpt", "s", "u", []))


@pytest.mark.asyncio
async def test_cost_estimation_in_integer_cents():
    gateway = ModelGatewayService(settings=Settings(ENVIRONMENT="test"))
    # gpt-4o: $2.50 input + $10.00 output per 1M tokens => $12.50 => 1250 cents.
    assert await gateway.estimate_token_cost("chatgpt", 1_000_000, 1_000_000) == 1250
    assert await gateway.estimate_token_cost("chatgpt", 0, 0) == 0


@pytest.mark.asyncio
async def test_active_models_reflect_configured_keys():
    gateway = _gateway(lambda request: httpx.Response(200, json={}))
    models = {m.id: m for m in await gateway.get_active_models()}
    assert models["chatgpt"].apiModel == "gpt-4o"
    assert models["chatgpt"].is_available is True
    assert models["claude"].is_available is True

    unconfigured = ModelGatewayService(settings=Settings(ENVIRONMENT="test"))
    models = {m.id: m for m in await unconfigured.get_active_models()}
    assert all(m.is_available is False for m in models.values())


@pytest.mark.asyncio
async def test_provider_health_checks_credentials():
    gateway = _gateway(lambda request: httpx.Response(200, json={"data": []}))
    assert await gateway.check_provider_health("OpenAI") is True
    assert await gateway.check_provider_health("unknown-provider") is False

    failing = _gateway(lambda request: httpx.Response(401, json={"error": "bad key"}))
    assert await failing.check_provider_health("OpenAI") is False


# ---------------------------------------------------------------------------
# Pure debate engine
# ---------------------------------------------------------------------------

def _transcript():
    return [
        {"round": 1, "speaker": "A", "model_name": "ChatGPT", "text": "We should choose Python for clarity and speed.", "converging": False},
        {"round": 1, "speaker": "B", "model_name": "Claude", "text": "Go is stronger for high-throughput services and operations.", "converging": False},
        {"round": 2, "speaker": "A", "model_name": "ChatGPT", "text": "That is a fair point about throughput; I concede scale matters.", "converging": True},
        {"round": 2, "speaker": "B", "model_name": "Claude", "text": "I agree Python wins on iteration speed for early teams.", "converging": True},
        {"round": 3, "speaker": "A", "model_name": "ChatGPT", "text": "We agree on a hybrid: Python first, Go for hot paths.", "converging": True},
        {"round": 3, "speaker": "B", "model_name": "Claude", "text": "Common ground is a shared staged migration plan.", "converging": True},
        {"round": 4, "speaker": "A", "model_name": "ChatGPT", "text": "Final: start with Python and agree to revisit scale with shared metrics.", "converging": False},
        {"round": 4, "speaker": "B", "model_name": "Claude", "text": "Final: agree on Python first, with a shared Go boundary for throughput.", "converging": False},
    ]


def test_agreement_is_computed_from_transcript():
    agreement = compute_agreement(_transcript(), "ChatGPT", "Claude")
    assert agreement is not None
    assert agreement.demo is False
    assert agreement.method == "claim-graph-overlap-v1"
    assert 0 <= agreement.score <= 100
    assert "not a demo value" in agreement.note
    assert agreement.computedAt is not None


def test_turn_metadata_uses_real_transcript():
    messages = _transcript()[:2]
    metadata = derive_turn_metadata(2, "I concede that scale matters, but clarity still wins.", messages, "A")
    assert metadata["converging"] is True
    assert metadata["challenges"]
    assert "Claude" in metadata["contention"]

    opening = derive_turn_metadata(1, "My opening position is clear.", [], "A")
    assert opening["converging"] is False
    assert opening["challenges"] is None


def test_round_summary_and_prompts():
    summary = summarize_round(1, _transcript()[:2])
    assert "Opening Arguments" in summary
    assert "ChatGPT" in summary and "Claude" in summary

    archetype = default_archetype_for_model("chatgpt")
    system = build_system_prompt("ChatGPT", "A", archetype, "Claude")
    prompt = build_turn_prompt(
        "Should startups choose Python or Go?",
        "We have a small team.",
        _transcript()[:2],
        2,
        "ChatGPT",
        "Claude",
    )
    assert "Fighter A" in system
    assert "Round 2" in prompt
    assert "Should startups choose Python or Go?" in prompt
    assert "Claude (B)" in prompt
