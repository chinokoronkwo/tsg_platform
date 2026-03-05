"""Products API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User
from ...services.commerce_service import ProductService
from ...schemas.commerce import (
    ProductCreate,
    ProductUpdate,
    ProductResponse,
    ProductListResponse,
    BulkUpdateRequest,
)

router = APIRouter()


def _product_to_response(product) -> ProductResponse:
    """Convert Product model to ProductResponse, handling enum serialization."""
    return ProductResponse(
        id=product.id,
        name=product.name,
        slug=product.slug,
        description=product.description,
        short_description=product.short_description,
        product_type=product.product_type.value if hasattr(product.product_type, "value") else str(product.product_type),
        status=product.status.value if hasattr(product.status, "value") else str(product.status),
        sku=product.sku,
        price=product.price,
        sale_price=product.sale_price,
        stock_quantity=product.stock_quantity,
        stock_status=product.stock_status,
        featured=product.featured,
        created_at=product.created_at,
    )


@router.get("/", response_model=ProductListResponse)
async def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    product_type: Optional[str] = None,
    status: Optional[str] = None,
    category: Optional[int] = Query(None, alias="category"),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> ProductListResponse:
    """List all products with pagination and optional filters."""
    svc = ProductService(db)
    items, total = await svc.list_products(
        skip=skip,
        limit=limit,
        product_type=product_type,
        status=status,
        category_id=category,
        search=search,
    )
    return ProductListResponse(
        items=[_product_to_response(p) for p in items],
        total=total,
        page=skip // limit + 1 if limit > 0 else 1,
        page_size=limit,
    )


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
) -> ProductResponse:
    """Get product by ID."""
    svc = ProductService(db)
    product = await svc.get_product(product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _product_to_response(product)


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    data: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> ProductResponse:
    """Create a new product (admin only)."""
    svc = ProductService(db)
    try:
        product = await svc.create_product(data)
        return _product_to_response(product)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.put("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    data: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> ProductResponse:
    """Update product details (admin only)."""
    svc = ProductService(db)
    product = await svc.update_product(product_id, data)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return _product_to_response(product)


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(
    product_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> None:
    """Delete product (admin only)."""
    svc = ProductService(db)
    deleted = await svc.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")


@router.post("/bulk-update", response_model=list[ProductResponse])
async def bulk_update_products(
    data: BulkUpdateRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> list[ProductResponse]:
    """Bulk update product status and/or price (admin only)."""
    svc = ProductService(db)
    items = [item.model_dump() for item in data.items]
    updated = await svc.bulk_update(items)
    return [_product_to_response(p) for p in updated]
