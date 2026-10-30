"""Tests for Scaffolding and 501 MODULE_NOT_IMPLEMENTED Responses.

Verifies:
1. Unimplemented routes return explicit HTTP 501 instead of fake success.
2. Protected scaffold routes still require authentication first (fail-closed).
3. Error messages clearly reference the respective developer owner.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_scaffold_route_requires_auth_before_501(async_client: AsyncClient):
    """Unauthenticated call to /api/battles fails with 401, not 501."""
    response = await async_client.post(
        "/api/battles",
        json={
            "question": "Should startups choose Python or Go for high-throughput services?",
            "modelA": "chatgpt",
            "modelB": "claude",
        },
    )
    assert response.status_code == 401
    assert response.json()["code"] == "AUTH_FAILED"


@pytest.mark.asyncio
async def test_battle_create_fails_closed_when_selected_provider_is_not_configured(auth_client: AsyncClient):
    """Battle creation reports a missing provider key instead of returning fake success."""
    response = await auth_client.post(
        "/api/battles",
        json={
            "question": "Should startups choose Python or Go for high-throughput services?",
            "modelA": "chatgpt",
            "modelB": "claude",
        },
    )
    assert response.status_code == 422
    data = response.json()
    assert data["code"] == "VALIDATION_ERROR"
    assert "not configured" in data["message"]


@pytest.mark.asyncio
async def test_scaffold_billing_checkout_returns_501(auth_client: AsyncClient):
    """Authenticated call to unintegrated billing checkout returns 501 MODULE_NOT_IMPLEMENTED."""
    response = await auth_client.post(
        "/api/billing/checkout",
        json={
            "planId": "pro",
            "interval": "monthly",
            "successUrl": "http://localhost:3000/checkout/success",
            "cancelUrl": "http://localhost:3000/checkout/cancelled",
        },
    )
    assert response.status_code == 501
    data = response.json()
    assert data["code"] == "MODULE_NOT_IMPLEMENTED"
    assert "Developer 5" in data["message"]
