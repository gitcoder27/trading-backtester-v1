# Environment & Setup Notes

- **Project Location:** This project directory is located inside a WSL2 Ubuntu environment on Windows (e.g., `/home/<user>/Projects/trading-backtester-v1` in Ubuntu via WSL2).
- **Dependency Installation:** All Python dependencies must be installed inside a virtual environment (venv) within WSL2. Do not install Python packages globally or outside the venv.

**Quickstart for WSL2 Ubuntu:**

```bash
# From project root in Ubuntu WSL2:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

This ensures all dependencies are isolated and avoids system Python issues in WSL2.

# Repository Guidelines

## Project Structure & Module Organization
- `backtester/`: Core engine (`engine.py`), metrics, reporting, plotting, base class `strategy_base.py`.
- `strategies/`: User strategies. File: `snake_case.py`; Class: `CamelCaseStrategy` with `generate_signals()`.
- `backend/`: FastAPI API. Entry: `backend/app/main.py`; services under `backend/app/services/`; tests in `backend/tests/`.
- `frontend/`: React + TypeScript app (Vite). Code in `frontend/src/`.
- `tests/`: Pytest suite for core backtester. `data/`: sample CSVs (avoid committing large/private data).

## Build, Test, and Development Commands
- Python env: `python -m venv .venv && source .venv/bin/activate`
- Install deps (core + API): `pip install -r requirements.txt && pip install -r backend/requirements.txt`
- Run API (dev): `uvicorn backend.app.main:app --reload` → http://localhost:8000
- Core tests: `pytest tests -q` (coverage: `pytest --cov=backtester -q`)
- Backend tests: `pytest -c backend/pytest.ini -q` or `cd backend && pytest -q`
- Frontend: `npm -C frontend install`; dev: `npm -C frontend run dev`; build: `npm -C frontend run build`; tests: `npm -C frontend run test:coverage`; lint: `npm -C frontend run lint`

## Coding Style & Naming Conventions
- Python: PEP 8, 4‑space indent, type hints; modules `snake_case.py`, classes `CamelCase`, functions `snake_case`, constants `UPPER_CASE`.
- Keep strategies small, pure, and deterministic; log via library logging (avoid print in libs).
- TypeScript/React: ESLint + Prettier; components `PascalCase.tsx` under `components/`; hooks `useName.ts`; tests `*.test.ts(x)`.

## Testing Guidelines
- Python: Pytest. Backend markers available: `unit`, `integration`, `api`, `slow` (see `backend/pytest.ini`).
- Aim for 90%+ coverage in touched areas; add minimal fixtures and parametrize where helpful.
- Frontend: Vitest + Testing Library. Run `npm -C frontend run test` or `test:watch/coverage`.

## Commit & Pull Request Guidelines
- Commits: Prefer Conventional Commits (e.g., `feat:`, `fix:`, `test:`, `docs:`). Keep messages imperative and scoped.
- PRs: Clear description, linked issues, what/why, test plan; include screenshots for UI changes. Ensure lint/tests pass for backend, core, and frontend.

## Security & Configuration Tips
- Do not commit secrets or large datasets. Use env vars for local overrides; SQLite files in `backend/database/` are dev‑only.
- CORS is limited to localhost in dev; review before exposing services.
