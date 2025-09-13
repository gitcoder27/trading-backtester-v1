# Project Handoff – Trading Backtester (Phase 2 Complete)

This document summarizes what was implemented, why, how to use it, and what’s next. It is intended as a practical handoff to the next developer/agent to continue with Phase 2+ performance work and features.

## Executive Summary

- Overall goal: a fast, data‑driven backtesting UI with a clean, modern dashboard and a performant Analytics workflow that scales to large datasets.
- Phase 1 delivered:
  - A redesigned Dashboard with actionable, live content and no hardcoded values.
  - Correct parameter wiring between the Backtest Modal (Execution & Risk) and the backtesting engine.
  - API enhancements to reduce payloads and avoid recomputation on page loads.
  - Analytics page restructured to emphasize the price+trades (TradingView) experience and lazy‑load heavy charts.
- Next phases focus on server‑side caching, downsampling, and background precompute to make large backtests feel instantaneous.

---

## What’s Implemented (Phase 2)

This phase focused on backend performance primitives and frontend integration to keep analytics snappy on large datasets.

- Performance sections + server cache
  - `GET /api/v1/analytics/performance/{id}?sections=...` computes only requested sections: `basic_metrics`, `advanced_analytics`, `risk_metrics`, `trade_analysis`, `daily_target_stats`, `drawdown_analysis`.
  - First compute persists to `Backtest.results.analytics_summary` and stamps `results.analytics_cache` (cached_at, version, sections, completed_at).
  - Responses include `ETag`/`Last-Modified` headers; to keep clients simple, endpoints always return 200 with a body.

- Chart downsampling
  - `GET /api/v1/analytics/charts/{id}` and focused variants (`/equity`, `/drawdown`, `/trades`) accept `max_points` (100–200000) and downsample server‑side while preserving last point.

- Transport + validation
  - GZip middleware enabled.
  - Input bounds enforced for `max_points` and `chart-data` `max_candles` (now allows 1 to support prime query).

- Frontend integration
  - API client now encodes arrays as repeated query params (FastAPI‑compatible for `sections`, `chart_types`).
  - Equity/Drawdown charts request `maxPoints` and lazy‑fetch on intersection.
  - Advanced metrics call the new sections endpoint and load reliably on Overview.

Key files (Phase 2)
- BE: `backend/app/api/v1/analytics.py`, `backend/app/services/analytics/analytics_service.py`, `backend/app/services/analytics/chart_generator.py`, `backend/app/services/analytics_service.py`, `backend/app/main.py`.
- FE: `frontend/src/services/api.ts`, `frontend/src/services/analytics.ts`, `frontend/src/components/charts/{EquityChart,DrawdownChart}.tsx`, `frontend/src/pages/Analytics/Analytics.tsx`, `frontend/src/components/analytics/AdvancedMetrics/{index.tsx,usePerformanceData.ts}`, `frontend/src/hooks/useInView.ts`.
- Tests: `backend/tests/test_analytics_phase2.py`.

How to validate (Phase 2 highlights)
- Overview: metrics load; quick charts request `max_points≈600` and fetch on visibility.
- Analytics tab: Equity/Drawdown use `max_points≈1500`; Returns/Monthly unchanged.
- TradingView: primes with `max_candles=1` then loads the selected window (default 3000).
- API spot checks:
  - `GET /api/v1/analytics/performance/{id}?sections=basic_metrics&sections=risk_metrics`
  - `GET /api/v1/analytics/charts/{id}/equity?max_points=600`

What's not done yet (left for Phase 3/4)
- Downsampling for returns/monthly charts and comparison chart.
- Persistent chart caches keyed by `{chart_type,max_points}` with TTL.
- Rolling metrics API route (service method exists) and more lightweight endpoints for tiles.
- Trade log table (virtualized) and broader frontend polish.

---

## What’s Implemented (Phase 1)

### 1) Dashboard – New Layout + Live Data

- Replaced the old dashboard with a clean, minimal, data‑driven layout:
  - Hero card with quick actions (Run Backtest opens the config modal directly; post‑submit auto‑navigates to Backtests).
  - Performance Snapshot row (horizontal tiles): pulls metrics from minimal endpoint; no recomputation.
  - Recent Activity: recent backtests + recent jobs with status and quick links.
  - Strategy Highlights: Top Performers (with fallback computed from recent backtests) and Most Tested.
  - Data Overview: dataset counts, rows, quality, top timeframes/exchanges.

Key frontend files:
- `frontend/src/pages/Dashboard/Dashboard.tsx`
- `frontend/src/pages/Dashboard/hooks/useDashboardData.ts`
- `frontend/src/pages/Dashboard/components/PerformanceRow.tsx`
- `frontend/src/pages/Dashboard/components/RecentActivity.tsx`
- `frontend/src/pages/Dashboard/components/StrategyHighlights.tsx`
- `frontend/src/pages/Dashboard/components/DataOverview.tsx`

