"""Tests for products API endpoints."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient):
    """GET /api/v1/products/ returns list."""
    response = await client.get("/api/v1/products/")
    assert response.status_code == 200
    body = response.json()
    assert "items" in body
    assert "total" in body
    assert isinstance(body["items"], list)


@pytest.mark.asyncio
async def test_create_product_admin(client: AsyncClient, admin_headers):
    """POST /api/v1/products/ as admin returns 201."""
    data = {
        "name": "Test Product",
        "product_type": "physical",
        "price": "29.99",
    }
    response = await client.post("/api/v1/products/", json=data, headers=admin_headers)
    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Test Product"
    assert "id" in body


@pytest.mark.asyncio
async def test_create_product_unauthorized(client: AsyncClient):
    """POST /api/v1/products/ without auth returns 401."""
    data = {
        "name": "Test Product",
        "product_type": "physical",
        "price": "29.99",
    }
    response = await client.post("/api/v1/products/", json=data)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, admin_headers):
    """GET /api/v1/products/{id} returns product."""
    # Create product first
    create_data = {"name": "Get Test Product", "product_type": "physical", "price": "19.99"}
    create_resp = await client.post("/api/v1/products/", json=create_data, headers=admin_headers)
    product_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/products/{product_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == product_id
    assert body["name"] == "Get Test Product"


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, admin_headers):
    """PUT /api/v1/products/{id} as admin updates product."""
    create_data = {"name": "Update Test Product", "product_type": "physical", "price": "9.99"}
    create_resp = await client.post("/api/v1/products/", json=create_data, headers=admin_headers)
    product_id = create_resp.json()["id"]

    update_data = {"name": "Updated Product Name", "price": "14.99"}
    response = await client.put(
        f"/api/v1/products/{product_id}",
        json=update_data,
        headers=admin_headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "Updated Product Name"


@pytest.mark.asyncio
async def test_delete_product(client: AsyncClient, admin_headers):
    """DELETE /api/v1/products/{id} as admin deletes product."""
    create_data = {"name": "Delete Test Product", "product_type": "physical", "price": "5.99"}
    create_resp = await client.post("/api/v1/products/", json=create_data, headers=admin_headers)
    product_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/products/{product_id}", headers=admin_headers)
    assert response.status_code == 204

    # Verify deleted
    get_resp = await client.get(f"/api/v1/products/{product_id}")
    assert get_resp.status_code == 404
