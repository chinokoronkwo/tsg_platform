from decimal import Decimal
from datetime import datetime, timezone

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from python_slugify import slugify

from ..models.commerce import (
    Product, ProductCategory, ProductVariant, ProductMedia,
    Order, OrderItem, Payment, Subscription,
    MembershipPlan, Membership, MembershipTier,
    WalletAccount, WalletTransaction,
    Coupon, PricingRule, ConditionalFee,
    product_categories_assoc,
    ProductType, ProductStatus, OrderStatus, PaymentStatus,
    SubscriptionStatus,
)
from ..schemas.commerce import (
    ProductCreate,
    ProductUpdate,
    CheckoutRequest,
    CartItem,
    MembershipPlanCreate,
)


class ProductService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_products(
        self,
        skip: int = 0,
        limit: int = 20,
        product_type: str | None = None,
        status: str | None = None,
        category_id: int | None = None,
        search: str | None = None,
    ):
        query = select(Product)

        if product_type:
            query = query.where(Product.product_type == product_type)
        if status:
            query = query.where(Product.status == status)
        if category_id:
            query = query.join(product_categories_assoc).where(
                product_categories_assoc.c.category_id == category_id
            ).distinct()
        if search:
            query = query.where(Product.name.ilike(f"%{search}%"))

        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        query = query.offset(skip).limit(limit).order_by(Product.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_product(self, product_id: int) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.variants),
                selectinload(Product.media),
                selectinload(Product.event_detail),
            )
            .where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def get_product_by_slug(self, slug: str) -> Product | None:
        result = await self.db.execute(
            select(Product)
            .options(
                selectinload(Product.categories),
                selectinload(Product.variants),
                selectinload(Product.media),
            )
            .where(Product.slug == slug)
        )
        return result.scalar_one_or_none()

    async def create_product(self, data: ProductCreate) -> Product:
        slug = data.slug or slugify(data.name)
        existing = await self.get_product_by_slug(slug)
        if existing:
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"

        product = Product(
            name=data.name,
            slug=slug,
            description=data.description,
            short_description=data.short_description,
            product_type=data.product_type,
            sku=data.sku,
            price=data.price,
            sale_price=data.sale_price,
            stock_quantity=data.stock_quantity,
            manage_stock=data.manage_stock,
            featured=data.featured,
            billing_interval=data.billing_interval,
            billing_period=data.billing_period,
            trial_days=data.trial_days,
            signup_fee=data.signup_fee,
        )

        if data.category_ids:
            cats = await self.db.execute(
                select(ProductCategory).where(ProductCategory.id.in_(data.category_ids))
            )
            product.categories = list(cats.scalars().all())

        self.db.add(product)
        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def update_product(self, product_id: int, data: ProductUpdate) -> Product | None:
        product = await self.get_product(product_id)
        if not product:
            return None

        update_data = data.model_dump(exclude_unset=True)
        category_ids = update_data.pop("category_ids", None)

        for key, value in update_data.items():
            setattr(product, key, value)

        if category_ids is not None:
            cats = await self.db.execute(
                select(ProductCategory).where(ProductCategory.id.in_(category_ids))
            )
            product.categories = list(cats.scalars().all())

        await self.db.commit()
        await self.db.refresh(product)
        return product

    async def delete_product(self, product_id: int) -> bool:
        product = await self.get_product(product_id)
        if not product:
            return False
        await self.db.delete(product)
        await self.db.commit()
        return True

    async def bulk_update(
        self,
        items: list[dict],
    ) -> list[Product]:
        """Bulk update product status and/or price. Each item: {product_id, status?, price?, sale_price?}"""
        updated = []
        for item in items:
            product_id = item.get("product_id")
            product = await self.get_product(product_id)
            if not product:
                continue
            if item.get("status") is not None:
                product.status = ProductStatus(item["status"]) if isinstance(item["status"], str) else item["status"]
            if item.get("price") is not None:
                product.price = item["price"]
            if item.get("sale_price") is not None:
                product.sale_price = item["sale_price"]
            updated.append(product)
        await self.db.commit()
        for p in updated:
            await self.db.refresh(p)
        return updated


