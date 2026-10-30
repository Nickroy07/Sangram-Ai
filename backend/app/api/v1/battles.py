"""Battle and Debate Routing Endpoints (Developer 4 Boundary).

Implements the contract for battle initiation, retrieval, history, and SSE event streaming.
Routes require authentication and delegate to IBattleService and IBattleStreamService,
returning 501 MODULE_NOT_IMPLEMENTED until Developer 4 connects orchestration logic.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Header, Query, status
from fastapi.responses import StreamingResponse

from app.api.deps import (
    get_battle_service,
    get_battle_stream_service,
    get_current_principal,
)
from app.interfaces.battles import IBattleService, IBattleStreamService
from app.schemas.auth import CurrentPrincipal
from app.schemas.battle import (
    Battle,
    BattleCreateRequest,
    BattleCreateResponse,
    BattleSummaryCard,
)
from app.schemas.common import PaginatedResponse

router = APIRouter(prefix="/battles", tags=["Dialectic Battles"])


@router.post(
    "",
    response_model=BattleCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Debate Battle",
    description="Initiates a new multi-model arena debate and reserves quota credits.",
)
async def create_battle(
    payload: BattleCreateRequest,
    principal: CurrentPrincipal = Depends(get_current_principal),
    battle_service: IBattleService = Depends(get_battle_service),
) -> BattleCreateResponse:
    """Creates a new battle. Owned by Developer 4."""
    return await battle_service.create_battle(user_id=principal.user_id, payload=payload)


@router.get(
    "/{battle_id}",
    response_model=Battle,
    status_code=status.HTTP_200_OK,
    summary="Get Battle By ID",
    description="Returns the full normalized Battle object matching frontend UI expectations.",
)
async def get_battle(
    battle_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    battle_service: IBattleService = Depends(get_battle_service),
) -> Battle:
    """Retrieves full battle state. Owned by Developer 4."""
    return await battle_service.get_battle(battle_id=battle_id, user_id=principal.user_id)


@router.get(
    "/{battle_id}/events",
    summary="Stream Battle Events (SSE)",
    description=(
        "Server-Sent Events endpoint streaming real-time stage transitions, message chunks, "
        "round summaries, and final synthesis. See docs/BACKEND_CONTRACT.md."
    ),
    response_class=StreamingResponse,
)
async def stream_battle_events(
    battle_id: str,
    last_event_id: Optional[str] = Header(None, alias="Last-Event-ID"),
    principal: CurrentPrincipal = Depends(get_current_principal),
    stream_service: IBattleStreamService = Depends(get_battle_stream_service),
    battle_service: IBattleService = Depends(get_battle_service),
) -> StreamingResponse:
    """SSE debate turn and synthesis stream. Owned by Developer 4."""
    await battle_service.get_battle(battle_id=battle_id, user_id=principal.user_id)
    async def sse_generator():
        try:
            async for event_name, data in stream_service.stream_events(battle_id, last_event_id, principal.user_id):
                yield f"event: {event_name}\ndata: {data}\n\n"
        except Exception as exc:
            import json
            import logging
            logging.getLogger("sangram_ai.battles").exception("SSE stream exception: %s", exc)
            yield f"event: battle.error\ndata: {json.dumps({'code': 'STREAM_ERROR', 'message': str(exc), 'retryable': True})}\n\n"
            yield f"event: battle.done\ndata: {json.dumps({'battleId': battle_id})}\n\n"

    return StreamingResponse(
        sse_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "",
    response_model=PaginatedResponse[BattleSummaryCard],
    status_code=status.HTTP_200_OK,
    summary="List Debate History",
    description="Lists past completed debate summaries for the authenticated user.",
)
async def list_battles(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(get_current_principal),
    battle_service: IBattleService = Depends(get_battle_service),
) -> PaginatedResponse[BattleSummaryCard]:
    """Lists history cards. Owned by Developer 4."""
    items, total = await battle_service.list_user_battles(
        user_id=principal.user_id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.delete(
    "/{battle_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Battle",
    description="Deletes a battle record owned by the authenticated caller.",
)
async def delete_battle(
    battle_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    battle_service: IBattleService = Depends(get_battle_service),
) -> dict:
    """Deletes a battle. Owned by Developer 4."""
    success = await battle_service.delete_battle(battle_id=battle_id, user_id=principal.user_id)
    return {"success": success, "battleId": battle_id}


@router.post(
    "/{battle_id}/cancel",
    status_code=status.HTTP_200_OK,
    summary="Cancel In-Progress Battle",
)
async def cancel_battle(
    battle_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    battle_service: IBattleService = Depends(get_battle_service),
) -> dict:
    """Cancels a running battle. Owned by Developer 4."""
    success = await battle_service.cancel_battle(battle_id=battle_id, user_id=principal.user_id)
    return {"success": success, "battleId": battle_id}


@router.post(
    "/{battle_id}/retry",
    response_model=BattleCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Retry Failed Battle",
)
async def retry_battle(
    battle_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    battle_service: IBattleService = Depends(get_battle_service),
) -> BattleCreateResponse:
    """Retries a failed battle. Owned by Developer 4."""
    return await battle_service.retry_battle(battle_id=battle_id, user_id=principal.user_id)
