"""SSE adapter that streams persisted provider-generated battle progress."""

import asyncio
import json
from typing import AsyncGenerator, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.errors import ForbiddenError, NotFoundError
from app.db.session import get_session_factory
from app.interfaces.battles import IBattleStreamService
from app.proposals.entities import Battle


class BattleStreamService(IBattleStreamService):
    async def stream_events(
        self, battle_id: str, last_event_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> AsyncGenerator[Tuple[str, str], None]:
        sent_messages = max(0, int(last_event_id or 0))
        sent_summaries = 0
        current_round = 0
        sent_final = False
        factory = get_session_factory()
        while True:
            async with factory() as db:
                row = (await db.execute(select(Battle).where(Battle.id == battle_id).options(
                    selectinload(Battle.messages), selectinload(Battle.round_summaries)
                ))).scalar_one_or_none()
                if not row:
                    raise NotFoundError("Battle was not found.")
                if user_id and row.user_id and row.user_id != user_id:
                    raise ForbiddenError("You do not have access to this battle.")

                # Extract pure Python dictionaries inside the active session
                messages = [
                    {
                        "id": m.id,
                        "round": m.round,
                        "stage_key": m.stage_key,
                        "stage_label": m.stage_label,
                        "speaker": m.speaker,
                        "model_id": m.model_id,
                        "text": m.text or "",
                        "contention": m.contention,
                        "challenges": m.challenges,
                        "converging": m.converging,
                    }
                    for m in sorted(row.messages, key=lambda item: (item.round, 0 if item.speaker == "A" else 1))
                ]
                summaries = [
                    {
                        "round": s.round,
                        "summary": s.summary or "",
                    }
                    for s in sorted(row.round_summaries, key=lambda item: item.round)
                ]
                status = row.status
                final = row.final_answer
                error_note = row.final_answer if status == "failed" else None
                agreement = {
                    "score": row.agreement_score, "note": row.agreement_note,
                    "method": row.agreement_method,
                    "computedAt": row.agreement_computed_at.isoformat() if row.agreement_computed_at else None,
                    "demo": False,
                }
                final_turns = {m["speaker"]: m["text"] for m in messages if m["round"] == 4}

            for message in messages[sent_messages:]:
                if message["round"] != current_round:
                    current_round = message["round"]
                    yield "battle.stage", json.dumps({"round": message["round"], "stageKey": message["stage_key"]})
                yield "battle.message.start", json.dumps({
                    "messageId": message["id"], "speaker": message["speaker"],
                    "modelId": message["model_id"], "stageLabel": message["stage_label"],
                })
                text_content = message["text"]
                for start in range(0, len(text_content), 120):
                    yield "battle.message.chunk", json.dumps({"messageId": message["id"], "delta": text_content[start:start + 120]})
                yield "battle.message.done", json.dumps({
                    "messageId": message["id"], "contention": message["contention"],
                    "challenges": message["challenges"], "converging": message["converging"],
                })
                sent_messages += 1

            for summary in summaries[sent_summaries:]:
                yield "battle.round.summary", json.dumps({"round": summary["round"], "summary": summary["summary"]})
                sent_summaries += 1

            if status == "failed":
                yield "battle.error", json.dumps({"code": "API_FAILURE", "message": error_note or "Battle failed.", "retryable": True})
                yield "battle.done", json.dumps({"battleId": battle_id})
                return
            if status == "completed" and not sent_final:
                yield "battle.synthesis.start", json.dumps({"status": "synthesizing"})
                yield "battle.final", json.dumps({
                    "finalAnswer": final or "", "insights": {"a": final_turns.get("A", ""), "b": final_turns.get("B", "")}, "agreement": agreement,
                })
                yield "battle.done", json.dumps({"battleId": battle_id})
                return
            if status not in {"pending", "running"}:
                return
            await asyncio.sleep(0.35)
