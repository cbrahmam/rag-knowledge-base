# Contributing to DocuMind

Thanks for improving DocuMind! This guide covers local setup, tests and the
conventions CI enforces.

## Prerequisites

- Python 3.11+
- Node.js 18+
- An Anthropic API key for the LLM-backed features (put it in `.env`)

## Setup

```bash
# from the repo root
make install        # installs backend (requirements-dev) + frontend deps
cp .env.example .env  # then add your ANTHROPIC_API_KEY
```

Or manually:

```bash
cd backend && pip install -r requirements-dev.txt
cd frontend && npm install
```

## Running

```bash
make dev-backend    # uvicorn on :8000
make dev-frontend   # vite on :5173
```

## Tests & linting

CI (`.github/workflows/ci.yml`) runs on every PR. Reproduce it locally:

```bash
make test           # backend pytest
make lint           # ruff (backend) + eslint (frontend)
make build          # frontend production build
```

- Backend tests live in `backend/tests/` and isolate their JSON stores to a
  temp directory, so they never touch real local data.
- Config is centralized in `backend/config.py` (env-overridable). Avoid
  hardcoding model ids, thresholds or paths in service code.

## Conventions

- Keep commits focused and message them conventionally
  (`feat:`, `fix:`, `refactor:`, `test:`, `chore:`, `docs:`).
- Run `make lint` and `make test` before opening a PR.
