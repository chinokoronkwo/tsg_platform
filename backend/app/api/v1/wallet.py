"""Wallet API endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...middleware.auth import get_current_user, require_admin
from ...models.user import User
from ...services.commerce_service import WalletService
from ...schemas.commerce import (
    WalletBalanceResponse,
    WalletTransactionResponse,
    CreditWalletRequest,
    DebitWalletRequest,
    TopUpRequest,
)

router = APIRouter()


@router.get("/balance", response_model=WalletBalanceResponse)
async def get_balance(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WalletBalanceResponse:
    """Get current user's wallet balance."""
    svc = WalletService(db)
    wallet = await svc.get_or_create_wallet(user.id)
    return WalletBalanceResponse(balance=wallet.balance, allow_negative=wallet.allow_negative)


@router.get("/transactions", response_model=dict)
async def list_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    """List current user's wallet transactions."""
    svc = WalletService(db)
    txns = await svc.get_transactions(user.id, skip=skip, limit=limit)
    return {
        "items": [
            WalletTransactionResponse(
                id=t.id,
                amount=t.amount,
                balance_after=t.balance_after,
                transaction_type=t.transaction_type,
                description=t.description,
                created_at=t.created_at,
            )
            for t in txns
        ],
        "total": len(txns),
        "page": skip // limit + 1 if limit > 0 else 1,
        "page_size": limit,
    }


@router.post("/credit", response_model=WalletTransactionResponse)
async def credit_wallet(
    data: CreditWalletRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> WalletTransactionResponse:
    """Credit amount to user wallet (admin only)."""
    svc = WalletService(db)
    try:
        txn = await svc.credit(
            data.user_id,
            data.amount,
            description=data.reason or "Admin credit",
        )
        return WalletTransactionResponse(
            id=txn.id,
            amount=txn.amount,
            balance_after=txn.balance_after,
            transaction_type=txn.transaction_type,
            description=txn.description,
            created_at=txn.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/debit", response_model=WalletTransactionResponse)
async def debit_wallet(
    data: DebitWalletRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_admin),
) -> WalletTransactionResponse:
    """Debit amount from user wallet (admin only)."""
    svc = WalletService(db)
    try:
        txn = await svc.debit(
            data.user_id,
            data.amount,
            description=data.reason or "Admin debit",
        )
        return WalletTransactionResponse(
            id=txn.id,
            amount=txn.amount,
            balance_after=txn.balance_after,
            transaction_type=txn.transaction_type,
            description=txn.description,
            created_at=txn.created_at,
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/top-up", response_model=WalletTransactionResponse)
async def top_up_wallet(
    data: TopUpRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> WalletTransactionResponse:
    """Top up current user's wallet via payment."""
    svc = WalletService(db)
    try:
        txn = await svc.credit(
            user.id,
            data.amount,
            description="Wallet top-up",
        )
        return WalletTransactionResponse(
            id=txn.id,
            amount=txn.amount,
            balance_after=txn.balance_after,
            transaction_type=txn.transaction_type,
            description=txn.description,
            created_at=txn.created_at,
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
