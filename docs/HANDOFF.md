# Project Handoff – Trading Backtester (Phase 1 Complete)

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

---

## Suggested Work Breakdown (Actionable)

1) Backend
- Add `sections` to `/analytics/performance/{id}` and implement per‑section computation.
- Persist `analytics_summary` on first compute + add cache metadata.
- Add `max_points` to `/analytics/charts/{id}` and apply downsampling; add GZip middleware.
- Add ETag/Last‑Modified headers to analytics endpoints.
- Enforce hard limits for `max_candles`/`max_points` and input validation.

2) Frontend
- Switch quick charts to call lighter server endpoints when available (downsampled/compact).
- Add IntersectionObserver to delay Analytics tab chart fetches until visible.
- Align commission semantics across Backtests form and Modal (explicit UI labels or conversion logic).

3) Testing
- Add API tests for `compact` and `minimal` flags.
- Add performance smoke tests (simple timers) around analytics endpoints to catch regressions.

---

## Contact / Notes

- If the code owner wants an initial PR draft summarizing Phase 1 and outlining Phase 2, the branch `feat/enhancements-phase-2` is ready.
- The repository has recent changes that remove unused components; be mindful when rebasing long‑lived branches.

*** End of handoff ***

