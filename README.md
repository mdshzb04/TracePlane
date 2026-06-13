<div align="center">

# Traceplane

**Telemetry-first control plane for AI agents in production**

Monitor traces, costs, and failures across every model provider — one SDK, full visibility.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg)](https://fastapi.tiangolo.com/)
[![Langfuse](https://img.shields.io/badge/Langfuse-Integrated-blue.svg)](https://langfuse.com/)

[Quick Start](#quick-start) · [Documentation](#documentation) · [Configuration](#configuration)

</div>

---

## Overview

**Traceplane** is an AI agent observability platform. Instrument agents with the SDK, ingest real telemetry into PostgreSQL, and explore traces, costs, latency, and health in the dashboard — no fake metrics.

The Python package and internal repo name remain `agentops-hub` for compatibility; the product brand is **Traceplane**.

### What you get

- **One SDK** — Python and TypeScript clients with auto agent discovery
- **13+ LLM providers** — OpenAI, Anthropic, Gemini, Mistral, and more in the marketing SDK showcase
- **Real telemetry** — Executions, spans, tokens, and cost stored in PostgreSQL
- **Langfuse tracing** — Optional LLM span export (SDK v4)
- **Enterprise auth** — Email/password and GitHub OAuth
- **Marketing site** — Landing page with provider orbit, architecture flow, and SDK snippets

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│  Frontend (Next.js 15 · React 19 · Tailwind · Framer Motion) │
│  Landing · Dashboard · Traces · Agents · Analytics · SDK   │
└──────────────────────────┬──────────────────────────────────┘
                           │ REST /api → proxy → /api/v1
┌──────────────────────────▼──────────────────────────────────┐
│  Backend (FastAPI)                                          │
│  Auth · Ingest · Analytics · Agents · Alerts · Providers   │
└──────────────────────────┬──────────────────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
  PostgreSQL          Langfuse (opt.)    OpenAI / NVIDIA NIM
```

**Layers:** Routers → Services → Repositories → PostgreSQL. LLM calls route through `backend/app/llm/` (OpenAI or NVIDIA NIM). LangGraph powers backend investigation workflows.

---

## Tech stack

| Layer | Stack |
|-------|--------|
| **Backend** | FastAPI, SQLAlchemy 2 (async), Alembic, Pydantic v2, LangGraph, Langfuse SDK v4 |
| **Frontend** | Next.js 15, React 19, TypeScript, Tailwind CSS, Framer Motion, Recharts |
| **Data** | PostgreSQL (local Docker or Neon), optional Redis/Celery |
| **Auth** | JWT + refresh cookies, GitHub OAuth, RBAC (admin / developer / viewer) |
| **SDKs** | `sdk/` (Python), `sdk-ts/` (TypeScript) |

---

## Project structure

```
p3h/
├── backend/                 # FastAPI API
│   ├── app/
│   │   ├── agents/          # LangGraph investigator graph
│   │   ├── llm/             # OpenAI + NVIDIA provider layer
│   │   ├── routers/         # HTTP endpoints
│   │   ├── services/        # Business logic (analytics, ingest, auth, …)
│   │   └── models/          # SQLAlchemy models
│   ├── alembic/             # Migrations
│   └── tests/
├── frontend/                # Next.js app
│   ├── app/                 # Routes (dashboard, traces, agents, …)
│   └── components/
│       └── marketing/       # Landing page (hero orbit, architecture flow)
├── sdk/                     # Python SDK (agentops_hub)
├── sdk-ts/                  # TypeScript SDK
├── scripts/                 # Demo and e2e validation helpers
├── docs/                    # Getting started, GitHub OAuth setup
└── docker-compose.yml       # Postgres + Redis + API + worker
```

---

## Quick start

### Prerequisites

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ (or `docker compose up postgres -d`)

### 1. Clone and configure

```bash
git clone https://github.com/traceplane/traceplane.git
cd traceplane   # or your local folder name

cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env.local
```

Edit `backend/.env` with your database URL, `SECRET_KEY`, and optional API keys (Langfuse, NVIDIA/OpenAI, GitHub OAuth).

### 2. Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open **http://localhost:3000**

| URL | Purpose |
|-----|---------|
| http://localhost:3000 | Marketing landing + app entry |
| http://localhost:3000/login | Sign in (GitHub or email) |
| http://localhost:3000/dashboard | Observability dashboard (after login) |
| http://localhost:8000/docs | OpenAPI / Swagger |

> **Both servers must run.** The frontend proxies `/api/*` to the backend. If only Next.js is running, GitHub sign-in and API calls will fail.

### Docker (optional)

```bash
docker compose up -d postgres redis
# Then run backend + frontend locally as above, pointing DATABASE_URL at localhost:5432
```

### First trace

See **[docs/getting-started.md](docs/getting-started.md)** — create an API key, install the SDK, send one trace, and open Dashboard / Traces.

```bash
pip install -e ./sdk
python scripts/demo_agent.py    # optional local demo
```

---

## Configuration

### Backend (`backend/.env`)

```env
ENV=development
DATABASE_URL=postgresql+asyncpg://agentops:agentops@localhost:5432/agentops_hub
DATABASE_URL_SYNC=postgresql://agentops:agentops@localhost:5432/agentops_hub
SECRET_KEY=your-secret-key
FRONTEND_URL=http://localhost:3000
BACKEND_PUBLIC_URL=http://localhost:8000
CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
ALLOW_REGISTRATION=true

# GitHub OAuth (optional)
GITHUB_OAUTH_ENABLED=true
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=
GITHUB_REDIRECT_URI=http://localhost:3000/api/auth/github/callback

# LLM (investigator / agent builder)
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=
OPENAI_API_KEY=

# Langfuse (optional)
LANGFUSE_PUBLIC_KEY=
LANGFUSE_SECRET_KEY=
LANGFUSE_BASE_URL=https://cloud.langfuse.com
LANGFUSE_ENABLED=true
```

### Frontend (`frontend/.env.local`)

```env
NEXT_PUBLIC_API_URL=/api
BACKEND_INTERNAL_URL=http://127.0.0.1:8000
```

The browser uses the **same-origin** `/api` proxy so auth cookies and GitHub OAuth work without CORS issues.

---

## Authentication

- **Email** — Register/sign in at `/login` (`@gmail.com` or `@company.com` emails)
- **GitHub OAuth** — `Continue with GitHub` on the login page

GitHub setup: **[docs/GITHUB_OAUTH_SETUP.md](docs/GITHUB_OAUTH_SETUP.md)**

Callback URL for local dev:

```
http://localhost:3000/api/auth/github/callback
```

---

## SDK

| SDK | Path | Install |
|-----|------|---------|
| Python | `sdk/` | `pip install -e ./sdk` |
| TypeScript | `sdk-ts/` | `npm install ./sdk-ts` |

Ingest endpoint: `POST /api/v1/ingest/trace` with `X-API-Key` header.

```python
from agentops_hub import AgentOps

client = AgentOps(api_key="aoh_...", base_url="http://localhost:8000/api/v1")

with client.trace(agent="MyAgent", model="gpt-4o", framework="custom") as span:
    span.set_input("Hello")
    span.set_output("World")
    span.set_tokens(input_tokens=10, output_tokens=5)
```

Agents are **auto-discovered** on first ingest — no manual registry step.

---

## App pages

| Route | Description |
|-------|-------------|
| `/` | Marketing landing (hero, observability features, SDK showcase, architecture flow) |
| `/login` | Authentication |
| `/quickstart` | Onboarding wizard |
| `/dashboard` | Overview metrics |
| `/traces` | Trace explorer |
| `/agents` | Auto-discovered agents |
| `/analytics` | Cost and usage intelligence |
| `/alerts` | Threshold alerts |
| `/tools` | Tool invocation analytics |
| `/sdk` | Integration snippets (logged-in) |
| `/settings/*` | Account, API keys, providers |

---

## API overview

Base path: `/api/v1` (proxied as `/api` from the frontend).

| Area | Examples |
|------|----------|
| Auth | `POST /auth/login`, `POST /auth/register`, `GET /auth/github` |
| Ingest | `POST /ingest/trace` |
| Agents | `GET /agents`, `GET /agents/{id}` |
| Analytics | `GET /analytics/dashboard`, `GET /analytics/traces` |
| Executions | `GET /executions` |
| System | `GET /health`, `GET /system/onboarding` |

Full interactive docs: **http://localhost:8000/docs**

---

## Documentation

| Doc | Description |
|-----|-------------|
| [docs/getting-started.md](docs/getting-started.md) | Account → API key → first trace |
| [docs/GITHUB_OAUTH_SETUP.md](docs/GITHUB_OAUTH_SETUP.md) | GitHub OAuth app configuration |
| [backend/LANGFUSE_TRACING.md](backend/LANGFUSE_TRACING.md) | Langfuse SDK v4 integration |
| [sdk/README.md](sdk/README.md) | Python SDK reference |

---

## Development

```bash
# Backend tests
cd backend && pytest

# Backend lint
cd backend && ruff check .

# Frontend lint
cd frontend && npm run lint

# E2E (Playwright)
cd frontend && npm run test:e2e

# Live API validation
python scripts/e2e_validate.py
```

### Migrations

```bash
cd backend
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

### Demo scripts

```bash
python scripts/demo_company.py   # Seed demo agents
python scripts/demo_agent.py     # Send sample telemetry
python scripts/e2e_validate.py   # HTTP smoke checks
```

---

## Langfuse

When `LANGFUSE_ENABLED=true`, the backend exports traces for executions, evaluations, and LangGraph investigator runs. See [backend/LANGFUSE_TRACING.md](backend/LANGFUSE_TRACING.md).

---

## License

MIT — see repository license file.
# TracePlane