Notes:
- Removed legacy demo/placeholder components to keep codebase clean.
- Dashboard uses compact queries and minimal endpoints to avoid heavy JSON and recompute.

### 2) Backtest Modal – Correct Engine Wiring

- Fixed mapping so Execution & Risk config actually affects backtests:
  - Frontend `BacktestConfig` now maps to API’s `BacktestRequest` shape:
    - `strategy_params` → strategy constructor params (formerly `parameters`).
    - `engine_options` → execution engine options (`initial_cash`, `lots`, `fee_per_trade`, `slippage`, `intraday`, `daily_target`, etc.).
  - Fixed lots/position size confusion: modal sends lots directly (no units inflation).
  - Forwarded `slippage` and `fee_per_trade` correctly.
- Backend bridging: if engine options include `daily_profit_target`, we set `daily_target` for the engine.

Key files:
- FE: `frontend/src/components/modals/BacktestModal/useBacktestForm.ts`
- FE: `frontend/src/services/backtest.ts` (BacktestService + JobService mapping corrected)
- BE: `backend/app/api/v1/backtests.py` and `backend/app/api/v1/jobs.py` (daily_target bridge)

### 3) API Enhancements for Performance

- Minimal detail for backtest detail:
  - `GET /api/v1/backtests/{id}?minimal=true`
    - Returns essential fields + `metrics` + `engine_config`, omits heavy `results` blob unless explicitly requested.
- Compact list for backtests:
  - `GET /api/v1/backtests?page=1&size=50&compact=true`
    - Returns minimal rows and avoids parsing heavy JSON for list rendering.

Backend file:
- `backend/app/api/v1/backtests.py` (compact list + minimal detail)

### 4) Analytics – Restructure + Lazy Loading

- Tabs are now:
  - Overview: Advanced metrics + two quick charts (Equity, Drawdown).
  - Price + Trades: Only the TradingView panel (primary experience), with limited default candles.
  - Analytics: Other charts (Equity, Drawdown, Returns, Trade Analysis), loaded lazily with React.lazy + Suspense.
- All analytics queries use longer `staleTime`, keep previous data, and skip focus refetch.

Key files:
- `frontend/src/pages/Analytics/Analytics.tsx`
- `frontend/src/components/analytics/AdvancedMetrics/usePerformanceData.ts`
- `frontend/src/components/charts/*` (query options tuned)

---

## Data Contracts and Endpoints (Quick Reference)

### Phase 2 Endpoint Updates (Delta)

- Performance
  - `GET /api/v1/analytics/performance/{id}?sections=...`
    - Accepts repeated `sections` params; computes only requested sections and serves from cache when present.
    - Caches under `Backtest.results.analytics_summary` with metadata in `results.analytics_cache`.
    - Includes `ETag`/`Last-Modified` headers; endpoint always returns 200 with body.
- Charts
  - `GET /api/v1/analytics/charts/{id}?chart_types=...&max_points=1500`
  - `GET /api/v1/analytics/charts/{id}/{equity|drawdown|trades}?max_points=600`
    - Downsamples large series to keep payload sizes bounded while preserving the last point.
- TradingView
  - `GET /api/v1/analytics/chart-data/{id}?include_trades=true&include_indicators=true&max_candles=3000&start=YYYY-MM-DD&end=YYYY-MM-DD&tz=Zone`
    - `max_candles` now allows 1 to support prime queries.

- Backtests
  - `GET /api/v1/backtests?compact=true&page=1&size=50` → `{ total, page, size, results: [{ id, strategy_name, dataset_id, status, created_at, completed_at }] }`
  - `GET /api/v1/backtests/{id}?minimal=true` → minimal fields + `metrics` + `engine_config` (omits heavy `results`)
- Jobs
  - `POST /api/v1/jobs/` (BacktestRequest shape; include `strategy_params` and `engine_options`)
  - `GET /api/v1/jobs/stats` → for running jobs count
- Analytics (current)
  - `GET /api/v1/analytics/performance/{id}` → computes performance summary (heavy). Used only where needed; consider caching (Phase 2).
  - `GET /api/v1/analytics/charts/{id}/...` → generates Plotly JSON; heavy for large datasets.
  - `GET /api/v1/analytics/chart-data/{id}` → TradingView data with flags: `include_trades`, `include_indicators`, `max_candles`, `start`, `end`, `tz`.

---

## Known Gaps / Observations

- Analytics endpoints recompute on every call; large datasets increase CPU and latency.
- Plotly JSON payloads are large; no server‑side downsampling/ETag/gzip.
- TradingView chart loads entire day ranges; default `max_candles` is limited but can still be heavy for big windows.
- Commission semantics differ between older Backtests form (percent) and modal (fee per trade). Consider unification or explicit labels.

---

## Next Steps (Phase 2 → Phase 4)

Note: Phase 2 items in this section are now complete. See “What’s Implemented (Phase 2)” above. Focus next on Phase 3/4 tasks.

### Phase 2 – API Controls + Caching (High ROI)

