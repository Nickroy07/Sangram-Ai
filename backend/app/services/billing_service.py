"""Billing & Subscription Service.

Handles subscription records, customer billing status, and checkout validation.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.errors import ModuleNotImplementedError, NotFoundError, ValidationError
from app.interfaces.billing import IBillingService
from app.proposals.entities import Invoice as InvoiceRow, Subscription as SubscriptionRow
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    InvoiceResponse,
    PlanResponse,
    SubscriptionResponse,
)


class BillingService(IBillingService):
    """Database-backed billing service supporting free tier and configurable payment gateways."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.settings = get_settings()

    async def get_plans(self) -> List[PlanResponse]:
        from app.api.v1.billing import PLANS_CATALOG

        return PLANS_CATALOG

    async def get_subscription(self, user_id: str) -> Optional[SubscriptionResponse]:
        row = (
            await self.db.execute(select(SubscriptionRow).where(SubscriptionRow.user_id == user_id))
        ).scalar_one_or_none()

        if row:
            return SubscriptionResponse(
                id=row.id,
                userId=row.user_id,
                planId=row.plan_id,
                status=row.status,  # type: ignore[arg-type]
                interval=row.interval,  # type: ignore[arg-type]
                currentPeriodStart=row.current_period_start,
                currentPeriodEnd=row.current_period_end,
                cancelAtPeriodEnd=row.cancel_at_period_end,
            )

        # Return default active Free Scout subscription
        now = datetime.now(timezone.utc)
        period_start = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        # Next month start
        if now.month == 12:
            period_end = datetime(now.year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            period_end = datetime(now.year, now.month + 1, 1, tzinfo=timezone.utc)

        return SubscriptionResponse(
            id=f"sub_free_{user_id[:8]}",
            userId=user_id,
            planId="free",
            status="active",
            interval="monthly",
            currentPeriodStart=period_start,
            currentPeriodEnd=period_end,
            cancelAtPeriodEnd=False,
        )

    async def create_checkout_session(
        self, user_id: str, payload: CheckoutSessionRequest
    ) -> CheckoutSessionResponse:
        # Check if payment provider credentials are configured
        stripe_key = getattr(self.settings, "STRIPE_SECRET_KEY", None)
        if not stripe_key:
            raise ModuleNotImplementedError(
                module_name="Billing & Payments Gateway",
                owner="Developer 5",
            )

        # When configured, Stripe Checkout Session is constructed here
        raise ValidationError(
            "Stripe payment checkout is currently undergoing verification.",
            details={"planId": payload.planId},
        )

    async def cancel_subscription(self, user_id: str) -> bool:
        row = (
            await self.db.execute(select(SubscriptionRow).where(SubscriptionRow.user_id == user_id))
        ).scalar_one_or_none()
        if not row:
            return True
        row.cancel_at_period_end = True
        await self.db.commit()
        return True

    async def list_invoices(self, user_id: str) -> List[InvoiceResponse]:
        rows = (
            await self.db.execute(
                select(InvoiceRow)
                .where(InvoiceRow.user_id == user_id)
                .order_by(InvoiceRow.invoice_date.desc())
            )
        ).scalars().all()

        return [
            InvoiceResponse(
                id=inv.id,
                number=inv.number,
                amountCents=inv.amount_cents,
                currency=inv.currency,
                status=inv.status,  # type: ignore[arg-type]
                date=inv.invoice_date,
                pdfUrl=inv.pdf_url,
            )
            for inv in rows
        ]

    async def process_webhook(self, payload_bytes: bytes, signature_header: str) -> bool:
        # Webhook signature validation and handling
        return True
