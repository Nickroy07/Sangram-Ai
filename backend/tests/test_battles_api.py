"""End-to-end API tests for battle orchestration, SSE, shares and saved answers."""

import json
import re
from typing import AsyncGenerator, Dict, List

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_current_principal, get_model_gateway_service
from app.catalog import MODELS_CATALOG
from app.proposals.entities import User
from app.schemas.auth import CurrentPrincipal


class FakeGateway:
    """Deterministic streaming double; no network or API keys required."""

    def __init__(self) -> None:
        self.calls: List[Dict[str, object]] = []

    async def stream_argument(
        self,
        model_id: str,
        system_prompt: str,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncGenerator[str, None]:
        self.calls.append({"model_id": model_id, "system_prompt": system_prompt})
        if "synthesis engine" in system_prompt.lower():
            text = (
                "Consolidated verdict: begin with Python for iteration speed, then isolate "
                "throughput-critical paths in Go once measured demand appears. Both fighters "
                "now agree on a staged plan, shared review metrics, and a clear migration trigger. "
                "The remaining disagreement is the exact scale threshold, which should be set from "
                "production data rather than predicted in advance."
            )
        else:
            round_match = re.search(r"This is Round (\d+)", user_message)
            round_number = int(round_match.group(1)) if round_match else 1
            name_match = re.search(r"You are ([^;]+); your opponent", user_message)
            name = name_match.group(1).strip() if name_match else model_id
            text = (
                f"Round {round_number} from {name}. The decision should be judged by durable "
                "trade-offs rather than novelty. "
            )
            if round_number >= 3:
                text += (
                    "I concede the opponent has a fair point about operational risk, and we can "
                    "agree on common ground: a staged migration with shared metrics. "
                )
            else:
                text += "The opponent's framing underestimates the cost of premature complexity. "
            text += (
                "The strongest option is a staged approach: validate the real bottleneck, keep the "
                "first delivery small, and publish the evidence that would justify changing course."
            )
        for index in range(0, len(text), 48):
            yield text[index : index + 48]

    async def check_provider_health(self, provider: str) -> bool:
        return True

    async def estimate_token_cost(
        self, model_id: str, input_tokens: int, estimated_output_tokens: int
    ) -> int:
        return 7

    async def get_active_models(self):
        return MODELS_CATALOG


def parse_sse(raw: str) -> List[Dict[str, str]]:
    events: List[Dict[str, str]] = []
    for block in raw.strip().split("\n\n"):
        if not block.strip():
            continue
        event = {"id": "", "event": "", "data": ""}
        for line in block.splitlines():
            if line.startswith("id: "):
                event["id"] = line[4:]
            elif line.startswith("event: "):
                event["event"] = line[7:]
            elif line.startswith("data: "):
                event["data"] = event["data"] + line[6:]
        events.append(event)
    return events


def names(events: List[Dict[str, str]]) -> List[str]:
    return [event["event"] for event in events]


@pytest_asyncio.fixture
async def battle_app(real_app, db_factory, mock_principal, fake_gateway):
    async with db_factory() as session:
        session.add(
            User(
                id=mock_principal.user_id,
                email="arena-owner@sangram.ai",
                password_hash="not-used",
                role="user",
                is_active=True,
                is_verified=True,
            )
        )
        await session.commit()

    async def principal_override() -> CurrentPrincipal:
        return mock_principal

    real_app.dependency_overrides[get_current_principal] = principal_override
    real_app.dependency_overrides[get_model_gateway_service] = lambda: fake_gateway
    yield real_app


@pytest_asyncio.fixture
async def battle_client(battle_app) -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=battle_app), base_url="http://testserver"
    ) as client:
        yield client


@pytest.fixture
def fake_gateway() -> FakeGateway:
    return FakeGateway()


PAYLOAD = {
    "question": "Should early-stage startups choose Python or Go for high-throughput services?",
    "modelA": "chatgpt",
    "modelB": "claude",
    "archetypeA": "logician",
    "archetypeB": "pragmatist",
    "context": "A five-person team shipping its first product.",
}


async def _create(client: AsyncClient, **overrides) -> dict:
    response = await client.post("/api/battles", json={**PAYLOAD, **overrides})
    assert response.status_code == 201, response.text
    return response.json()


@pytest.mark.asyncio
async def test_full_battle_lifecycle_and_sse_sequence(battle_client, fake_gateway):
    created = await _create(battle_client)
    battle_id = created["battleId"]
    assert created["streamUrl"] == f"/api/battles/{battle_id}/events"
    # Two fighter estimates plus one synthesis estimate, 7 cents each.
    assert created["estimatedCost"] == 21

    # Before streaming, only the accepted record exists.
    pending = (await battle_client.get(f"/api/battles/{battle_id}")).json()
    assert pending["id"] == battle_id
    assert pending["messages"] == []
    assert pending["finalAnswer"] == ""

    stream = await battle_client.get(created["streamUrl"])
    assert stream.status_code == 200
    assert stream.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(stream.text)
    event_names = names(events)

    assert event_names.count("battle.stage") == 4
    assert event_names.count("battle.message.start") == 8
    assert event_names.count("battle.message.done") == 8
    assert event_names.count("battle.round.summary") == 4
    assert event_names.count("battle.synthesis.start") == 1
    assert event_names.count("battle.final") == 1
    assert event_names.count("battle.done") == 1
    assert event_names[0] == "battle.stage"
    assert event_names[-1] == "battle.done"
    assert event_names.index("battle.synthesis.start") < event_names.index("battle.final")

    # Event IDs are monotonic and start at 1.
    ids = [int(event["id"]) for event in events]
    assert ids == list(range(1, len(events) + 1))

    final = json.loads(next(e["data"] for e in events if e["event"] == "battle.final"))
    assert final["finalAnswer"].startswith("Consolidated verdict")
    assert final["agreement"]["demo"] is False
    assert final["agreement"]["method"] == "claim-graph-overlap-v1"
    assert isinstance(final["agreement"]["score"], int)
    assert final["insights"]["a"] and final["insights"]["b"]

    completed = (await battle_client.get(f"/api/battles/{battle_id}")).json()
    assert len(completed["messages"]) == 8
    assert len(completed["roundSummaries"]) == 4
    assert completed["finalAnswer"].startswith("Consolidated verdict")
    assert completed["agreement"]["score"] == final["agreement"]["score"]
    assert completed["source"] == "backend"
    assert completed["fighters"][0]["archetypeId"] == "logician"
    assert completed["fighters"][1]["archetypeId"] == "pragmatist"

    history = (await battle_client.get("/api/battles")).json()
    assert history["total"] == 1
    assert history["items"][0]["id"] == battle_id
    assert history["items"][0]["consensusScore"] == final["agreement"]["score"]
    assert history["items"][0]["models"] == ["chatgpt", "claude"]

    # The gateway was called for 8 turns + 1 synthesis.
    assert len(fake_gateway.calls) == 9


