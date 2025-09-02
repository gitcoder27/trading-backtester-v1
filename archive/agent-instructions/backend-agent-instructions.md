# Backend Integration Instructions (FastAPI-first)

Use this file as the exact instruction for the next AI agent you assign to implement the backend described in the attached PRD. Work step-by-step and avoid destructive refactors. The goal is to build a FastAPI backend that reuses the existing `backtester/` framework and `strategies/` implementations in this repository.

-----

## High-level rules (must follow)
- Do NOT perform any git operations (branching, commits, pushes, PRs). The human operator will handle all git actions.
- Do NOT add or require Redis for Phase 1. You may add optional notes where Redis/Celery could improve scale, but do not implement Redis now.
- Do NOT run or depend on the Streamlit UI. Any module that imports `streamlit` must be considered UI-only. Extract pure logic only; remove Streamlit calls from code that will be used by the backend.
- Ask clarifying questions only when absolutely necessary (missing file path, ambiguous input schema). Otherwise proceed and return results when a phase is complete.
- Preserve CLI compatibility: do not change `main.py`'s behavior or the strategy files' public API unless absolutely required; document any small compatibility changes.
- Prefer minimal, surgical changes and keep existing public APIs stable.

-----

## Files/folders you should reuse (copy or import directly from the repo root)
- Core backtester framework (required):
  - `backtester/engine.py`  (core engine)
  - `backtester/strategy_base.py`  (strategy interface)
  - `backtester/data_loader.py`  (CSV loading/resampling)
  - `backtester/metrics.py`  (performance metrics)
  - `backtester/optimization_utils.py`  (fast indicators/optimizations)
  - `backtester/trade_log.py`  (export logic)
  - `backtester/plotting.py`  (plotly/matplotlib utilities)
  - `backtester/reporting.py` and `backtester/html_report.py` and `backtester/report_template.html`
- Strategies: `strategies/*.py` (all strategy implementations) — do not modify their public methods unless required.
- Business logic to port (strip UI):
  - `webapp/analytics.py` (analytics functions)
  - `webapp/backtest_runner.py` (run_backtest wrapper) — extract business logic only.
  - Any `webapp/*` modules that contain pure functions (data filters, exporters), you may port those functions but remove Streamlit dependencies.
- Tests: `tests/*` (use to validate behavior after port).

Files to ignore or decouple (do not port UI code into backend):
- `app.py` (Streamlit UI entrypoint) and any modules that import `streamlit` and assume session state.

-----

## Phased Plan (execute strictly in order)

### Phase 0 — initial setup and verification (deliverable: skeleton + verification)
1. Create a FastAPI app skeleton at `backend/app/main.py` (or similar). Expose `/health` endpoint.
2. Create a `backend/requirements.txt` (or update `pyproject.toml`) for backend-only dependencies. Include: `fastapi`, `uvicorn`, `sqlalchemy`, `pydantic`, plus existing deps: `pandas`, `numpy`, `numba`, `plotly`.
3. Ensure CLI `main.py` continues to run unchanged (no edits required for Phase 0).
4. Add a simple unit test that imports `backtester.engine` and runs a smoke test on a small CSV in `data/` to ensure import path correctness.

### Phase 1 — engine adapter and synchronous API (deliverable: working synchronous backtest endpoint)
1. Implement `backend/app/services/backtest_service.py`:
   - Wrap `BacktestEngine` to accept: dataset path or uploaded CSV bytes, strategy identifier (module/class name), strategy params, and engine options.
   - Return a JSON-serializable result: equity curve (array of {timestamp: ISO, equity: float}), trade_log (list of dicts), indicators if present, and a metrics summary (use `backtester/metrics.py`).
   - Convert pandas/numpy types to native Python types (e.g., timestamps to ISO strings, numpy floats to float).
2. Implement `backend/app/api/v1/backtests.py`:
   - POST `/api/v1/backtests` — accept JSON body with fields: `strategy` (module.class), `strategy_params` (dict), `dataset` (path or multipart upload), `engine_options` (initial_cash, lots, option_delta, fee_per_trade, slippage, intraday, daily_target).
   - For small datasets run synchronously and return results in the response.
   - GET `/api/v1/backtests/{id}/results` — for now allow retrieval of last result from in-memory store or SQLite.
3. Write unit tests for the service: run a known strategy using sample CSV from `data/` and assert that the metrics functions return expected values (sanity checks, not numeric equality to many decimals).
4. Provide a README snippet `backend/README.md` showing how to run uvicorn and execute sample request (PowerShell commands).

### Phase 2 — background job queue and status (deliverable: queued job support without Redis)
> NOTE: Do not add Redis now. Implement a simple in-process job queue and persistence table for background runs. Keep the code structured so Redis/Celery can be introduced later.
1. Implement a minimal job runner (file `backend/app/tasks/job_runner.py`) that:
   - Runs long backtests in a separate thread or process (Python `concurrent.futures.ThreadPoolExecutor` / `ProcessPoolExecutor`).
   - Stores job metadata and progress into SQLite `backtests` table.
   - Supports job cancellation via a simple in-memory cancellation flag and check points inside the engine adapter.