1) Performance summary sections + caching
- Add `sections` query to `/analytics/performance/{id}` (e.g., `basic`, `advanced`, `risk`, `trade`) so clients can request only what they need.
- Compute and persist `analytics_summary` JSON per backtest on first request (or on job completion), keyed by backtest_id.
- Add `force=true` to recompute on demand.

2) Chart downsampling + compression
- Add `max_points` to `/analytics/charts/{id}` and downsample on server (LTTB or similar).
- Enable gzip via FastAPI `GZipMiddleware` and ensure JSON responses use it for large payloads.
- Add `ETag` and `Last-Modified` headers for `/analytics/performance`, `/analytics/charts`, `/analytics/chart-data` for client/proxy caching.

3) Chart-data guardrails
- Enforce reasonable defaults/limits for `max_candles` and reject abusive ranges with 400.
- Provide suggested presets (e.g., `max_candles` presets for small/medium/large views).

### Phase 3 – Background Precompute (UX polish)
- On backtest completion (job runner), precompute and store:
  - `analytics_summary` (all sections): basic, advanced, risk, trade.
  - Downsampled equity/drawdown snapshot (e.g., 500/2000 points) for fast chart loads.
- Move large `results` arrays to a dedicated table/column or compress them to avoid heavy DB reads for metadata queries.

### Phase 4 – Frontend Polish + Observability
- Add IntersectionObserver to lazy‑fetch analytics tile sections only when visible.
- Introduce a small cache TTL indicator in the UI if needed (optional).
- Add API timing logs and basic metrics (per endpoint) to track P95 latency and cache hit rate.
- Consider virtualized trade log table (react-window) when implemented.

---

## Implementation Notes / Rationale

- Minimal/Compact endpoints: by reducing payload and avoiding JSON parsing of `results`, we cut initial load time and CPU.
- Query caching: longer `staleTime`, `keepPreviousData`, and avoiding window‑focus refetch stabilize the UI and reduce needless work.
- TradingView focus: users primarily want price + trades; placing it in its own tab emphasizes the core workflow while keeping heavy charts lazy.
- Engine wiring: making sure Execution & Risk params affect the engine resolved “identical results” from different runs.

---

## How to Validate

- Dashboard
  - Verify snapshot tiles appear quickly; no recompute calls; changing latest backtest changes metrics.
  - “Run Backtest” opens modal; submitting navigates to Backtests.
- Analytics
  - Overview loads header + metrics and two quick charts quickly.
  - Price + Trades loads TradingView with default 3000 candles; day switching in the panel should be responsive.
  - Analytics tab lazy‑loads charts the first time and stays cached across tab switches.
- API
  - `GET /api/v1/backtests?compact=true` should not parse heavy `results` and returns minimal fields.
  - `GET /api/v1/backtests/{id}?minimal=true` returns metrics + engine_config without `results`.

---

## Risks / Edge Cases

- Legacy consumers expecting old response shapes could be affected if they rely on `results` always present (we gated via `minimal` flag).
- Some strategies may still ignore newer `strategy_params` entries; validate parameter naming and types on those strategies.
- Timezone handling in TradingView: ensure `tz` is supplied consistently by datasets.

---

## Branches / Commits

- Base: `main`
- Phase 1 commit: `feat: redesign dashboard and optimize analytics performance` (hash visible in `git log`)
- Current working branch for Phase 2: `feat/enhancements-phase-2` (pushed and tracking origin)

Additional:
- Phase 2 changes have been merged into `main`. New tests: `backend/tests/test_analytics_phase2.py`.

---

## Suggested Work Breakdown (Actionable)

1) Backend (Phase 3)
- Persist downsampled chart caches per `{chart_type,max_points}` with TTL; invalidate on backtest changes.
- Add downsampling for `returns` and `monthly_returns`; consider comparison chart downsampling.
- Optional: re‑enable 304 conditional responses once clients handle them gracefully.
- Add rolling metrics API route (service method exists) and lightweight endpoints for tile data.
- Add stricter guards/rate limits for `max_points`/`max_candles`.

2) Frontend (Phase 3/4)
- Extend downsampled usage to Returns/Trade Analysis/Monthly charts (where appropriate).
- Virtualize trade log table and add sort/filter UX.
- Unify commission semantics across forms (absolute fee vs percent toggle or consistent labels).
- Extend IntersectionObserver to remaining heavy tiles; keep skeletons for perceived performance.

3) Testing & Observability
- Add API tests for `compact`/`minimal` flags and performance `sections` filtering.
- Add performance smoke tests and set baseline payload size/latency caps for analytics endpoints.
- Add basic server metrics (P95 latency, cache hit rate) and wire simple dashboards.

---

## Contact / Notes

- If the code owner wants an initial PR draft summarizing Phase 1 and outlining Phase 2, the branch `feat/enhancements-phase-2` is ready.
- The repository has recent changes that remove unused components; be mindful when rebasing long‑lived branches.

*** End of handoff ***
