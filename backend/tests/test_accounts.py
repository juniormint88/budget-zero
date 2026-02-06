"""
Tests for account management endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_account(authenticated_client):
    """Test creating a new account."""
    client, _ = authenticated_client
    response = await client.post(
        "/api/accounts/",
        json={
            "name": "Test Checking",
            "account_type": "checking",
            "institution": "Test Bank",
            "balance": 1000.50,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Checking"
    assert data["account_type"] == "checking"
    assert data["institution"] == "Test Bank"
    assert float(data["balance"]) == 1000.50


@pytest.mark.asyncio
async def test_list_accounts(authenticated_client):
    """Test listing user accounts."""
    client, _ = authenticated_client

    # Create two accounts
    await client.post("/api/accounts/", json={"name": "Account 1", "account_type": "checking"})
    await client.post("/api/accounts/", json={"name": "Account 2", "account_type": "savings"})

    response = await client.get("/api/accounts/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_account(authenticated_client):
    """Test getting a specific account."""
    client, _ = authenticated_client

    # Create account
    create_response = await client.post(
        "/api/accounts/",
        json={"name": "My Account", "account_type": "checking"},
    )
    account_id = create_response.json()["id"]

    # Get account
    response = await client.get(f"/api/accounts/{account_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "My Account"


@pytest.mark.asyncio
async def test_update_account(authenticated_client):
    """Test updating an account."""
    client, _ = authenticated_client

    # Create account
    create_response = await client.post(
        "/api/accounts/",
        json={"name": "Original Name", "account_type": "checking"},
    )
    account_id = create_response.json()["id"]

    # Update account
    response = await client.put(
        f"/api/accounts/{account_id}",
        json={"name": "Updated Name", "balance": 500.00},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Updated Name"
    assert float(data["balance"]) == 500.00


@pytest.mark.asyncio
async def test_delete_account(authenticated_client):
    """Test deleting an account."""
    client, _ = authenticated_client

    # Create account
    create_response = await client.post(
        "/api/accounts/",
        json={"name": "To Delete", "account_type": "checking"},
    )
    account_id = create_response.json()["id"]

    # Delete account
    response = await client.delete(f"/api/accounts/{account_id}")
    assert response.status_code == 204

    # Verify it's gone
    get_response = await client.get(f"/api/accounts/{account_id}")
    assert get_response.status_code == 404


@pytest.mark.asyncio
async def test_account_not_found(authenticated_client):
    """Test getting a non-existent account returns 404."""
    client, _ = authenticated_client
    response = await client.get("/api/accounts/99999")
    assert response.status_code == 404
