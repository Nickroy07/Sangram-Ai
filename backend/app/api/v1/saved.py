"""Saved Answers & ADR Endpoints (Developer 4 Boundary).

Implements saved synthesis endpoints matching mockSavedService.
Requires authentication and delegates to ISavedAnswerService.
"""

from fastapi import APIRouter, Depends, Query, status

from app.api.deps import get_current_principal, get_saved_answer_service
from app.interfaces.battles import ISavedAnswerService
from app.schemas.auth import CurrentPrincipal
from app.schemas.common import PaginatedResponse
from app.schemas.saved import SavedAnswerCreate, SavedAnswerResponse

router = APIRouter(prefix="/saved", tags=["Saved Answers & ADRs"])


@router.get(
    "",
    response_model=PaginatedResponse[SavedAnswerResponse],
    status_code=status.HTTP_200_OK,
    summary="List Saved Answers",
)
async def list_saved(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    principal: CurrentPrincipal = Depends(get_current_principal),
    saved_service: ISavedAnswerService = Depends(get_saved_answer_service),
) -> PaginatedResponse[SavedAnswerResponse]:
    """Lists saved synthesis verdicts. Owned by Developer 4."""
    items, total = await saved_service.list_saved_answers(
        user_id=principal.user_id, page=page, page_size=page_size
    )
    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        has_more=(page * page_size) < total,
    )


@router.post(
    "",
    response_model=SavedAnswerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save Debate Synthesis",
)
async def save_answer(
    payload: SavedAnswerCreate,
    principal: CurrentPrincipal = Depends(get_current_principal),
    saved_service: ISavedAnswerService = Depends(get_saved_answer_service),
) -> SavedAnswerResponse:
    """Saves a synthesis verdict to library. Owned by Developer 4."""
    return await saved_service.save_answer(user_id=principal.user_id, payload=payload)


@router.delete(
    "/{saved_id}",
    status_code=status.HTTP_200_OK,
    summary="Remove Saved Answer",
)
async def delete_saved(
    saved_id: str,
    principal: CurrentPrincipal = Depends(get_current_principal),
    saved_service: ISavedAnswerService = Depends(get_saved_answer_service),
) -> dict:
    """Deletes a saved answer. Owned by Developer 4."""
    success = await saved_service.delete_saved_answer(
        answer_id=saved_id, user_id=principal.user_id
    )
    return {"success": success, "id": saved_id}
