"""Tests for Support, Usage, and Billing Endpoints."""

import pytest


@pytest.mark.asyncio
async def test_contact_submission_success(client, outbox):
    payload = {
        "name": "Jane Developer",
        "email": "jane@example.com",
        "subject": "Enterprise War Room Deployment",
        "message": "We would like to discuss deploying Sangram AI across our architecture squad.",
    }
    response = await client.post("/api/support/contact", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "received" in data["message"].lower()

    # Verify email was captured in outbox
    assert len(outbox.messages) > 0
    assert "Enterprise War Room Deployment" in outbox.messages[-1]["subject"]
    assert "jane@example.com" in outbox.messages[-1]["body"]


@pytest.mark.asyncio
async def test_contact_submission_validation_error(client):
    # Short message under 10 chars
    payload = {
        "name": "J",
        "email": "not-an-email",
        "subject": "Hi",
        "message": "Short",
    }
    response = await client.post("/api/support/contact", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_usage_endpoint(auth_client):
    response = await auth_client.get("/api/usage")
    assert response.status_code == 200
    data = response.json()
    assert data["quotaTotal"] >= 10
    assert "quotaUsed" in data
    assert "quotaRemaining" in data
    assert "modelBreakdown" in data


@pytest.mark.asyncio
async def test_subscription_endpoint(auth_client):
    response = await auth_client.get("/api/billing/subscription")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "active"
    assert data["planId"] == "free"


@pytest.mark.asyncio
async def test_invoices_endpoint(auth_client):
    response = await auth_client.get("/api/billing/invoices")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
