# Backend Implementation Checklist (FastAPI-first)

Use this file to track the AI agent's backend progress. No Redis now; no git operations by the agent. The agent works phase-by-phase and reports status on phase completion.

## High-level plan
Implement backend in phases. Deliverables are testable at the end of each phase.

## Checklist (compact)

### Phase 0 — Setup & verification
- [ ] `backend/app/main.py` with `/health` endpoint
  - Done if: `uvicorn backend.app.main:app` serves `/health` 200
- [ ] `backend/requirements.txt` (backend deps)
  - Done if: includes fastapi, uvicorn, sqlalchemy, pydantic + core deps
- [ ] Smoke test importing and running a tiny backtest
  - Done if: unit test exists and passes

### Phase 1 — Synchronous engine adapter + API
- [ ] `backend/app/services/backtest_service.py` (wraps `BacktestEngine`)
  - Done if: returns serializable {equity, trade_log, metrics}
- [ ] POST `/api/v1/backtests` and GET `/api/v1/backtests/{id}/results`
  - Done if: POST runs small dataset synchronously and returns result; GET returns result
- [ ] Unit tests for the service using `data/` sample CSVs
- [ ] `backend/README.md` with run & sample request instructions (PowerShell)

### Phase 2 — Background jobs & status (no Redis)
- [ ] In-process job runner `backend/app/tasks/job_runner.py` (Thread/Process pool)
- [ ] Endpoints: list jobs, GET `/api/v1/backtests/{id}/status`, POST `/api/v1/backtests/{id}/stop`
- [ ] Progress hook in adapter to record percent complete
- [ ] Integration test: submit job, poll until complete, fetch results

### Phase 3 — Persistence, datasets & strategy registry
- [ ] SQLAlchemy models + migrations: `strategies`, `datasets`, `backtests`, `trades`, `metrics`
- [ ] Dataset endpoints: upload, preview, quality check
- [ ] Strategy registry service (discover `strategies/` and expose metadata)
- [ ] Strategy validation endpoint (`/api/v1/strategies/{id}/validate`)

### Phase 4 — Analytics & optimization
- [ ] Analytics endpoints (drawdown, rolling sharpe, plotly JSON)
- [ ] `/api/v1/optimize` runs grid-search as background job

## Quality gates (apply at each phase)
- [ ] Unit tests for the phase pass
- [ ] Integration tests (phase flows) pass
- [ ] No `streamlit` imports in backend modules
- [ ] CLI `main.py` still runnable
- [ ] README updated with run/test steps

## Acceptance criteria
Mark a phase done when: checklist items implemented, tests pass, and agent returns a concise status report listing files changed and run commands.

## Minimal blocker questions (agent may ask only if necessary)
1. "Use filesystem strategy discovery or store strategies in DB?" (Default: filesystem)
2. "Confirm dataset storage path (default: `data/market_data/`)?" (Default: yes)
3. "Do you want Redis & Celery now or later?" (Default: later — do not implement now)

## Progress cadence & reporting
Agent returns concise status at phase completion with:
- Files added/modified
- Test results (PASS/FAIL)
- Run instructions
- Open issues or technical debt

---

End of checklist.
