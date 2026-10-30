"""Persisted, provider-backed dialectic battle orchestration."""

import asyncio
import uuid
from typing import List, Optional, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import AppException, ForbiddenError, NotFoundError, ValidationError
from app.db.session import get_session_factory
from app.interfaces.battles import IBattleService
from app.proposals.entities import Battle as BattleRow, BattleMessage as MessageRow, BattleRoundSummary
from app.schemas.battle import (
    Battle, BattleAgreement, BattleCreateRequest, BattleCreateResponse, BattleFighter,
    BattleInsights, BattleMessage, BattleSummaryCard,
)
from app.services.model_gateway import ModelGatewayService


STAGES = [(1, "opening", "Opening Arguments"), (2, "counter", "Counterarguments"),
          (3, "rebuttal", "Rebuttals"), (4, "final", "Final Positions")]


class BattleService(IBattleService):
    def __init__(self, db: AsyncSession):
        self.db = db
        self.gateway = ModelGatewayService()

    async def create_battle(self, user_id: str, payload: BattleCreateRequest) -> BattleCreateResponse:
        if payload.modelA == payload.modelB:
            raise ValidationError("Choose two different AI models for a battle.")
        # Validate the selections and credentials before recording a successful-looking run.
        self.gateway.provider_for(payload.modelA)
        self.gateway.provider_for(payload.modelB)
        if payload.clientBattleId:
            old = (await self.db.execute(select(BattleRow).where(
                BattleRow.user_id == user_id, BattleRow.client_battle_id == payload.clientBattleId
            ))).scalar_one_or_none()
            if old:
                return BattleCreateResponse(battleId=old.id, streamUrl=f"/api/battles/{old.id}/events")

        battle_id = str(uuid.uuid4())
        row = BattleRow(
            id=battle_id, user_id=user_id, client_battle_id=payload.clientBattleId,
            status="pending", question=payload.question.strip(), context=payload.context,
            model_a=payload.modelA, model_b=payload.modelB,
            archetype_a=payload.archetypeA, archetype_b=payload.archetypeB,
        )
        self.db.add(row)
        await self.db.commit()
        asyncio.create_task(self._execute(battle_id))
        return BattleCreateResponse(battleId=battle_id, streamUrl=f"/api/battles/{battle_id}/events")

    async def _execute(self, battle_id: str) -> None:
        factory = get_session_factory()
        async with factory() as db:
            row = (await db.execute(select(BattleRow).where(BattleRow.id == battle_id))).scalar_one_or_none()
            if not row:
                return
            row.status = "running"
            await db.commit()
            model_a = row.model_a
            model_b = row.model_b
            arch_a = row.archetype_a
            arch_b = row.archetype_b
            question_text = row.question
            context_text = row.context

        try:
            from app.api.v1.models import MODELS_CATALOG, ARCHETYPES_CATALOG
            catalog = {item.id: item for item in MODELS_CATALOG}
            archetypes = {item.id: item for item in ARCHETYPES_CATALOG}
            fighters = [model_a, model_b]
            ids = [arch_a, arch_b]
            histories: List[str] = []
            final_turns = ["", ""]
            for round_no, stage, label in STAGES:
                round_texts = []
                for slot, model_id in enumerate(fighters):
                    model = catalog[model_id]
                    archetype = archetypes.get(ids[slot])
                    system = (
                        "You are a participant in a rigorous multi-model debate. Be specific, candid, "
                        "and evidence-aware. Do not claim to be another model. Do not invent citations. "
                        f"Your perspective: {archetype.debateStyle if archetype else 'balanced analysis'}. "
                        "Address the question and directly engage the other participant's strongest points."
                    )
                    question = f"Question: {question_text}\nContext: {context_text or 'None provided'}\nStage: {label}."
                    if round_no == 1:
                        question += " Present your opening position, rationale, risks, and conditions."
                    elif round_no == 2:
                        question += " Challenge the prior arguments and identify the strongest counterpoint."
                    elif round_no == 3:
                        question += " Rebut the challenge; revise your position where warranted."
                    else:
                        question += " State your final position, key concessions, and practical recommendation."
                    text = await self.gateway.complete(model_id, system, question, "\n\n".join(histories))
                    challenge = histories[-1][:240] if histories and round_no > 1 else None
                    msg = MessageRow(
                        id=str(uuid.uuid4()), battle_id=battle_id, round=round_no,
                        stage_key=stage, stage_label=label, speaker="A" if slot == 0 else "B",
                        model_id=model_id, model_name=model.name, provider=model.provider,
                        model_label=model.modelLabel, text=text, challenges=challenge,
                        contention=None, converging=round_no >= 3,
                    )
                    async with factory() as db:
                        db.add(msg)
                        await db.commit()

                    histories.append(f"{model.name}: {text}")
                    round_texts.append(text)
                    if round_no == 4:
                        final_turns[slot] = text

                async with factory() as db:
                    db.add(BattleRoundSummary(
                        id=str(uuid.uuid4()), battle_id=battle_id, round=round_no,
                        summary="\n\n".join(f"{fighters[i]}: {text[:350]}" for i, text in enumerate(round_texts)),
                    ))
                    await db.commit()

            synthesis = await self.gateway.complete(
                model_a,
                "You are the neutral synthesis editor. Produce a clear, actionable answer that "
                "distinguishes agreement from unresolved disagreement. Do not invent facts or a numerical score.",
                f"Question: {question_text}\nContext: {context_text or 'None'}\n\nFinal positions:\n"
                f"{catalog[model_a].name}: {final_turns[0]}\n\n{catalog[model_b].name}: {final_turns[1]}\n\n"
                "Write the consolidated recommendation and the conditions under which each position is strongest.",
            )
            async with factory() as db:
                current = (await db.execute(select(BattleRow).where(BattleRow.id == battle_id))).scalar_one_or_none()
                if current:
                    current.final_answer = synthesis
                    current.status = "completed"
                    current.agreement_note = "No numeric agreement score is available; the backend does not fabricate one."
                    current.agreement_method = None
                    await db.commit()
        except Exception as exc:
            import logging
            logging.getLogger("sangram_ai.battles").exception("Battle execution failed for %s", battle_id)
            async with factory() as db:
                current = (await db.execute(select(BattleRow).where(BattleRow.id == battle_id))).scalar_one_or_none()
                if current:
                    current.status = "failed"
                    current.final_answer = exc.message if isinstance(exc, AppException) else "The model provider request failed. Check backend logs and provider configuration."
                    await db.commit()

    async def get_battle(self, battle_id: str, user_id: Optional[str] = None) -> Battle:
        row = (await self.db.execute(select(BattleRow).where(BattleRow.id == battle_id).options(
            selectinload(BattleRow.messages), selectinload(BattleRow.round_summaries)
        ))).scalar_one_or_none()
        if not row:
            raise NotFoundError("Battle was not found.")
        if user_id and row.user_id and row.user_id != user_id:
            raise ForbiddenError("You do not have access to this battle.")
        from app.api.v1.models import MODELS_CATALOG, ARCHETYPES_CATALOG
        models = {item.id: item for item in MODELS_CATALOG}
        archetypes = {item.id: item for item in ARCHETYPES_CATALOG}
        fighters = []
        for slot, (model_id, archetype_id) in enumerate(((row.model_a, row.archetype_a), (row.model_b, row.archetype_b))):
            model = models[model_id]
            arch = archetypes.get(archetype_id)
            fighters.append(BattleFighter(
                slot=slot, modelId=model_id, name=model.name, provider=model.provider, modelLabel=model.modelLabel,
                archetypeId=archetype_id, archetypeName=arch.name if arch else None, archetypeTag=arch.tag if arch else None,
            ))
        ordered = sorted(row.messages, key=lambda m: (m.round, 0 if m.speaker == "A" else 1))
        summaries = sorted(row.round_summaries, key=lambda s: s.round)
        final_answer = row.final_answer or ""
        return Battle(
            id=row.id, status=row.status, question=row.question, fighters=fighters,
            messages=[BattleMessage(
                id=m.id, round=m.round, stageKey=m.stage_key, stageLabel=m.stage_label, speaker=m.speaker,
                modelId=m.model_id, modelName=m.model_name, provider=m.provider, modelLabel=m.model_label,
                text=m.text, challenges=m.challenges, contention=m.contention, converging=m.converging,
                createdAt=m.created_at,
            ) for m in ordered],
            roundSummaries=[s.summary for s in summaries], finalAnswer=final_answer,
            insights=BattleInsights(a=ordered[-2].text if len(ordered) >= 2 else "", b=ordered[-1].text if ordered else ""),
            agreement=BattleAgreement(score=row.agreement_score, note=row.agreement_note,
                method=row.agreement_method, computedAt=row.agreement_computed_at, label="Agreement"),
            source="backend", createdAt=row.created_at,
        )

    async def list_user_battles(self, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[BattleSummaryCard], int]:
        query = select(BattleRow).where(BattleRow.user_id == user_id).order_by(BattleRow.created_at.desc())
        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        rows = (await self.db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return [BattleSummaryCard(
            id=row.id, title=row.question, date=row.created_at.isoformat(), models=[row.model_a, row.model_b],
            status=row.status, summary=row.final_answer or ("Battle in progress" if row.status == "running" else ""),
            consensusScore=row.agreement_score,
        ) for row in rows], total

    async def delete_battle(self, battle_id: str, user_id: str) -> bool:
        row = (await self.db.execute(select(BattleRow).where(BattleRow.id == battle_id))).scalar_one_or_none()
        if not row:
            raise NotFoundError("Battle was not found.")
        if row.user_id != user_id:
            raise ForbiddenError("You do not have access to this battle.")
        await self.db.delete(row)
        await self.db.commit()
        return True

    async def cancel_battle(self, battle_id: str, user_id: str) -> bool:
        row = (await self.db.execute(select(BattleRow).where(BattleRow.id == battle_id, BattleRow.user_id == user_id))).scalar_one_or_none()
        if not row:
            raise NotFoundError("Battle was not found.")
        if row.status in {"pending", "running"}:
            row.status = "failed"
            await self.db.commit()
        return True

    async def retry_battle(self, battle_id: str, user_id: str) -> BattleCreateResponse:
        row = (await self.db.execute(select(BattleRow).where(BattleRow.id == battle_id, BattleRow.user_id == user_id))).scalar_one_or_none()
        if not row:
            raise NotFoundError("Battle was not found.")
        return await self.create_battle(user_id, BattleCreateRequest(
            question=row.question, modelA=row.model_a, modelB=row.model_b,
            archetypeA=row.archetype_a, archetypeB=row.archetype_b, context=row.context,
        ))
