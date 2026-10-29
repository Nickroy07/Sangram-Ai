"""Dialectic battle execution and SSE event streaming (Developer 4).

Architecture
------------
* The first client to open ``GET /api/battles/{id}/events`` starts an in-process
  producer task for that battle. The producer owns its own DB session, runs the
  four-round state machine, persists every completed turn, and appends events to
  a per-battle :class:`RunChannel`.
* Any number of SSE subscribers (including reconnect attempts with
  ``Last-Event-ID``) read from that channel. A battle therefore keeps running if
  the original connection drops, and a reconnect can resume from the last event.
* Completed/failed battles with no live channel are replayed deterministically
  from the persisted transcript, so restarts do not lose finished debates.

The event vocabulary matches ``docs/API_CONVENTIONS.md`` exactly.
"""

import asyncio
import json
import logging
import uuid
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.orm import selectinload

from app.core.errors import AppErrorCode, AppException, NotFoundError
from app.proposals.entities import (
    Battle as BattleRow,
    BattleMessage as BattleMessageRow,
    BattleRoundSummary as BattleRoundSummaryRow,
)
from app.schemas.battle import (
    SSEBattleFinal,
    SSEBattleMessageChunk,
    SSEBattleMessageDone,
    SSEBattleMessageStart,
    SSEBattleRoundSummary,
    SSEBattleStage,
    SSEBattleSynthesisStart,
)
from app.services.battle_engine import (
    build_insights,
    build_synthesis_prompt,
    build_system_prompt,
    build_turn_prompt,
    compute_agreement,
    default_archetype_for_model,
    derive_turn_metadata,
    get_archetype,
    get_model_profile,
    stage_for_round,
    summarize_round,
    synthesis_system_prompt,
)
from app.services.battle_presenter import battle_to_schema
from app.services.battle_service import BattleService
from app.services.common import utcnow
from app.services.model_gateway import ModelGatewayService

logger = logging.getLogger("sangram_ai.battle")

Event = Tuple[str, str, int]
TERMINAL_STATUSES = {"completed", "failed", "cancelled"}


def _as_json(payload: Any) -> str:
    if hasattr(payload, "model_dump"):
        payload = payload.model_dump(mode="json")
    return json.dumps(payload, ensure_ascii=False, default=str)


class RunChannel:
    """Append-only event log with condition-variable subscription."""

    def __init__(self, battle_id: str) -> None:
        self.battle_id = battle_id
        self.events: List[Event] = []
        self.done = False
        self.condition = asyncio.Condition()
        self.task: Optional[asyncio.Task] = None

    async def publish(self, event_name: str, payload: Any) -> None:
        await self.publish_serialized(event_name, _as_json(payload))

    async def publish_serialized(self, event_name: str, serialized: str) -> None:
        async with self.condition:
            event_id = len(self.events) + 1
            self.events.append((event_name, serialized, event_id))
            self.condition.notify_all()

    async def close(self) -> None:
        async with self.condition:
            self.done = True
            self.condition.notify_all()


# ---------------------------------------------------------------------------
# Channel registry (single event loop: check-and-set needs no await)
# ---------------------------------------------------------------------------
_channels: Dict[str, RunChannel] = {}
_MAX_RETAINED_CHANNELS = 200


def _get_or_create_channel(battle_id: str) -> Tuple[RunChannel, bool]:
    channel = _channels.get(battle_id)
    if channel is not None:
        return channel, False
    channel = RunChannel(battle_id)
    _channels[battle_id] = channel
    # Evict the oldest finished channels to bound memory in long-lived workers.
    if len(_channels) > _MAX_RETAINED_CHANNELS:
        for key, candidate in list(_channels.items()):
            if candidate.done and key != battle_id:
                _channels.pop(key, None)
                if len(_channels) <= _MAX_RETAINED_CHANNELS:
                    break
    return channel, True


