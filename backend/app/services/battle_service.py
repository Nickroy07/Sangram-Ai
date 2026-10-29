"""Dialectic battle lifecycle service (Developer 4).

Owns creation, retrieval, history, cancellation, retry and deletion of arena
battles. Execution and SSE streaming live in app/services/battle_stream.py.
"""

import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.catalog import ARCHETYPES_CATALOG, MODELS_CATALOG
from app.core.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from app.proposals.entities import (
    Battle as BattleRow,
    BattleMessage as BattleMessageRow,
    BattleRoundSummary as BattleRoundSummaryRow,
    ShareLink,
)
from app.schemas.battle import (
    Battle,
    BattleCreateRequest,
    BattleCreateResponse,
    BattleSummaryCard,
)
from app.services.battle_engine import estimate_tokens
from app.services.battle_presenter import battle_to_schema, summary_card
from app.services.common import utcnow
from app.services.model_gateway import ModelGatewayService

ACTIVE_STATUSES = {"pending", "running"}


class BattleService:
    """Concrete IBattleService implementation."""

    def __init__(self, db: AsyncSession, gateway: ModelGatewayService) -> None:
        self.db = db
        self.gateway = gateway

    # ------------------------------------------------------------------ loading
    async def load_row(
        self,
        battle_id: str,
        user_id: Optional[str] = None,
        *,
        with_children: bool = True,
    ) -> BattleRow:
        """Loads a battle, enforcing ownership unless it has an active share link."""
        statement = select(BattleRow).where(BattleRow.id == battle_id)
        if with_children:
            statement = statement.options(
                selectinload(BattleRow.messages),
                selectinload(BattleRow.round_summaries),
            )
        row = (await self.db.execute(statement)).scalar_one_or_none()
        if row is None:
            raise NotFoundError(message="The requested battle was not found.")
        if user_id is not None and row.user_id != user_id:
            shared = (
                await self.db.execute(
                    select(ShareLink.id).where(
                        ShareLink.battle_id == battle_id,
                        ShareLink.is_active.is_(True),
                    )
                )
            ).first()
            if shared is None:
                raise ForbiddenError(message="You do not have access to this battle.")
        return row

    # --------------------------------------------------------------- validation
    def _validate_fighters(self, payload: BattleCreateRequest) -> None:
        model_ids = {profile.id for profile in MODELS_CATALOG}
        archetype_ids = {archetype.id for archetype in ARCHETYPES_CATALOG}
        if payload.modelA == payload.modelB:
            raise ValidationError(
                message="Two distinct model profiles are required to run a debate.",
                details={"modelA": payload.modelA, "modelB": payload.modelB},
            )
        unknown_models = [
            model_id
            for model_id in (payload.modelA, payload.modelB)
            if model_id not in model_ids
        ]
        unknown_archetypes = [
            archetype_id
            for archetype_id in (payload.archetypeA, payload.archetypeB)
            if archetype_id and archetype_id not in archetype_ids
        ]
        if unknown_models or unknown_archetypes:
            details = {}
            if unknown_models:
                details["unknownModels"] = unknown_models
            if unknown_archetypes:
                details["unknownArchetypes"] = unknown_archetypes
            raise ValidationError(
                message="One or more selected models or archetypes are not in the catalog.",
                details=details,
            )

    async def _estimate_cost(self, payload: BattleCreateRequest) -> Optional[int]:
        """Rough pre-run estimate: 8 turns plus a synthesis call."""
        base_input = estimate_tokens(payload.question or "") + estimate_tokens(payload.context or "")
        per_turn_input = base_input + 420  # persona, rules and growing transcript
        per_turn_output = 300
        total = 0
        try:
            for model_id in (payload.modelA, payload.modelB):
                total += await self.gateway.estimate_token_cost(
                    model_id,
                    input_tokens=per_turn_input * 8,
                    estimated_output_tokens=per_turn_output * 8,
                )
            total += await self.gateway.estimate_token_cost(
                payload.modelA,
                input_tokens=per_turn_input + 2600,
                estimated_output_tokens=450,
            )
        except Exception:
            return None
        return total or None

    # ------------------------------------------------------------ IBattleService
    async def create_battle(
        self, user_id: str, payload: BattleCreateRequest
    ) -> BattleCreateResponse:
        self._validate_fighters(payload)

        if payload.clientBattleId:
            existing = (
                await self.db.execute(
                    select(BattleRow).where(
                        BattleRow.user_id == user_id,
                        BattleRow.client_battle_id == payload.clientBattleId,
                    )
                )
            ).scalar_one_or_none()
            if existing is not None:
                return BattleCreateResponse(
                    battleId=existing.id,
                    streamUrl=f"/api/battles/{existing.id}/events",
                    estimatedCost=await self._estimate_cost(payload),
                )

        row = BattleRow(
            id=str(uuid.uuid4()),
            user_id=user_id,
            client_battle_id=payload.clientBattleId,
            status="pending",
            question=payload.question.strip(),
            context=payload.context.strip() if payload.context else None,
            model_a=payload.modelA,
            model_b=payload.modelB,
            archetype_a=payload.archetypeA,
            archetype_b=payload.archetypeB,
        )
        self.db.add(row)
        await self.db.commit()

        return BattleCreateResponse(
            battleId=row.id,
            streamUrl=f"/api/battles/{row.id}/events",
            estimatedCost=await self._estimate_cost(payload),
        )

    async def get_battle(self, battle_id: str, user_id: Optional[str] = None) -> Battle:
        row = await self.load_row(battle_id, user_id)
        return battle_to_schema(row)

    async def list_user_battles(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[BattleSummaryCard], int]:
        total = (
            await self.db.execute(
                select(func.count()).select_from(BattleRow).where(BattleRow.user_id == user_id)
            )
        ).scalar_one()
        rows = (
            await self.db.execute(
                select(BattleRow)
                .where(BattleRow.user_id == user_id)
                .options(selectinload(BattleRow.round_summaries))
                .order_by(BattleRow.created_at.desc())
                .offset((page - 1) * page_size)
                .limit(page_size)
            )
        ).scalars().all()
        return [summary_card(row) for row in rows], int(total)

    async def delete_battle(self, battle_id: str, user_id: str) -> bool:
        from app.services.battle_stream import discard_channel

        row = await self.load_row(battle_id, user_id, with_children=False)
        await self.db.delete(row)
        await self.db.commit()
        discard_channel(battle_id)
        return True

    async def cancel_battle(self, battle_id: str, user_id: str) -> bool:
        row = await self.load_row(battle_id, user_id, with_children=False)
        if row.status not in ACTIVE_STATUSES:
            return False
        row.status = "cancelled"
        row.updated_at = utcnow()
        await self.db.commit()
        return True

    async def retry_battle(self, battle_id: str, user_id: str) -> BattleCreateResponse:
        from app.services.battle_stream import discard_channel

        row = await self.load_row(battle_id, user_id, with_children=False)
        if row.status == "running":
            raise ConflictError(message="This battle is still running; cancel it before retrying.")
        await self.db.execute(
            BattleMessageRow.__table__.delete().where(BattleMessageRow.battle_id == battle_id)
        )
        await self.db.execute(
            BattleRoundSummaryRow.__table__.delete().where(
                BattleRoundSummaryRow.battle_id == battle_id
            )
        )
        row.status = "pending"
        row.final_answer = None
        row.agreement_score = None
        row.agreement_note = None
        row.agreement_method = None
        row.agreement_computed_at = None
        row.updated_at = utcnow()
        await self.db.commit()
        discard_channel(battle_id)

        estimate = await self.gateway.estimate_token_cost(
            row.model_a, input_tokens=4000, estimated_output_tokens=2400
        ) + await self.gateway.estimate_token_cost(
            row.model_b, input_tokens=4000, estimated_output_tokens=2400
        )
        return BattleCreateResponse(
            battleId=row.id,
            streamUrl=f"/api/battles/{row.id}/events",
            estimatedCost=estimate or None,
        )