2. Expose API endpoints:
   - GET `/api/v1/backtests` — list jobs.
   - GET `/api/v1/backtests/{id}/status` — returns job state and progress.
   - POST `/api/v1/backtests/{id}/stop` — request cancellation.
3. Ensure the engine adapter supports an optional progress callback (hook) you can call periodically to record percent-complete into the job record.
4. Tests: integration test that submits a small job via POST, polls status until `completed`, then fetches results.

### Phase 3 — persistence, datasets and strategies management (deliverable: persist runs and dataset endpoints)
1. Add SQLite models via SQLAlchemy for: `strategies`, `datasets`, `backtests`, `trades`, `metrics`.
2. Implement dataset endpoints:
   - POST `/api/v1/datasets/upload` — save CSV to local `data/market_data/` and create dataset record (rows, timeframe).
   - GET `/api/v1/datasets/{id}/preview` — return first N rows as JSON.
   - GET `/api/v1/datasets/{id}/quality` — simple checks (missing timestamps, NaNs, timezone consistency).
3. Implement strategy registry service that discovers strategies from `strategies/` and returns metadata (name, params schema derived from `get_params_config()` if available).
4. Implement strategy validation endpoint: POST `/api/v1/strategies/{id}/validate` that attempts to instantiate and call `generate_signals` on a small sample dataset and returns errors/warnings.

### Phase 4 — analytics & optimization endpoints (deliverable: analytics endpoints and basic optimizer)
1. Port analytic functions from `webapp/analytics.py` and expose endpoints:
   - GET `/api/v1/analytics/performance` — returns metrics summary.
   - GET `/api/v1/analytics/charts/{id}` — returns Plotly JSON for equity/trades/drawdown.
2. Implement `/api/v1/optimize` to run a grid search using `backtester/optimization_utils.py`. Run as background job; return job id and results when done.
3. Tests: basic optimizer run that searches a small param grid and returns best parameters.

-----

## API contract examples (minimal)
- POST /api/v1/backtests
  - Request body example (JSON):
    ```json
    {
      "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
      "strategy_params": {"debug": false},
      "dataset_path": "data/nifty_2024_1min_22Dec_14Jan.csv",
      "engine_options": {"initial_cash": 100000, "lots": 2, "option_delta": 0.5}
    }
    ```
  - Response: JSON with `job_id` (if queued) or `result` (equity curve + trades + metrics).

- GET /api/v1/backtests/{id}/results
  - Response: same result structure (serializable lists/dicts).

-----

## Acceptance criteria / quality gates
- Unit tests covering backtest service and analytics functions pass.
- Integration test: POST backtest, poll status, GET results succeed for a sample CSV in `data/`.
- CLI `main.py` remains runnable and produces the same results for the same inputs.
- No `streamlit` imports exist in backend modules. If refactoring is required, move Streamlit usages to a `ui/` adapter that is not imported by backend services.
- Provide `backend/README.md` with run/test steps.

-----

## How to run locally (PowerShell examples)

### Recommended: Create and activate a Python virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

Install dependencies (you may already have the repo-level `requirements.txt`; ensure FastAPI deps added):

```powershell
python -m pip install -r requirements.txt
python -m pip install fastapi uvicorn sqlalchemy pydantic
```

Start FastAPI server (from repo root):

```powershell
uvicorn backend.app.main:app --reload
```

Run tests (from repo root):

```powershell
pytest -q
```

-----

## Minimal deliverables to return to the human operator at phase completion
- Phase 0: `backend/app/main.py` with `/health` endpoint, `backend/requirements.txt`, and a smoke test that imports core modules.
- Phase 1: `backend/app/services/backtest_service.py`, `backend/app/api/v1/backtests.py`, unit tests, and `backend/README.md` showing run steps. The POST backtest endpoint must return immediate results for small datasets.
- Phase 2: background job runner (`backend/app/tasks/job_runner.py`), status and stop endpoints, and integration tests validating queued runs.
- Phase 3+: persistence, dataset endpoints, strategy registry and validation endpoints.

When each phase is finished, return a concise status message with:
- What was implemented (files added/modified),
- Test results (unit + integration),
- Any open issues, blockers or non-blocking technical debt (e.g., places to add Redis/Celery later),
- How to run the new code locally.

-----

## If blocked or uncertain
Ask only one of the following short questions:
1. "Do you want Redis & Celery now or later?" (answer: later — do not implement Redis now)
2. "Confirm dataset storage path (default: `data/market_data/`)?"
3. "Do you want strategies stored in DB or discovered from filesystem initially?" (default: filesystem discovery)

-----

## Final note to the agent
- Do not print commentary updates to the human unless a phase completes or you are blocked and require one of the allowed clarifying questions.
- Do not perform any git operations.
- Keep changes minimal and test-driven. Return only when Phase 1 is ready or if one of the clarifying questions above must be answered.


---

End of instructions.
