"""Tests for SMS API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_contact(client: AsyncClient, staff_headers):
    """POST /api/v1/sms/contacts creates contact."""
    data = {
        "phone_number": "+15551234567",
        "first_name": "Test",
        "last_name": "Contact",
        "is_opted_in": True,
    }
    response = await client.post("/api/v1/sms/contacts", json=data, headers=staff_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["phone_number"] == "+15551234567"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_campaign(client: AsyncClient, staff_headers):
    """POST /api/v1/sms/campaigns creates campaign."""
    data = {
        "name": "Test Campaign",
        "body": "Hello {{first_name}}, this is a test message.",
        "status": "draft",
        "list_ids": [],
    }
    response = await client.post("/api/v1/sms/campaigns", json=data, headers=staff_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test Campaign"
    assert "id" in body


@pytest.mark.asyncio
async def test_opt_out(client: AsyncClient, staff_headers):
    """POST /api/v1/sms/opt-out adds phone to opt-out list."""
    data = {
        "phone": "+15559876543",
        "reason": "User requested",
    }
    response = await client.post("/api/v1/sms/opt-out", json=data, headers=staff_headers)
    assert response.status_code == 200
    body = response.json()
    assert "phone_number" in body
    assert "message" in body