def discard_channel(battle_id: str) -> None:
    """Drops a retained run so a retried/deleted battle starts from a clean log."""
    _channels.pop(battle_id, None)


def _event(name: str, event_id: int, payload: Any) -> Event:
    return name, _as_json(payload), event_id


def _parse_last_event_id(value: Optional[str]) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


class _BattleProducer:
    """Runs one battle's four-round dialectic using its own DB session."""

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
        gateway: ModelGatewayService,
        channel: RunChannel,
    ) -> None:
        self.session_factory = session_factory
        self.gateway = gateway
        self.channel = channel

    async def run(self, battle_id: str) -> None:
        try:
            async with self.session_factory() as session:
                await self._run_with_session(session, battle_id)
        except Exception as exc:  # never leak an unhandled task exception
            logger.exception("Battle %s failed", battle_id)
            await self._mark_failed(battle_id)
            await self._publish_failure(exc)
            await self.channel.close()

    async def _mark_failed(self, battle_id: str) -> None:
        try:
            async with self.session_factory() as session:
                await session.execute(
                    update(BattleRow)
                    .where(
                        BattleRow.id == battle_id,
                        ~BattleRow.status.in_(["completed", "cancelled"]),
                    )
                    .values(status="failed", updated_at=utcnow())
                )
                await session.commit()
        except Exception:  # DB unavailable: the SSE error still explains the failure
            logger.exception("Could not mark battle %s as failed", battle_id)

    async def _publish_failure(self, exc: Exception) -> None:
        if isinstance(exc, AppException):
            code, message, retryable = exc.code.value, exc.message, exc.retryable
        else:
            code = AppErrorCode.INTERNAL_SERVER_ERROR.value
            message = "The debate engine failed unexpectedly."
            retryable = True
        await self.channel.publish(
            "battle.error",
            {"code": code, "message": message, "retryable": retryable},
        )
        await self.channel.publish(
            "battle.done", {"battleId": self.channel.battle_id, "status": "failed"}
        )

    async def _run_with_session(self, session: AsyncSession, battle_id: str) -> None:
        row = await self._load(session, battle_id)
        if row.status in TERMINAL_STATUSES:
            for name, data, _ in _replay_from_db(row):
                await self.channel.publish_serialized(name, data)
            await self.channel.close()
            return

        # Seed the live channel with anything already persisted (resume/restart).
        for name, data, _ in _replay_from_db(row, include_done=False):
            await self.channel.publish_serialized(name, data)

        row.status = "running"
        row.updated_at = utcnow()
        await session.commit()

        messages = [
            {
                "id": m.id,
                "round": m.round,
                "stage_key": m.stage_key,
                "stage_label": m.stage_label,
                "speaker": m.speaker,
                "model_id": m.model_id,
                "model_name": m.model_name,
                "provider": m.provider,
                "model_label": m.model_label,
                "text": m.text,
                "challenges": m.challenges,
                "contention": m.contention,
                "converging": m.converging,
                "created_at": m.created_at,
            }
            for m in sorted(row.messages, key=lambda m: (m.round, m.created_at, m.id))
        ]
        completed_turns = {(m["round"], m["speaker"]) for m in messages}
        seeded_rounds = {m["round"] for m in messages}
        summaries = {summary.round: summary.summary for summary in row.round_summaries}

        fighter_a = get_model_profile(row.model_a)
        fighter_b = get_model_profile(row.model_b)
        name_a = fighter_a.name if fighter_a else row.model_a
        name_b = fighter_b.name if fighter_b else row.model_b

        for round_number in range(1, 5):
            if await self._is_cancelled(session, battle_id):
                await session.rollback()
                await self.channel.publish(
                    "battle.done", {"battleId": battle_id, "status": "cancelled"}
                )
                await self.channel.close()
                return

            stage = stage_for_round(round_number)
            if round_number not in seeded_rounds:
                await self.channel.publish(
                    "battle.stage", SSEBattleStage(round=round_number, stageKey=stage.key)
                )

            for slot in ("A", "B"):
                if (round_number, slot) in completed_turns:
                    continue
                model_id = row.model_a if slot == "A" else row.model_b
                model_name = name_a if slot == "A" else name_b
                opponent_name = name_b if slot == "A" else name_a
                archetype_id = row.archetype_a if slot == "A" else row.archetype_b
                archetype = get_archetype(archetype_id) or default_archetype_for_model(model_id)

                turn = await self._generate_turn(
                    session=session,
                    battle_id=battle_id,
                    battle_question=row.question,
                    context=row.context,
                    round_number=round_number,
                    slot=slot,
                    model_id=model_id,
                    model_name=model_name,
                    opponent_name=opponent_name,
                    archetype=archetype,
                    messages=messages,
                )
                messages.append(turn)
                completed_turns.add((round_number, slot))

            round_turns = [m for m in messages if m["round"] == round_number]
            if round_number not in summaries and len(round_turns) >= 2:
                summary = summarize_round(round_number, round_turns)
                session.add(
                    BattleRoundSummaryRow(
                        id=str(uuid.uuid4()),
                        battle_id=battle_id,
                        round=round_number,
                        summary=summary,
                    )
                )
                await session.commit()
                summaries[round_number] = summary
                await self.channel.publish(
                    "battle.round.summary",
                    SSEBattleRoundSummary(round=round_number, summary=summary),
                )

        # ------------------------------------------------------------ synthesis
        await self.channel.publish(
            "battle.synthesis.start", SSEBattleSynthesisStart(status="synthesizing")
        )
        final_answer = await self._generate_synthesis(
            session=session,
            battle_id=battle_id,
            row=row,
            messages=messages,
            name_a=name_a,
            name_b=name_b,
        )

        agreement = compute_agreement(messages, name_a, name_b)
        insights = build_insights(messages, name_a, name_b)

        row.status = "completed"
        row.final_answer = final_answer
        if agreement is not None:
            row.agreement_score = agreement.score
            row.agreement_note = agreement.note
            row.agreement_method = agreement.method
            row.agreement_computed_at = agreement.computedAt
        row.updated_at = utcnow()
        await session.commit()

        await self.channel.publish(
            "battle.final",
            SSEBattleFinal(finalAnswer=final_answer, insights=insights, agreement=agreement),
        )
        await self.channel.publish(
            "battle.done",
            {"battleId": battle_id, "status": "completed", "completedAt": utcnow().isoformat()},
        )
        await self.channel.close()

    async def _load(self, session: AsyncSession, battle_id: str) -> BattleRow:
        row = (
            await session.execute(
                select(BattleRow)
                .where(BattleRow.id == battle_id)
                .options(
                    selectinload(BattleRow.messages),
                    selectinload(BattleRow.round_summaries),
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise NotFoundError(message="The requested battle was not found.")
        return row

    async def _is_cancelled(self, session: AsyncSession, battle_id: str) -> bool:
        status = (
            await session.execute(select(BattleRow.status).where(BattleRow.id == battle_id))
        ).scalar_one_or_none()
        return status in TERMINAL_STATUSES

    async def _generate_turn(
        self,
        *,
        session: AsyncSession,
        battle_id: str,
        battle_question: str,
        context: Optional[str],
        round_number: int,
        slot: str,
        model_id: str,
        model_name: str,
        opponent_name: str,
        archetype,
        messages: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        stage = stage_for_round(round_number)
        message_id = str(uuid.uuid4())
        await self.channel.publish(
            "battle.message.start",
            SSEBattleMessageStart(
                messageId=message_id,
                speaker=slot,
                modelId=model_id,
                stageLabel=stage.label,
            ),
        )

        system_prompt = build_system_prompt(model_name, slot, archetype, opponent_name)
        user_prompt = build_turn_prompt(
            question=battle_question,
            context=context,
            messages=messages,
            round_number=round_number,
            model_name=model_name,
            opponent_name=opponent_name,
        )

        parts: List[str] = []
        try:
            async for delta in self.gateway.stream_argument(
                model_id=model_id,
                system_prompt=system_prompt,
                user_message=user_prompt,
                conversation_history=[],
                temperature=0.75,
                max_tokens=700,
            ):
                if not delta:
                    continue
                parts.append(delta)
                await self.channel.publish(
                    "battle.message.chunk",
                    SSEBattleMessageChunk(messageId=message_id, delta=delta),
                )
        except AppException:
            raise

        text = "".join(parts).strip()
        if not text:
            raise AppException(
                code=AppErrorCode.EMPTY_RESPONSE,
                message=f"{model_name} returned an empty argument.",
                status_code=502,
                retryable=True,
                details={"modelId": model_id, "round": round_number},
            )

        metadata = derive_turn_metadata(round_number, text, messages, slot)
        created_at = utcnow()
        profile = get_model_profile(model_id)
        provider = profile.provider if profile else "Unknown"
        model_label = profile.modelLabel if profile else model_id
        session.add(
            BattleMessageRow(
                id=message_id,
                battle_id=battle_id,
                round=round_number,
                stage_key=stage.key,
                stage_label=stage.label,
                speaker=slot,
                model_id=model_id,
                model_name=model_name,
                provider=provider,
                model_label=model_label,
                text=text,
                challenges=metadata["challenges"],
                contention=metadata["contention"],
                converging=bool(metadata["converging"]),
                created_at=created_at,
            )
        )
        await session.commit()

        await self.channel.publish(
            "battle.message.done",
            SSEBattleMessageDone(
                messageId=message_id,
                contention=metadata["contention"],
                challenges=metadata["challenges"],
                converging=bool(metadata["converging"]),
            ),
        )

        return {
            "id": message_id,
            "round": round_number,
            "stage_key": stage.key,
            "stage_label": stage.label,
            "speaker": slot,
            "model_id": model_id,
            "model_name": model_name,
            "provider": provider,
            "model_label": model_label,
            "text": text,
            "challenges": metadata["challenges"],
            "contention": metadata["contention"],
            "converging": bool(metadata["converging"]),
            "created_at": created_at,
        }

    async def _generate_synthesis(
        self,
        *,
        session: AsyncSession,
        battle_id: str,
        row: BattleRow,
        messages: List[Dict[str, Any]],
        name_a: str,
        name_b: str,
    ) -> str:
        prompt = build_synthesis_prompt(
            question=row.question,
            context=row.context,
            messages=messages,
            fighter_a=name_a,
            fighter_b=name_b,
        )
        parts: List[str] = []
        async for delta in self.gateway.stream_argument(
            model_id=row.model_a,
            system_prompt=synthesis_system_prompt(),
            user_message=prompt,
            conversation_history=[],
            temperature=0.4,
            max_tokens=900,
        ):
            if delta:
                parts.append(delta)
        final_answer = "".join(parts).strip()
        if not final_answer:
            raise AppException(
                code=AppErrorCode.SYNTHESIS_FAILED,
                message="The synthesis verdict was empty. Please retry the battle.",
                status_code=500,
                retryable=True,
                details={"battleId": battle_id},
            )
        return final_answer


class BattleStreamService:
    """Concrete IBattleStreamService implementation."""

    def __init__(
        self,
        db: AsyncSession,
        gateway: ModelGatewayService,
        session_factory: Optional[async_sessionmaker[AsyncSession]] = None,
    ) -> None:
        self.db = db
        self.gateway = gateway
        self.session_factory = session_factory or async_sessionmaker(
            bind=db.bind, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )

    async def stream_events(
        self,
        battle_id: str,
        last_event_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> AsyncGenerator[Event, None]:
        battle_service = BattleService(self.db, self.gateway)
        row = await battle_service.load_row(battle_id, user_id)
        last = _parse_last_event_id(last_event_id)

        # A retained channel is the canonical event log for the current run: its
        # IDs match what live subscribers already saw, so reconnects resume
        # without gaps or duplicates. This also covers the common case where a
        # battle completed between the disconnect and the reconnect.
        channel = _channels.get(battle_id)
        if channel is not None:
            await self.db.rollback()
            async for event in self._subscribe(channel, last):
                yield event
            return

        if row.status in TERMINAL_STATUSES:
            # No live channel (fresh worker or evicted): replay deterministically
            # from the persisted transcript.
            for event in _replay_from_db(row):
                if event[2] > last:
                    yield event
            return

        # Release the request's read transaction before the producer writes with
        # its own session (important for single-connection SQLite pools and for
        # returning the pool connection early in PostgreSQL).
        await self.db.rollback()

        channel, _ = _get_or_create_channel(battle_id)
        if channel.task is None and not channel.done:
            producer = _BattleProducer(self.session_factory, self.gateway, channel)
            channel.task = asyncio.create_task(producer.run(battle_id))

        async for event in self._subscribe(channel, last):
            yield event

    async def _subscribe(self, channel: RunChannel, last: int) -> AsyncGenerator[Event, None]:
        index = last
        while True:
            async with channel.condition:
                while len(channel.events) <= index and not channel.done:
                    await channel.condition.wait()
                batch = channel.events[index:]
                finished = channel.done and not batch
            if not batch:
                if finished:
                    break
                await asyncio.sleep(0)
                continue
            for event in batch:
                index = event[2]
                yield event
            if finished:
                break


def _replay_from_db(row: BattleRow, *, include_done: bool = True) -> List[Event]:
    """Deterministically rebuilds the SSE sequence from a persisted battle."""
    events: List[Event] = []

    def add(name: str, payload: Any) -> None:
        events.append(_event(name, len(events) + 1, payload))

    messages = sorted(row.messages, key=lambda m: (m.round, m.created_at, m.id))
    summaries = {summary.round: summary.summary for summary in row.round_summaries}
    for round_number in range(1, 5):
        turns = [m for m in messages if m.round == round_number]
        if not turns:
            continue
        stage = stage_for_round(round_number)
        add("battle.stage", SSEBattleStage(round=round_number, stageKey=stage.key))
        for turn in turns:
            add(
                "battle.message.start",
                SSEBattleMessageStart(
                    messageId=turn.id,
                    speaker=turn.speaker,
                    modelId=turn.model_id,
                    stageLabel=turn.stage_label,
                ),
            )
            add("battle.message.chunk", SSEBattleMessageChunk(messageId=turn.id, delta=turn.text))
            add(
                "battle.message.done",
                SSEBattleMessageDone(
                    messageId=turn.id,
                    contention=turn.contention,
                    challenges=turn.challenges,
                    converging=turn.converging,
                ),
            )
        if round_number in summaries:
            add(
                "battle.round.summary",
                SSEBattleRoundSummary(round=round_number, summary=summaries[round_number]),
            )

    if row.final_answer:
        add("battle.synthesis.start", SSEBattleSynthesisStart(status="synthesizing"))
        battle = battle_to_schema(row)
        add(
            "battle.final",
            SSEBattleFinal(
                finalAnswer=battle.finalAnswer,
                insights=battle.insights,
                agreement=battle.agreement,
            ),
        )
    elif row.status == "failed":
        add(
            "battle.error",
            {
                "code": AppErrorCode.API_FAILURE.value,
                "message": "This battle failed before producing a verdict. You can retry it.",
                "retryable": True,
            },
        )
    if include_done:
        add(
            "battle.done",
            {"battleId": row.id, "status": row.status, "completedAt": utcnow().isoformat()},
        )
    return events
