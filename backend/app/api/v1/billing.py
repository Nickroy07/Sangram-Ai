"""Billing, Subscriptions, Usage, and Payment Webhook Endpoints (Developer 5 Boundary).

Implements financial contracts with integer minor units (cents).
Delegates to IBillingService and IUsageService.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Request, status

from app.api.deps import (
    get_billing_service,
    get_current_principal,
    get_usage_service,
)
from app.interfaces.billing import IBillingService, IUsageService
from app.schemas.auth import CurrentPrincipal
from app.schemas.billing import (
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    InvoiceResponse,
    PlanPricing,
    PlanResponse,
    SubscriptionResponse,
    UsageResponse,
)

router = APIRouter(tags=["Billing & Subscriptions"])

# Public plan catalog. Paid checkout and entitlements are not active yet.
PLANS_CATALOG: List[PlanResponse] = [
    PlanResponse(
        id="free",
        name="Free Scout",
        badge=None,
        description="Use current battle and account features with configured model providers.",
        pricing=PlanPricing(monthlyCents=0, yearlyCents=0, currency="USD"),
        features=["Two-model battles (two providers required)", "Account battle history", "Save completed answers"],
        monthlyBattleQuota=10,
    ),
    PlanResponse(
        id="pro",
        name="Pro Dialectic",
        badge=None,
        description="Paid catalog tier. Checkout and plan entitlements are not enabled yet.",
        pricing=PlanPricing(monthlyCents=2900, yearlyCents=29000, currency="USD"),
        features=["Subscription activation unavailable", "Usage quotas are not enforced", "Provider access depends on backend configuration"],
        monthlyBattleQuota=100,
    ),
    PlanResponse(
        id="power",
        name="Power Thinker",
        badge=None,
        description="Paid catalog tier. Checkout and plan entitlements are not enabled yet.",
        pricing=PlanPricing(monthlyCents=7900, yearlyCents=79000, currency="USD"),
        features=["Subscription activation unavailable", "Usage quotas are not enforced", "Provider access depends on backend configuration"],
        monthlyBattleQuota=500,
    ),
    PlanResponse(
        id="team",
        name="Enterprise Team",
        badge=None,
        description="Enterprise catalog tier. Team billing and workspace features are not enabled yet.",
        pricing=PlanPricing(monthlyCents=19900, yearlyCents=199000, currency="USD"),
        features=["Team workspaces are not enabled", "SAML SSO is not enabled", "Audit logs are not available"],
        monthlyBattleQuota=999999,
    ),
]


@router.get(
    "/billing/plans",
    response_model=List[PlanResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Pricing Plans",
    description="Returns available subscription plans with prices in integer minor units (cents).",
)
async def get_plans() -> List[PlanResponse]:
    """Public catalog of subscription tiers."""
    return PLANS_CATALOG


@router.get(
    "/billing/subscription",
    response_model=Optional[SubscriptionResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Customer Subscription",
    openapi_extra={"x-implementation-status": "planned", "x-owner": "developer-5"},
)
async def get_subscription(
    principal: CurrentPrincipal = Depends(get_current_principal),
    billing_service: IBillingService = Depends(get_billing_service),
) -> Optional[SubscriptionResponse]:
    """Retrieves caller subscription state. Owned by Developer 5."""
    return await billing_service.get_subscription(user_id=principal.user_id)


@router.post(
    "/billing/checkout",
    response_model=CheckoutSessionResponse,
    status_code=status.HTTP_200_OK,
    summary="Create Checkout Session",
    openapi_extra={"x-implementation-status": "planned", "x-owner": "developer-5"},
)
async def create_checkout(
    payload: CheckoutSessionRequest,
    principal: CurrentPrincipal = Depends(get_current_principal),
    billing_service: IBillingService = Depends(get_billing_service),
) -> CheckoutSessionResponse:
    """Initiates checkout session with payment provider. Owned by Developer 5."""
    return await billing_service.create_checkout_session(
        user_id=principal.user_id, payload=payload
    )


@router.post(
    "/billing/subscription/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel Subscription",
    openapi_extra={"x-implementation-status": "planned", "x-owner": "developer-5"},
)
async def cancel_subscription(
    principal: CurrentPrincipal = Depends(get_current_principal),
    billing_service: IBillingService = Depends(get_billing_service),
) -> dict:
    """Schedules subscription cancellation at period end. Owned by Developer 5."""
    success = await billing_service.cancel_subscription(user_id=principal.user_id)
    return {"success": success, "message": "Subscription scheduled for cancellation at period end."}


@router.get(
    "/billing/invoices",
    response_model=List[InvoiceResponse],
    status_code=status.HTTP_200_OK,
    summary="List Customer Invoices",
    openapi_extra={"x-implementation-status": "planned", "x-owner": "developer-5"},
)
async def list_invoices(
    principal: CurrentPrincipal = Depends(get_current_principal),
    billing_service: IBillingService = Depends(get_billing_service),
) -> List[InvoiceResponse]:
    """Retrieves customer invoices. Owned by Developer 5."""
    return await billing_service.list_invoices(user_id=principal.user_id)


@router.get(
    "/usage",
    response_model=UsageResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Usage & Quota Telemetry",
    openapi_extra={"x-implementation-status": "planned", "x-owner": "developer-5"},
)
async def get_usage(
    principal: CurrentPrincipal = Depends(get_current_principal),
    usage_service: IUsageService = Depends(get_usage_service),
) -> UsageResponse:
    """Returns caller monthly credit consumption. Owned by Developer 5."""
    return await usage_service.get_user_usage(user_id=principal.user_id)


@router.post(
    "/webhooks/payment",
    status_code=status.HTTP_200_OK,
    summary="Payment Provider Webhook Ingress",
    description="Validates cryptographic signature (e.g. Stripe-Signature) and processes payment events.",
    openapi_extra={"x-implementation-status": "planned", "x-owner": "developer-5"},
)
async def payment_webhook(
    request: Request,
    stripe_signature: Optional[str] = Header(None, alias="Stripe-Signature"),
    billing_service: IBillingService = Depends(get_billing_service),
) -> dict:
    """Webhook ingestion for payment updates. Owned by Developer 5."""
    body_bytes = await request.body()
    processed = await billing_service.process_webhook(
        payload_bytes=body_bytes, signature_header=stripe_signature or ""
    )
    return {"received": True, "processed": processed}
