"""Usage and Quota Entitlements Service.

Provides real database-backed monthly battle telemetry and quota management.
"""

import uuid
from collections import Counter
from datetime import datetime, timezone
from typing import Dict

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import RateLimitError
from app.interfaces.billing import IUsageService
from app.proposals.entities import Battle, Subscription
from app.schemas.billing import UsageResponse


class UsageService(IUsageService):
    """Real database-backed usage tracking."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_user_usage(self, user_id: str) -> UsageResponse:
        now = datetime.now(timezone.utc)
        billing_period = now.strftime("%Y-%m")

        # Determine user tier and quota
        sub = (
            await self.db.execute(select(Subscription).where(Subscription.user_id == user_id))
        ).scalar_one_or_none()
        plan_id = sub.plan_id if sub and sub.status == "active" else "free"

        quota_map = {
            "free": 10,
            "pro": 100,
            "power": 500,
            "team": 999999,
        }
        quota_total = quota_map.get(plan_id, 10)

        # Count battles conducted this month
        start_of_month = datetime(now.year, now.month, 1, tzinfo=timezone.utc)
        query = select(Battle).where(
            Battle.user_id == user_id,
            Battle.created_at >= start_of_month,
        )
        result = await self.db.execute(query)
        battles = result.scalars().all()

        quota_used = len(battles)
        quota_remaining = max(0, quota_total - quota_used)

        # Model breakdown
        model_counts: Dict[str, int] = Counter()
        for b in battles:
            if b.model_a:
                model_counts[b.model_a] += 1
            if b.model_b:
                model_counts[b.model_b] += 1

        return UsageResponse(
            userId=user_id,
            billingPeriod=billing_period,
            quotaTotal=quota_total,
            quotaUsed=quota_used,
            quotaRemaining=quota_remaining,
            modelBreakdown=dict(model_counts),
            lastUpdated=now,
        )

    async def check_entitlement(self, user_id: str, action: str = "run_battle") -> bool:
        usage = await self.get_user_usage(user_id)
        return usage.quotaRemaining > 0

    async def reserve_quota(self, user_id: str, credits: int = 1) -> str:
        usage = await self.get_user_usage(user_id)
        if usage.quotaRemaining < credits:
            raise RateLimitError(
                f"Monthly battle quota depleted ({usage.quotaUsed}/{usage.quotaTotal}). Please upgrade your plan."
            )
        return str(uuid.uuid4())

    async def settle_quota(
        self, user_id: str, reservation_id: str, tokens_consumed: int, success: bool = True
    ) -> None:
        # Settlements persist implicitly via the created Battle rows.
        pass
