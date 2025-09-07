# Repository Guidelines

## Project Structure & Module Organization
- `backtester/` — Core engine (`engine.py`), metrics, reporting, plotting, and `strategy_base.py`.
- `strategies/` — User strategies. File: `snake_case.py`; Class: `CamelCaseStrategy` with `generate_signals()`.
- `backend/` — FastAPI API. Entry: `backend/app/main.py`; services under `backend/app/services/`; tests in `backend/tests/`.
- `frontend/` — React + TypeScript (Vite). App code in `frontend/src/`.
- `tests/` — Pytest suite for core backtester. `data/` — sample CSVs (avoid large/private data).

## Build, Test, and Development Commands
- Python venv (WSL2 recommended): `python3 -m venv venv && source venv/bin/activate`
- Install deps: `pip install -r requirements.txt && pip install -r backend/requirements.txt`
- Run API (dev): `uvicorn backend.app.main:app --reload` → http://localhost:8000
- Core tests: `pytest tests -q` (coverage: `pytest --cov=backtester -q`)
- Backend tests: `pytest -c backend/pytest.ini -q` or `cd backend && pytest -q`
- Frontend: `npm -C frontend install` · Dev: `npm -C frontend run dev` · Build: `npm -C frontend run build`
- Frontend tests/lint: `npm -C frontend run test:coverage` · `npm -C frontend run lint`

## Coding Style & Naming Conventions
- Python: PEP 8, 4‑space indent, type hints. Modules `snake_case.py`, classes `CamelCase`, functions `snake_case`, constants `UPPER_CASE`.
- Strategies: small, pure, deterministic; use `logging` (avoid prints in libraries).
- TypeScript/React: ESLint + Prettier. Components `PascalCase.tsx` in `components/`; hooks `useName.ts`; tests `*.test.ts(x)`.

## Testing Guidelines
- Frameworks: Pytest (core/backend), Vitest + Testing Library (frontend).
- Coverage: aim for 90%+ in touched areas; parametrize and use minimal fixtures.
- Naming: colocate tests mirroring source (e.g., `foo.test.tsx`, `test_engine.py`).

## Commit & Pull Request Guidelines
- Commits: Conventional Commits (e.g., `feat:`, `fix:`, `refactor:`, `test:`, `docs:`); imperative mood and scoped.
- PRs: clear description, what/why, linked issues, test plan; screenshots for UI diffs. Ensure lint and tests pass across backend, core, and frontend.

## Security & Configuration Tips
- Never commit secrets or large datasets. Use env vars for local overrides. SQLite in `backend/database/` is dev‑only.
- CORS defaults to localhost for dev; review before exposing services.

## Agent‑Specific Instructions
- Prefer minimal, focused diffs; keep changes consistent with existing style.
- Do not perform git operations unless explicitly requested.
- Use server-side filtering for large data (e.g., charts) and cache where possible.

# Agent Operation Policy

- **Do not run backend or frontend servers unless explicitly instructed by the user.** Always assume the user is already running the necessary servers for development or testing. As a pair programmer, the agent should rely on the user to test and validate any changes made. Never attempt to start, restart, or stop backend (FastAPI) or frontend (React/Vite) servers unless the user specifically requests it.