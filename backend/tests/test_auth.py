"""
Tests for authentication endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    """Test user registration creates a new account."""
    response = await client.post(
        "/api/auth/register",
        json={"email": "newuser@example.com", "password": "securepassword123"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert "id" in data
    assert "password_hash" not in data  # Ensure password isn't returned


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Test registration fails with duplicate email."""
    # Register first user
    await client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "password123"},
    )

    # Try to register with same email
    response = await client.post(
        "/api/auth/register",
        json={"email": "duplicate@example.com", "password": "different123"},
    )
    assert response.status_code == 400
    assert "already registered" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """Test successful login returns JWT token."""
    # Register user first
    await client.post(
        "/api/auth/register",
        json={"email": "login@example.com", "password": "password123"},
    )

    # Login
    response = await client.post(
        "/api/auth/login",
        data={"username": "login@example.com", "password": "password123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Test login fails with wrong password."""
    # Register user first
    await client.post(
        "/api/auth/register",
        json={"email": "wrongpass@example.com", "password": "correctpassword"},
    )

    # Try to login with wrong password
    response = await client.post(
        "/api/auth/login",
        data={"username": "wrongpass@example.com", "password": "wrongpassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_current_user(authenticated_client):
    """Test getting current user info with valid token."""
    client, user_info = authenticated_client
    response = await client.get("/api/auth/me")
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == user_info["email"]


@pytest.mark.asyncio
async def test_unauthorized_access(client: AsyncClient):
    """Test protected endpoint returns 401 without token."""
    response = await client.get("/api/auth/me")
    assert response.status_code == 401
