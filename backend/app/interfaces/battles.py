"""Battle Orchestration and Streaming Interfaces (Developer 4 Boundary).

Defines the protocols Developer 4 must fulfill to replace the mock deterministic
battle generator with multi-model dialectic debate and SSE streaming.
"""

from typing import AsyncGenerator, List, Optional, Protocol, Tuple, runtime_checkable
from app.schemas.battle import (
    Battle,
    BattleCreateRequest,
    BattleCreateResponse,
    BattleSummaryCard,
)
from app.schemas.saved import SavedAnswerCreate, SavedAnswerResponse
from app.schemas.share import ShareCreateResponse


@runtime_checkable
class IBattleService(Protocol):
    """Manages battle creation, debate lifecycle transitions, and persistence."""

    async def create_battle(
        self, user_id: str, payload: BattleCreateRequest
    ) -> BattleCreateResponse:
        """Validates fighters, checks credit entitlement, initializes battle state.
        
        Supports idempotency through clientBattleId.
        
        Raises:
            ValidationError: If model IDs are invalid.
            RateLimitError: If user quota is exceeded.
        """
        ...

    async def get_battle(self, battle_id: str, user_id: Optional[str] = None) -> Battle:
        """Retrieves full normalized Battle object.
        
        Enforces private ownership unless battle is publicly shared.
        
        Raises:
            NotFoundError: If battle does not exist.
            ForbiddenError: If caller does not own the battle.
        """
        ...

    async def list_user_battles(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[BattleSummaryCard], int]:
        """Returns paginated debate history cards for user dashboard."""
        ...

    async def delete_battle(self, battle_id: str, user_id: str) -> bool:
        """Removes a battle record owned by user."""
        ...

    async def cancel_battle(self, battle_id: str, user_id: str) -> bool:
        """Cancels an in-progress battle execution."""
        ...

    async def retry_battle(self, battle_id: str, user_id: str) -> BattleCreateResponse:
        """Restarts a failed battle run."""
        ...


@runtime_checkable
class IBattleStreamService(Protocol):
    """Streams real-time debate turns and synthesis via Server-Sent Events (SSE)."""

    async def stream_events(
        self, battle_id: str, last_event_id: Optional[str] = None, user_id: Optional[str] = None
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """Yields (event_name, json_data) tuples matching BACKEND_CONTRACT.md.
        
        Events emitted:
            battle.stage
            battle.message.start
            battle.message.chunk
            battle.message.done
            battle.round.summary
            battle.synthesis.start
            battle.final
            battle.error
            battle.done
        """
        ...


@runtime_checkable
class IShareService(Protocol):
    """Creates and resolves public read-only debate shares."""

    async def create_share_link(self, battle_id: str, user_id: str) -> ShareCreateResponse:
        """Generates a stable share token for a completed battle."""
        ...

    async def get_share_snapshot(self, share_token: str) -> Battle:
        """Returns the read-only Battle snapshot associated with shareToken."""
        ...


@runtime_checkable
class ISavedAnswerService(Protocol):
    """Manages user's saved architectural decision records (ADRs)."""

    async def save_answer(self, user_id: str, payload: SavedAnswerCreate) -> SavedAnswerResponse:
        """Saves a synthesis verdict to the user's library."""
        ...

    async def list_saved_answers(
        self, user_id: str, page: int = 1, page_size: int = 20
    ) -> Tuple[List[SavedAnswerResponse], int]:
        """Lists saved answers with pagination."""
        ...

    async def delete_saved_answer(self, answer_id: str, user_id: str) -> bool:
        """Removes a saved answer."""
        ...
