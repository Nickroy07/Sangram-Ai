"""Tests for Google Sign-In Authentication Flow."""

import pytest
from httpx import Response
from sqlalchemy import select

from app.db.auth_models import UserSession
from app.proposals.entities import Profile, User


@pytest.mark.asyncio
async def test_google_login_rejects_empty_payload(client):
    response = await client.post("/api/auth/google", json={})
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_google_login_invalid_token(client, monkeypatch):
    # Mock httpx returning 400 from Google tokeninfo
    async def mock_get(*args, **kwargs):
        return Response(400, json={"error_description": "Invalid Value"})

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = await client.post("/api/auth/google", json={"credential": "invalid-token-12345"})
    assert response.status_code == 401
    assert "Invalid or expired token" in response.json()["message"]


@pytest.mark.asyncio
async def test_google_login_creates_new_user_and_sets_cookies(client, db_factory, monkeypatch):
    google_email = "new_google_user@sangram.ai"
    google_name = "Arya Stark"

    async def mock_get(*args, **kwargs):
        return Response(
            200,
            json={
                "iss": "accounts.google.com",
                "aud": "",  # no specific client id configured
                "email": google_email,
                "email_verified": "true",
                "name": google_name,
                "picture": "https://example.com/photo.jpg",
                "sub": "google-uid-12345",
            },
        )

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = await client.post("/api/auth/google", json={"credential": "valid-simulated-token"})
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    # Ensure refresh_token is not leaked in body
    assert data["refresh_token"] is None
    # Ensure cookies set
    assert "sangram_session" in response.cookies

    # Verify database record
    async with db_factory() as db_session:
        user = (await db_session.execute(select(User).where(User.email == google_email))).scalar_one_or_none()
        assert user is not None
        assert user.is_verified is True
        assert user.is_active is True

        profile = (await db_session.execute(select(Profile).where(Profile.user_id == user.id))).scalar_one_or_none()
        assert profile is not None
        assert profile.name == google_name
        assert profile.avatar_url == "https://example.com/photo.jpg"


@pytest.mark.asyncio
async def test_google_login_existing_user_signs_in(client, db_factory, monkeypatch):
    # Pre-create an account
    existing_email = "preexisting@sangram.ai"
    async with db_factory() as db_session:
        u = User(email=existing_email, password_hash="dummy", is_verified=False)
        db_session.add(u)
        await db_session.flush()
        p = Profile(user_id=u.id, name="Original Name")
        db_session.add(p)
        await db_session.commit()

    async def mock_get(*args, **kwargs):
        return Response(
            200,
            json={
                "iss": "https://accounts.google.com",
                "email": existing_email,
                "email_verified": True,
                "name": "Updated Google Name",
                "sub": "google-uid-67890",
            },
        )

    monkeypatch.setattr("httpx.AsyncClient.get", mock_get)

    response = await client.post("/api/auth/google", json={"credential": "token-for-existing"})
    assert response.status_code == 200
    assert "sangram_session" in response.cookies

    # Email verified should now be True
    async with db_factory() as db_session:
        user = (await db_session.execute(select(User).where(User.email == existing_email))).scalar_one()
        assert user.is_verified is True
