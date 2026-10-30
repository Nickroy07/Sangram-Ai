# SANGRAM AI — Backend Integration Contract

The frontend talks to the FastAPI backend through `src/services/apiClient.js`.
**No provider API keys may ship in this client** — the backend holds provider
credentials and makes model requests.

## Current frontend boundary

| Module | Role | Swap point |
| --- | --- | --- |
| `src/services/apiClient.js` and `api.js` | Central API client and endpoint wrappers | `VITE_API_BASE_URL`, default `http://localhost:8000` |
| `src/services/battleService.js` | Legacy local battle generator | Not used by the Arena workflow |
| `src/services/api.js` | Battle creation, retrieval, history, and SSE | Uses backend response/event schemas below |
| `src/components/*` | Render backend battle data | No provider keys in the browser |

The backend returns one normalized battle shape:

```ts
type Battle = {
  id: string
  question: string
  fighters: [{ slot: 0, modelId, name, provider, modelLabel }, …]
  messages: BattleMessage[]          // chronological, shared timeline
  roundSummaries: string[]           // one per round, used by export
  finalAnswer: string                // ONE consolidated answer
  insights: { a: string, b: string }
  agreement: { score: number|null, note: string|null, label: string, demo: false }|null
  source: 'backend'
}

type BattleMessage = {
  id: string
  round: 1|2|3|4                     // 5 = synthesis (not a message)
  stageKey: 'opening'|'counter'|'rebuttal'|'final'
  stageLabel: string
  speaker: 'A'|'B'
  modelId: string                    // catalog identity, for accent resolution
  modelName: string
  provider: string
  modelLabel: string                 // display id, distinct from apiModel
  text: string
  challenges: string|null            // named claim being answered
  contention: string|null            // explicit disagreement topic (rare!)
  converging: boolean                // position was refined/conceded
}
```

## Endpoints the backend should expose

```
POST /api/battles
  body:  { question: string(10–1000), modelA: string, modelB: string,
           clientBattleId?: string }   // idempotency key
  201:   { battleId, streamUrl, estimatedCost }
  4xx/5xx: { code: ErrorCode, message, retryable: boolean }

GET  /api/battles/:id/events           (SSE)
  events:
    battle.stage { round, stageKey }
    battle.message.start   { messageId, speaker, modelId, stageLabel }
    battle.message.chunk   { messageId, delta }
    battle.message.done    { messageId, contention?: string, challenges?: string }
    battle.round.summary   { round, summary }
    battle.synthesis.start
    battle.final           { finalAnswer, insights, agreement }
    battle.error           { code, message, retryable }
    battle.done

GET  /api/battles/:id                  → persisted Battle (same shape)
POST /api/shares  { battleId }          → { shareToken }   (enables real links)
GET  /api/s/:token                      → read-only Battle snapshot
```

### Error codes the UI already renders

`MISSING_CONFIG`, `API_FAILURE`, `TIMEOUT`, `RATE_LIMIT`, `AUTH_FAILED`,
`NETWORK_OFFLINE`, `EMPTY_RESPONSE`, `SYNTHESIS_FAILED`.
The API client shows readable server, network, and timeout errors. Battle
updates are consumed from the backend SSE endpoint by `subscribeBattle()`.

## Agreement score

No numeric agreement score is currently computed. The backend returns a null
score with an explanatory note; the client does not invent one.

## Share links

Share API routes exist in the contract, but the backend share service is not
implemented and currently returns 501. The live battle UI does not present
client-generated links as persisted shared records.

## Timestamps

Battle and message timestamps come from persisted backend records.
