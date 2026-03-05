"""Tests for orders API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_order(client: AsyncClient, auth_headers, admin_headers):
    """POST /api/v1/orders/ creates order."""
    # Create a product first (admin)
    create_resp = await client.post(
        "/api/v1/products/",
        json={"name": "Order Product", "product_type": "physical", "price": "25.00"},
        headers=admin_headers,
    )
    product_id = create_resp.json()["id"]

    order_data = {
        "items": [{"product_id": product_id, "variant_id": None, "quantity": 2}],
    }
    response = await client.post("/api/v1/orders/", json=order_data, headers=auth_headers)
    assert response.status_code == 201
    body = response.json()
    assert "id" in body
    assert body["user_id"] is not None
    assert len(body["items"]) >= 1


@pytest.mark.asyncio
async def test_list_orders(client: AsyncClient, auth_headers, admin_headers):
    """GET /api/v1/orders/ returns user's orders."""
    # Create an order first
    create_resp = await client.post(
        "/api/v1/products/",
        json={"name": "List Order Product", "product_type": "physical", "price": "10.00"},
        headers=admin_headers,
    )
    product_id = create_resp.json()["id"]

    await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": product_id, "variant_id": None, "quantity": 1}]},
        headers=auth_headers,
    )

    response = await client.get("/api/v1/orders/", headers=auth_headers)
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert body["total"] >= 1


@pytest.mark.asyncio
async def test_update_order_status(client: AsyncClient, auth_headers, admin_headers):
    """PATCH /api/v1/orders/{id}/status as admin updates status."""
    # Create product and order
    create_resp = await client.post(
        "/api/v1/products/",
        json={"name": "Status Product", "product_type": "physical", "price": "15.00"},
        headers=admin_headers,
    )
    product_id = create_resp.json()["id"]

    order_resp = await client.post(
        "/api/v1/orders/",
        json={"items": [{"product_id": product_id, "variant_id": None, "quantity": 1}]},
        headers=auth_headers,
    )
    order_id = order_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/orders/{order_id}/status",
        json={"status": "processing"},
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "processing"
