"""Database-backed saved synthesis library."""

import json
import uuid
from typing import List, Tuple

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ForbiddenError, NotFoundError, ValidationError
from app.interfaces.battles import ISavedAnswerService
from app.proposals.entities import Battle, SavedAnswer
from app.schemas.saved import SavedAnswerCreate, SavedAnswerResponse


class SavedAnswerService(ISavedAnswerService):
    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_answer(self, user_id: str, payload: SavedAnswerCreate) -> SavedAnswerResponse:
        battle = (await self.db.execute(select(Battle).where(Battle.id == payload.battleId))).scalar_one_or_none()
        if not battle:
            raise NotFoundError("The source battle was not found.")
        if battle.user_id != user_id:
            raise ForbiddenError("You cannot save another user's battle.")
        if battle.status != "completed" or not battle.final_answer:
            raise ValidationError("Only completed battles can be saved.")
        row = SavedAnswer(
            id=str(uuid.uuid4()), user_id=user_id, battle_id=battle.id,
            question=payload.question, final_answer=payload.finalAnswer,
            fighters=json.dumps(payload.fighters), notes=payload.notes,
        )
        self.db.add(row)
        await self.db.commit()
        await self.db.refresh(row)
        return self._response(row)

    async def list_saved_answers(self, user_id: str, page: int = 1, page_size: int = 20) -> Tuple[List[SavedAnswerResponse], int]:
        query = select(SavedAnswer).where(SavedAnswer.user_id == user_id).order_by(SavedAnswer.created_at.desc())
        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        rows = (await self.db.execute(query.offset((page - 1) * page_size).limit(page_size))).scalars().all()
        return [self._response(row) for row in rows], total

    async def delete_saved_answer(self, answer_id: str, user_id: str) -> bool:
        row = (await self.db.execute(select(SavedAnswer).where(SavedAnswer.id == answer_id))).scalar_one_or_none()
        if not row:
            raise NotFoundError("Saved answer was not found.")
        if row.user_id != user_id:
            raise ForbiddenError("You cannot delete another user's saved answer.")
        await self.db.delete(row)
        await self.db.commit()
        return True

    @staticmethod
    def _response(row: SavedAnswer) -> SavedAnswerResponse:
        try:
            fighters = json.loads(row.fighters)
        except (TypeError, ValueError):
            fighters = [value for value in (row.fighters or "").split(",") if value]
        return SavedAnswerResponse(
            id=row.id, userId=row.user_id, battleId=row.battle_id, question=row.question,
            finalAnswer=row.final_answer, fighters=fighters, dateSaved=row.created_at, notes=row.notes,
        )
