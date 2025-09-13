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

### Frontend Testing (Vitest)
- Install: `npm -C frontend install`
- Run once with coverage: `CI=1 npm -C frontend run test:coverage --silent -- --run`
- Alternate: `npm -C frontend run test --silent -- --run` or `vitest --run --coverage`
- Coverage HTML: open `frontend/coverage/index.html`
- Avoid watch-mode hang: always pass `--run` or set `CI=1` (don’t rely on default watch)

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

## Frontend Overview (React + Vite + TS)

- **Entry & Routing**: `src/main.tsx` mounts app with `BrowserRouter` and React Query; routes in `src/App.tsx` under `components/layout/Layout` (pages: `Dashboard`, `Strategies`, `Datasets`, `Backtests`, `BacktestDetail`, `Analytics`).
- **State Management**: `zustand` stores in `src/stores/` (`themeStore.ts`, `uiStore.ts`, `settingsStore.ts`). Dark mode is forced via `themeStore` and Tailwind `dark` class.
- **Data Fetching**: `@tanstack/react-query` configured in `src/lib/queryClient.ts` (retry, stale times). API wrapper in `src/services/api.ts`; feature services in `src/services/` (`backtest.ts`, `dataset.ts`, `analytics.ts`, `optimization.ts`, `strategyService.ts`).
- **UI & Components**: Reusable primitives in `src/components/ui/` (Button, Card, Modal, Toast, etc.); feature components under domain folders (e.g., `components/backtests`, `components/analytics`, `components/charts`, `components/modals`). Layout in `components/layout/`.
- **Pages**: Route-level screens in `src/pages/` grouped by feature (`Dashboard`, `Backtests`, `Datasets`, `Strategies`, `Analytics`) with local hooks/components.
- **Charts**: `src/components/charts/` provides equity/returns/drawdown/trade charts, with TradingView/Plotly wrappers.
- **Styling**: Tailwind (`tailwind.config.js`, `postcss.config.js`) and global styles in `src/index.css` (dark-first design). Fonts via Google Fonts.
- **Testing**: Vitest + Testing Library (`vitest.config.ts`, `src/test/`), MSW handlers in `src/test/mocks/`. Example tests under `src/components/__tests__/` and `src/services/__tests__/`.
- **Configs**: `vite.config.ts`, `tsconfig*.json`, `eslint.config.js`. NPM scripts in `package.json`.

## Backend Overview (FastAPI + SQLAlchemy)

- **Entry & App**: `backend/app/main.py` sets up FastAPI, CORS, health, and includes `api/v1` routers.
- **Routers**: `backend/app/api/v1/` for `backtests.py`, `jobs.py` (background), `datasets.py`, `strategies.py`, `analytics.py`, `optimization.py`.
- **Database**: `backend/app/database/models.py` defines `Backtest`, `BacktestJob`, `Trade`, `BacktestMetrics`, `Dataset`, `Strategy`; SQLite at `backend/database/backtester.db`; helpers: `get_session_factory()`, `init_db()`.
- **Services**: `backend/app/services/` contains domain logic:
  - Backtest: `backtest/` (`execution_engine.py`, `result_processor.py`, `progress_tracker.py`, `strategy_loader.py`), `backtest_service.py` (facade).
  - Analytics: `analytics/` (`performance_calculator.py`, `risk_calculator.py`, `trade_analyzer.py`, `chart_generator.py`), `analytics_service.py` (API adapter).
  - Others: `dataset_service.py`, `strategy_service.py`, `optimization_service.py`.
- **Background Jobs**: `backend/app/tasks/job_runner.py` manages threaded jobs with progress/cancellation; persists to `BacktestJob` and writes `Backtest` on completion.
- **Schemas**: `backend/app/schemas/backtest.py` Pydantic models for requests/responses.
- **Utilities**: `backend/app/utils/path_utils.py`.
- **Tests**: `backend/tests/` has service and API tests; run with `pytest -c backend/pytest.ini -q`.

## Backtester Overview (Core Engine)

- **Engine**: `backtester/engine.py` executes strategies on data. Uses a fast numba‑JIT vectorized core when possible; falls back to traditional bar-by-bar with strategy `should_exit()` for complex logic. Outputs `equity_curve`, `trade_log`, optional `indicators`, and `daily_summary` (with daily profit target support).
- **Strategy Base**: `backtester/strategy_base.py` defines `StrategyBase` with `generate_signals(data)` and `should_exit(position, row, entry_price)`. Strategies provide optional `indicator_config()` metadata.
- **Data Loading**: `backtester/data_loader.py` loads CSVs (`load_csv`) with dtype hints and resampling; `optimize_dataframe_memory()` downcasts for memory.
- **Metrics**: `backtester/metrics.py` exposes core metrics (`total_return`, `sharpe_ratio`, `max_drawdown`, `win_rate`, `profit_factor`, etc.), session helpers, and `daily_profit_target_stats()`.
- **Reporting**: `backtester/reporting.py` re-exports utilities from:
  - `plotting.py` (Plotly/Matplotlib charts, `plot_trades_on_candlestick_plotly`, `plot_equity_curve`).
  - `trade_log.py` (`save_trade_log` with cumulative/daily PnL columns).
  - `comparison.py` (`comparison_table` across runs).
  - `html_report.py` (standalone Plotly + metrics HTML report via Jinja2 `report_template.html`).
- **Optimization Utilities**: `backtester/optimization_utils.py` fast indicators (EMA/SMA/RSI/Bollinger via numba), vectorized signal helpers, and performance suggestions.
- **Performance Tools**: `backtester/performance_monitor.py` timing/memory monitors and Streamlit display hooks.
