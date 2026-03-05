"""Tests for auth API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_success(client: AsyncClient):
    """POST /api/v1/auth/register returns 201 with tokens."""
    data = {
        "email": "newuser@example.com",
        "password": "SecurePass123!",
        "first_name": "New",
        "last_name": "User",
    }
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 201
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body
    assert body["token_type"] == "bearer"
    assert "expires_in" in body


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    """Register with existing email returns 409."""
    # First create a user via register
    data = {
        "email": "duplicate@example.com",
        "password": "SecurePass123!",
        "first_name": "First",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=data)

    # Try to register again with same email
    response = await client.post("/api/v1/auth/register", json=data)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    """POST /api/v1/auth/login returns 200 with tokens."""
    # Create user first
    reg_data = {
        "email": "loginuser@example.com",
        "password": "LoginPass123!",
        "first_name": "Login",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=reg_data)

    login_data = {"email": "loginuser@example.com", "password": "LoginPass123!"}
    response = await client.post("/api/v1/auth/login", json=login_data)
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    """Login with wrong password returns 401."""
    reg_data = {
        "email": "wrongpass@example.com",
        "password": "CorrectPass123!",
        "first_name": "Test",
        "last_name": "User",
    }
    await client.post("/api/v1/auth/register", json=reg_data)

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrongpass@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    """POST /api/v1/auth/refresh returns new tokens."""
    reg_data = {
        "email": "refreshuser@example.com",
        "password": "RefreshPass123!",
        "first_name": "Refresh",
        "last_name": "User",
    }
    reg_response = await client.post("/api/v1/auth/register", json=reg_data)
    refresh_token = reg_response.json()["refresh_token"]

    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert response.status_code == 200
    body = response.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_me_authenticated(client: AsyncClient, auth_headers):
    """GET /api/v1/auth/me returns user info when authenticated."""
    response = await client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert body["email"] == "testuser@example.com"
    assert "roles" in body
    assert "id" in body


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    """GET /api/v1/auth/me returns 401 when not authenticated."""
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