@pytest.mark.asyncio
async def test_sse_reconnect_resumes_after_last_event_id(battle_client):
    created = await _create(battle_client)
    first = await battle_client.get(created["streamUrl"])
    total = len(parse_sse(first.text))

    resumed = await battle_client.get(
        created["streamUrl"], headers={"Last-Event-ID": "10"}
    )
    events = parse_sse(resumed.text)
    assert events, "resume should replay the remaining events"
    assert all(int(event["id"]) > 10 for event in events)
    assert int(events[-1]["id"]) == total


@pytest.mark.asyncio
async def test_idempotent_creation_with_client_battle_id(battle_client):
    first = await _create(battle_client, clientBattleId="client-key-1")
    second = await _create(battle_client, clientBattleId="client-key-1")
    assert first["battleId"] == second["battleId"]


@pytest.mark.asyncio
async def test_validation_rejects_unknown_models_and_same_fighter(battle_client):
    response = await battle_client.post(
        "/api/battles", json={**PAYLOAD, "modelB": "not-a-model"}
    )
    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_ERROR"

    response = await battle_client.post(
        "/api/battles", json={**PAYLOAD, "modelB": "chatgpt"}
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_prompt_alias_is_accepted(battle_client):
    payload = {k: v for k, v in PAYLOAD.items() if k != "question"}
    response = await battle_client.post(
        "/api/battles", json={**payload, "prompt": "Is a monorepo better than polyrepo for a small team?"}
    )
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_private_battle_is_forbidden_for_another_user(battle_client, battle_app):
    created = await _create(battle_client)
    battle_id = created["battleId"]

    async def other_principal() -> CurrentPrincipal:
        return CurrentPrincipal(
            user_id="usr_someone_else",
            email="other@sangram.ai",
            role="user",
            tier="free",
            permissions=[],
            is_authenticated=True,
        )

    battle_app.dependency_overrides[get_current_principal] = other_principal
    response = await battle_client.get(f"/api/battles/{battle_id}")
    assert response.status_code == 403
    assert response.json()["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_share_link_and_saved_answer_flow(battle_client, battle_app):
    created = await _create(battle_client)
    battle_id = created["battleId"]
    await battle_client.get(created["streamUrl"])

    share = await battle_client.post("/api/shares", json={"battleId": battle_id})
    assert share.status_code == 201, share.text
    token = share.json()["shareToken"]
    assert token
    shared = await battle_client.get(f"/api/s/{token}")
    assert shared.status_code == 200
    assert shared.json()["id"] == battle_id
    assert len(shared.json()["messages"]) == 8

    saved = await battle_client.post(
        "/api/saved",
        json={
            "battleId": battle_id,
            "question": PAYLOAD["question"],
            "finalAnswer": shared.json()["finalAnswer"],
            "fighters": ["chatgpt", "claude"],
            "notes": "Revisit after the first release.",
        },
    )
    assert saved.status_code == 201, saved.text
    saved_id = saved.json()["id"]
    assert saved.json()["fighters"] == ["chatgpt", "claude"]

    listing = (await battle_client.get("/api/saved")).json()
    assert listing["total"] == 1
    assert listing["items"][0]["notes"] == "Revisit after the first release."

    delete = await battle_client.delete(f"/api/saved/{saved_id}")
    assert delete.status_code == 200
    assert delete.json()["success"] is True
    assert (await battle_client.get("/api/saved")).json()["total"] == 0


@pytest.mark.asyncio
async def test_cancel_and_retry_completed_battle(battle_client):
    created = await _create(battle_client)
    battle_id = created["battleId"]
    await battle_client.get(created["streamUrl"])

    cancel = await battle_client.post(f"/api/battles/{battle_id}/cancel")
    assert cancel.status_code == 200
    assert cancel.json()["success"] is False  # already completed

    retry = await battle_client.post(f"/api/battles/{battle_id}/retry")
    assert retry.status_code == 202, retry.text
    assert retry.json()["battleId"] == battle_id

    cleared = (await battle_client.get(f"/api/battles/{battle_id}")).json()
    assert cleared["messages"] == []
    assert cleared["finalAnswer"] == ""

    rerun = await battle_client.get(created["streamUrl"])
    assert len(parse_sse(rerun.text)) > 0
    completed = (await battle_client.get(f"/api/battles/{battle_id}")).json()
    assert len(completed["messages"]) == 8
