# Sangram AI — Different Minds. One Arena.

Sangram AI is a React/Vite frontend backed by a FastAPI service. Accounts, model availability, battles, battle history, saved answers, and preferences use the backend API. Model provider credentials stay on the backend.

## Local setup

### Backend (PowerShell)

```powershell
cd D:\Sangram-Ai-main\backend
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env  # only when .env does not already exist
# Edit .env with DATABASE_URL, SECRET_KEY, and provider keys (server-side only).
alembic upgrade head
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Set `DATABASE_URL` to a PostgreSQL SQLAlchemy async URL, for example `postgresql+asyncpg://USER:PASSWORD@localhost:5432/sangram_ai`. To start the repository's PostgreSQL container (when Docker Desktop is installed and running), run `docker compose up -d postgres` from `backend`. Set `SECRET_KEY` to a long random value. Add the provider key(s) needed by the selected models (`OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_API_KEY`, `GROQ_API_KEY`, `MISTRAL_API_KEY`, `XAI_API_KEY`). These belong only in `backend/.env` or your deployment secret manager. Email verification and password recovery use the configured backend email settings; console email is suitable only for local development.

The backend declares Python `>=3.11`. This workspace's Python 3.13 environment passed the backend test suite, lint, compilation, and migration checks.

### Frontend (separate PowerShell terminal)

```powershell
cd D:\Sangram-Ai-main\frontend
npm ci
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
npm run dev
```

`frontend/.env` should contain `VITE_API_BASE_URL=http://localhost:8000`. The FastAPI CORS allowlist must include the frontend origin (`http://localhost:3000` or `http://127.0.0.1:3000`). Never put provider keys, database credentials, or signing keys in `VITE_*` variables.

## Verify the integration

Open `http://localhost:3000`, create an account, then sign in. In Arena, select two models marked available, submit a prompt, and follow the streamed responses. The completed battle is persisted and appears in history. A model is unavailable until its provider key is configured in the backend environment.

API docs are at `http://localhost:8000/docs`.

## Current service boundaries

The backend implements authentication, profile/preferences, model and archetype catalogs, persisted battles and SSE, battle history, and saved answers. Billing plans are catalog data. Subscription, checkout, invoices, usage metering, payment webhooks, and share service operations are still backend stubs (501); the frontend surfaces those errors rather than showing fabricated payment or usage results.

Backend tests: `cd backend; .\.venv\Scripts\python.exe -m pytest -q`. Frontend production build: `cd frontend; npm run build`.
