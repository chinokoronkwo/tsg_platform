from pydantic import BaseModel, Field
from datetime import datetime
from decimal import Decimal


class ProductCreate(BaseModel):
    name: str = Field(max_length=300)
    slug: str | None = None
    description: str | None = None
    short_description: str | None = None
    product_type: str = "physical"
    sku: str | None = None
    price: Decimal = Decimal("0")
    sale_price: Decimal | None = None
    stock_quantity: int | None = None
    manage_stock: bool = False
    category_ids: list[int] = []
    featured: bool = False
    billing_interval: str | None = None
    billing_period: int | None = None
    trial_days: int | None = None
    signup_fee: Decimal | None = None


class ProductUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    short_description: str | None = None
    price: Decimal | None = None
    sale_price: Decimal | None = None
    status: str | None = None
    stock_quantity: int | None = None
    category_ids: list[int] | None = None
    featured: bool | None = None


class ProductResponse(BaseModel):
    id: int
    name: str
    slug: str
    description: str | None
    short_description: str | None
    product_type: str
    status: str
    sku: str | None
    price: Decimal
    sale_price: Decimal | None
    stock_quantity: int | None
    stock_status: str
    featured: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class ProductListResponse(BaseModel):
    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


class CartItem(BaseModel):
    product_id: int
    variant_id: int | None = None
    quantity: int = Field(ge=1, default=1)


class CartResponse(BaseModel):
    items: list[dict]
    subtotal: Decimal
    tax: Decimal
    fees: Decimal
    total: Decimal


class CheckoutRequest(BaseModel):
    items: list[CartItem]
    billing_address: dict | None = None
    shipping_address: dict | None = None
    coupon_code: str | None = None
    use_wallet: bool = False
    customer_note: str | None = None


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    subtotal: Decimal
    tax_total: Decimal
    discount_total: Decimal
    fee_total: Decimal
    total: Decimal
    items: list[dict]
    created_at: datetime

    model_config = {"from_attributes": True}


class SubscriptionResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    status: str
    current_period_start: datetime | None
    current_period_end: datetime | None
    cancel_at_period_end: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class MembershipPlanCreate(BaseModel):
    name: str
    tier: str
    price: Decimal
    description: str | None = None
    features_json: dict | None = None


class MembershipPlanResponse(BaseModel):
    id: int
    name: str
    slug: str
    tier: str
    price: Decimal
    description: str | None
    features_json: dict | None
    is_active: bool

    model_config = {"from_attributes": True}


class MembershipResponse(BaseModel):
    id: int
    user_id: int
    plan_id: int
    status: str
    starts_at: datetime
    expires_at: datetime | None
    plan: MembershipPlanResponse | None = None

    model_config = {"from_attributes": True}


class WalletResponse(BaseModel):
    balance: Decimal
    allow_negative: bool
    transactions: list[dict] = []


class WalletBalanceResponse(BaseModel):
    balance: Decimal
    allow_negative: bool


class WalletTransactionResponse(BaseModel):
    id: int
    amount: Decimal
    balance_after: Decimal
    transaction_type: str
    description: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WalletTransactionCreate(BaseModel):
    amount: Decimal
    transaction_type: str = Field(pattern="^(credit|debit)$")
    description: str | None = None


class BulkUpdateItem(BaseModel):
    product_id: int
    status: str | None = None
    price: Decimal | None = None
    sale_price: Decimal | None = None


class BulkUpdateRequest(BaseModel):
    items: list[BulkUpdateItem]


class OrderStatusUpdate(BaseModel):
    status: str


class RefundRequest(BaseModel):
    amount: Decimal | None = None
    reason: str | None = None


class CreditWalletRequest(BaseModel):
    user_id: int
    amount: Decimal = Field(gt=0)
    reason: str | None = None


class DebitWalletRequest(BaseModel):
    user_id: int
    amount: Decimal = Field(gt=0)
    reason: str | None = None


class TopUpRequest(BaseModel):
    amount: Decimal = Field(gt=0)


class AssignMembershipRequest(BaseModel):
    user_id: int
    plan_id: int