class OrderService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_order(self, user_id: int, data: CheckoutRequest) -> Order:
        order = Order(user_id=user_id, currency="USD")
        subtotal = Decimal("0")
        items = []

        for cart_item in data.items:
            product = await self.db.get(Product, cart_item.product_id)
            if not product:
                raise ValueError(f"Product {cart_item.product_id} not found")

            price = product.sale_price or product.price
            item_total = price * cart_item.quantity

            order_item = OrderItem(
                product_id=product.id,
                variant_id=cart_item.variant_id,
                name=product.name,
                sku=product.sku,
                quantity=cart_item.quantity,
                unit_price=price,
                total=item_total,
            )
            items.append(order_item)
            subtotal += item_total

        order.subtotal = subtotal
        order.total = subtotal
        order.items = items
        order.billing_address = data.billing_address
        order.shipping_address = data.shipping_address
        order.customer_note = data.customer_note

        if data.coupon_code:
            discount = await self._apply_coupon(data.coupon_code, subtotal)
            order.discount_total = discount
            order.total = subtotal - discount

        self.db.add(order)
        await self.db.commit()
        await self.db.refresh(order)
        return order

    async def _apply_coupon(self, code: str, subtotal: Decimal) -> Decimal:
        result = await self.db.execute(
            select(Coupon).where(Coupon.code == code, Coupon.is_active == True)
        )
        coupon = result.scalar_one_or_none()
        if not coupon:
            return Decimal("0")

        if coupon.discount_type == "percentage":
            return subtotal * coupon.discount_value / 100
        return min(coupon.discount_value, subtotal)

    async def list_orders(
        self,
        user_id: int | None = None,
        skip: int = 0,
        limit: int = 20,
        status: str | None = None,
    ) -> tuple[list[Order], int]:
        query = select(Order).options(selectinload(Order.items))
        if user_id:
            query = query.where(Order.user_id == user_id)
        if status:
            query = query.where(Order.status == status)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(Order.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_order(self, order_id: int) -> Order | None:
        result = await self.db.execute(
            select(Order)
            .options(selectinload(Order.items), selectinload(Order.payments))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def update_status(self, order_id: int, new_status: str) -> Order | None:
        order = await self.get_order(order_id)
        if not order:
            return None
        order.status = new_status
        await self.db.commit()
        return order

    async def refund_order(
        self,
        order_id: int,
        amount: Decimal | None = None,
        credit_wallet: bool = True,
    ) -> Order | None:
        order = await self.get_order(order_id)
        if not order:
            return None
        if order.status == OrderStatus.REFUNDED:
            raise ValueError("Order already refunded")
        refund_amount = amount if amount is not None else order.total
        order.status = OrderStatus.REFUNDED
        if credit_wallet and refund_amount > 0:
            wallet_svc = WalletService(self.db)
            await wallet_svc.credit(
                order.user_id,
                refund_amount,
                f"Refund for order #{order_id}",
            )
        await self.db.commit()
        await self.db.refresh(order)
        return order


class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_or_create_wallet(self, user_id: int) -> WalletAccount:
        result = await self.db.execute(
            select(WalletAccount).where(WalletAccount.user_id == user_id)
        )
        wallet = result.scalar_one_or_none()
        if not wallet:
            wallet = WalletAccount(user_id=user_id, balance=Decimal("0"))
            self.db.add(wallet)
            await self.db.commit()
            await self.db.refresh(wallet)
        return wallet

    async def credit(self, user_id: int, amount: Decimal, description: str = "") -> WalletTransaction:
        wallet = await self.get_or_create_wallet(user_id)
        wallet.balance += amount
        txn = WalletTransaction(
            wallet_id=wallet.id,
            amount=amount,
            balance_after=wallet.balance,
            transaction_type="credit",
            description=description,
        )
        self.db.add(txn)
        await self.db.commit()
        await self.db.refresh(txn)
        return txn

    async def debit(self, user_id: int, amount: Decimal, description: str = "") -> WalletTransaction:
        wallet = await self.get_or_create_wallet(user_id)
        if not wallet.allow_negative and wallet.balance < amount:
            raise ValueError("Insufficient wallet balance")
        wallet.balance -= amount
        txn = WalletTransaction(
            wallet_id=wallet.id,
            amount=-amount,
            balance_after=wallet.balance,
            transaction_type="debit",
            description=description,
        )
        self.db.add(txn)
        await self.db.commit()
        await self.db.refresh(txn)
        return txn

    async def auto_topup_on_purchase(self, user_id: int, sku: str, amount: Decimal):
        """Auto-top-up wallet when specific SKU (SG-SUIT-006) is purchased."""
        if sku == "SG-SUIT-006":
            await self.credit(user_id, amount, "Auto top-up from suit purchase")

    async def get_transactions(self, user_id: int, skip: int = 0, limit: int = 20):
        wallet = await self.get_or_create_wallet(user_id)
        result = await self.db.execute(
            select(WalletTransaction)
            .where(WalletTransaction.wallet_id == wallet.id)
            .order_by(WalletTransaction.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()


class MembershipService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_plans(self):
        result = await self.db.execute(
            select(MembershipPlan).where(MembershipPlan.is_active == True).order_by(MembershipPlan.sort_order)
        )
        return result.scalars().all()

    async def get_plan(self, plan_id: int) -> MembershipPlan | None:
        return await self.db.get(MembershipPlan, plan_id)

    async def assign_membership(self, user_id: int, plan_id: int) -> Membership:
        plan = await self.get_plan(plan_id)
        if not plan:
            raise ValueError("Plan not found")
        membership = Membership(
            user_id=user_id,
            plan_id=plan_id,
            starts_at=datetime.now(timezone.utc),
        )
        self.db.add(membership)
        await self.db.commit()
        await self.db.refresh(membership)
        return membership

    async def get_user_memberships(self, user_id: int):
        result = await self.db.execute(
            select(Membership)
            .options(selectinload(Membership.plan))
            .where(Membership.user_id == user_id)
        )
        return result.scalars().all()

    async def create_plan(self, data: MembershipPlanCreate) -> MembershipPlan:
        slug = slugify(data.name)
        existing = await self.db.execute(
            select(MembershipPlan).where(MembershipPlan.slug == slug)
        )
        if existing.scalar_one_or_none():
            slug = f"{slug}-{int(datetime.now(timezone.utc).timestamp())}"
        tier = MembershipTier(data.tier) if isinstance(data.tier, str) else data.tier
        plan = MembershipPlan(
            name=data.name,
            slug=slug,
            tier=tier,
            price=data.price,
            description=data.description,
            features_json=data.features_json,
        )
        self.db.add(plan)
        await self.db.commit()
        await self.db.refresh(plan)
        return plan


class SubscriptionService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_subscriptions(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 20,
    ) -> tuple[list[Subscription], int]:
        query = select(Subscription).where(Subscription.user_id == user_id)
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0
        query = query.offset(skip).limit(limit).order_by(Subscription.created_at.desc())
        result = await self.db.execute(query)
        return result.scalars().all(), total

    async def get_subscription(self, subscription_id: int) -> Subscription | None:
        result = await self.db.execute(
            select(Subscription)
            .options(selectinload(Subscription.product))
            .where(Subscription.id == subscription_id)
        )
        return result.scalar_one_or_none()

    async def cancel(self, subscription_id: int, user_id: int) -> Subscription | None:
        sub = await self.get_subscription(subscription_id)
        if not sub or sub.user_id != user_id:
            return None
        sub.cancel_at_period_end = True
        sub.status = SubscriptionStatus.CANCELLED
        sub.cancelled_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def pause(self, subscription_id: int, user_id: int) -> Subscription | None:
        sub = await self.get_subscription(subscription_id)
        if not sub or sub.user_id != user_id:
            return None
        sub.status = SubscriptionStatus.PAUSED
        await self.db.commit()
        await self.db.refresh(sub)
        return sub

    async def resume(self, subscription_id: int, user_id: int) -> Subscription | None:
        sub = await self.get_subscription(subscription_id)
        if not sub or sub.user_id != user_id:
            return None
        sub.status = SubscriptionStatus.ACTIVE
        await self.db.commit()
        await self.db.refresh(sub)
        return sub
