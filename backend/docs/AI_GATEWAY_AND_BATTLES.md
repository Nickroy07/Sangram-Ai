# AI Gateway & Dialectic Battle Engine

Implementation notes for Developer 3 (model gateway) and Developer 4 (battle
engine, SSE, shares and saved answers). The wire contracts are defined in
`docs/API_CONVENTIONS.md` and `docs/openapi.yaml`; this page covers operation.

## Configuration

Provider credentials are read from the environment only:

```bash
OPENAI_API_KEY=...        OPENAI_MODEL=gpt-4o
ANTHROPIC_API_KEY=...     ANTHROPIC_MODEL=claude-3-5-sonnet-20241022
GOOGLE_API_KEY=...        GEMINI_MODEL=gemini-2.0-flash
GROQ_API_KEY=...          GROQ_MODEL=llama-3.3-70b-versatile
MISTRAL_API_KEY=...       MISTRAL_MODEL=mistral-large-latest
XAI_API_KEY=...           XAI_MODEL=grok-2-latest
```

Optional `*_BASE_URL` overrides support OpenAI-compatible proxies. Timeouts are
controlled by `AI_CONNECT_TIMEOUT_SECONDS` and `AI_REQUEST_TIMEOUT_SECONDS`.

A model whose provider key is missing is reported with `isAvailable: false` on
`GET /api/models`. Running that model fails with `MISSING_CONFIG`; it is never
silently replaced by a mock.

## Endpoints

| Method | Path | Purpose |
| :-- | :-- | :-- |
| `GET` | `/api/models` | Catalog annotated with `apiModel` and `isAvailable` |
| `POST` | `/api/battles` | Create a battle (idempotent with `clientBattleId`) |
| `GET` | `/api/battles` | Paginated history cards |
| `GET` | `/api/battles/{id}` | Full normalized `Battle` object |
| `GET` | `/api/battles/{id}/events` | SSE debate stream |
| `POST` | `/api/battles/{id}/cancel` | Cancel a pending/running battle |
| `POST` | `/api/battles/{id}/retry` | Clear the transcript and re-queue |
| `DELETE` | `/api/battles/{id}` | Delete a battle |
| `POST` | `/api/shares` | Create a share token for a completed battle |
| `GET` | `/api/s/{token}` | Public read-only battle snapshot |
| `GET` | `/api/saved` | List saved verdicts |
| `POST` | `/api/saved` | Save/update a verdict |
| `DELETE` | `/api/saved/{id}` | Remove a saved verdict |

## Debate execution

The SSE endpoint starts the run on the first connection. Each battle runs four
rounds with both fighters speaking per round:

1. Opening Arguments
2. Counterarguments & Challenges
3. Rebuttals & Concessions
4. Final Positions

A synthesis call on Fighter A's provider then produces the consolidated verdict.
Every completed turn and round summary is persisted before the corresponding
event is published, so `GET /api/battles/{id}` never shows a turn the client has
not seen.

Event order is `battle.stage` → `battle.message.start` → `battle.message.chunk`
(repeated) → `battle.message.done` → `battle.round.summary` per round, then
`battle.synthesis.start` → `battle.final` → `battle.done`.

### Reconnects

Events carry a monotonic `id:`. The first connection creates an in-process,
append-only channel for the battle; reconnects with `Last-Event-ID` resume from
that channel without duplicate or skipped IDs. Completed/failed battles with no
live channel (for example after a worker restart) are replayed deterministically
from the persisted transcript. A retried battle discards its old channel.

The channel registry is per worker process. With multiple workers, a reconnect
that lands on a different worker still receives a complete replay, but its event
IDs restart from 1. If sticky SSE routing is required, terminate streaming on a
single worker or move the event log to Redis.

### Agreement score

`compute_agreement` uses `claim-graph-overlap-v1` and returns `demo: false`:

- 55% content-word overlap between the two Round 4 positions
- 25% share of turns containing explicit concession/agreement language
- 20% presence of shared agreement vocabulary

Scores are clamped to 5–95 and include an explanatory note. No demo or random
values are used.

## Tests

```bash
cd backend
.venv/bin/python -m pytest -q
```

`tests/test_model_gateway.py` covers provider parsing, error mapping, pricing and
catalog availability without network access. `tests/test_battles_api.py` runs the
full lifecycle with a deterministic fake gateway, including SSE resume, shares
and saved answers.
