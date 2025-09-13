## Backend Codebase Analysis and Refactor Plan

### Executive summary
- **Overall**: The backend is functionally rich with clear modularization for backtests and analytics, but it carries legacy bridges, duplicated logic, and several long files that hinder maintainability.
- **Top priorities**: Fix job runner bugs, remove/replace legacy analytics and backtest paths, de-duplicate shared helpers, and split very long service/router files.
- **Quick wins**: Resolve broken references in optimization, unify job status handling, centralize dataset and strategy resolution, and prune dead code.

---

## Long files and refactor recommendations
Below are the long or complex files that would benefit most from refactor. Line counts are approximate.

- **backend/app/services/analytics_service_legacy.py (~1410 LOC)**
  - **Issue**: Huge, largely duplicated with new modular analytics. Only `get_chart_data()` remains actively needed (others overlap with modular components).
  - **Plan**:
    - Extract a new modular component `analytics/data_fetcher.py` for dataset/backtest result loading and time range filtering.
    - Move TradingView formatting, trade markers, and indicator synthesis into `analytics/chart_generator.py` or a dedicated `analytics/tradingview_builder.py`.
    - Port `get_chart_data()` into `analytics/analytics_service.py` using the above helpers.
    - Delete unused legacy methods; keep a slim legacy shim only if strictly necessary during transition.

- **backend/app/tasks/job_runner.py (~615 LOC)**
  - **Issues**:
    - Duplicate `list_jobs` method (one overrides the other); dead code present.
    - Uses `JobStatus.PENDING.value` as if `JobStatus` were an Enum; it's a string container → runtime errors.
    - References undefined `is_cancelled()` (actual method is `_is_cancelled`).
    - Calls `_store_job_results()` which is not implemented.
    - Mixed concerns (DB CRUD, orchestration, progress, optimization) in a single class.
  - **Plan**:
    - Introduce `enum.Enum` for `JobStatus`, remove all `.value` usage.
    - Remove the earlier, overridden `list_jobs(limit=50)` function.
    - Rename calls to `_is_cancelled()` or implement `is_cancelled()` wrapper.
    - Replace `_store_job_results()` usage with `_update_job_status(..., result_data=...)` or implement the missing method.
    - Split into modules:
      - `tasks/job_store.py` (DB CRUD; list, get, delete, stats)
      - `tasks/backtest_runner.py` (backtest job execution)
      - `tasks/optimization_runner.py` (optimization execution)
      - Retain `job_runner.py` as thin facade and global singleton.

- **backend/app/services/dataset_service.py (~565 LOC)**
  - **Issues**: Monolithic service containing file IO, DB, quality analysis, validations, and helpers.
  - **Plan**:
    - Move analysis helpers to `services/datasets/dataset_analyzer.py`.
    - Move DB accessors to `services/datasets/dataset_repository.py`.
    - Keep `DatasetService` as an orchestrator calling analyzer + repo.
    - Centralize timestamp/column detection and JSON sanitation into shared utils.

- **backend/app/services/optimization_service.py (~458 LOC)**
  - **Issues**:
    - Calls non-existent `BacktestService.run_backtest_from_data(...)`.
    - Tightly couples to a direct `JobRunner()` instance; status handling assumes Enum `.value`.
  - **Plan**:
    - Switch to `BacktestService.run_backtest(data=csv_bytes, ...)` or `run_backtest_from_upload(...)`.
    - Use the global job runner singleton (via the API router or a shared accessor) for consistency.
    - Extract parameter-combination generation and analysis to `services/optimization/utils.py`.

- **backend/app/api/v1/backtests.py (~404 LOC)**
  - **Issues**: Contains repeated logic for dataset resolution, strategy ID resolution, and result shaping.
  - **Plan**:
    - Extract helpers: `resolve_dataset_path_or_id()`, `resolve_strategy_path()`, and `shape_backtest_response()` into `services/_helpers.py` or `api/_utils.py`.
    - Consider deprecating in-memory `results_store` endpoints after confirming no tests depend on them.

- **backend/app/services/backtest/backtest_service.py (~344 LOC)**
  - **Plan**: Mostly OK; ensure progress tracking and error handling remain cohesive. Consider moving CSV/bytes normalization logic into `ExecutionEngine` only.

- **backend/app/services/backtest/execution_engine.py (~416 LOC)**
  - **Plan**: Acceptable length. Optionally move `_process_equity_curve` and `_process_trades` into `ResultProcessor` to keep execution engine focused on running and validating.

- **backend/app/services/backtest/result_processor.py (~452 LOC)**
  - **Plan**: Acceptable; ensure reliance on `backtester.metrics` stays canonical. Consider moving DB write to a separate repository layer.

- **backend/app/api/v1/analytics.py (~340 LOC)**
  - **Plan**: Extract ETag/header logic to a small helper; keep routes lean.

- **backend/app/api/v1/strategies.py (~400 LOC)** and **backend/app/api/v1/datasets.py (~336 LOC)**, **backend/app/api/v1/optimization.py (~339 LOC)**
  - **Plan**: Similar extraction of shared request parsing/validation helpers. Replace direct `JobRunner()` with global accessor in optimization router.

- **backend/app/services/analytics/chart_generator.py (~402 LOC)** and other analytics modules (PerformanceCalculator ~307 LOC, RiskCalculator ~255 LOC, TradeAnalyzer ~352 LOC, DataFormatter ~221 LOC)
  - **Plan**: These are reasonable; keep as-is. Consider splitting `ChartGenerator` into submodules if new chart types grow.

---

## Duplicated/overlapping logic
- **Legacy vs Modular Analytics**: `analytics_service_legacy.py` duplicates chart and analytics logic now present in `analytics/*` modules. Only `get_chart_data()` is still needed. Refactor as described and remove duplicates.
- **`get_column_mapping`** appears both in legacy analytics and `DataFormatter`. Centralize on `DataFormatter.get_column_mapping()`.
- **Job progress + storage**: Similar responsibilities exist across `job_runner.py`, `backtest_service.ProgressCallback`, and `backtest/progress_tracker.py`. Consolidate on `ProgressTracker`.
- **Dataset and Strategy resolution**: Implemented in multiple routers (backtests, jobs). Centralize in shared helper(s).
- **Drawdown/returns computations**: Provided by both `ChartGenerator` and legacy analytics. Keep only `ChartGenerator`.

---

## Unused or dead code (candidates for removal)
- **`backend/app/services/backtest_service_legacy.py`**: Not referenced (the bridge imports are commented out). Safe to remove after confirming tests don’t import it.
- **Legacy methods in `analytics_service_legacy.py`**: Almost all besides `get_chart_data()` look unused by current routers. Remove after porting `get_chart_data()` to modular service.
- **`BacktestMetrics` SQLAlchemy model**: Not used by current services. Keep only if tests assert its presence; otherwise, consider removing or implementing proper persistence.
- **Earlier `list_jobs(self, limit=50)` in `job_runner.py`**: Overridden further down; dead code.

---

## Bugs and inconsistencies to fix
- **JobRunner API mismatches**:
  - Uses `JobStatus.PENDING.value` while `JobStatus` is a simple class of strings → AttributeError risk.
  - Calls `self.is_cancelled(job_id)` but only `_is_cancelled()` exists.
  - References `_store_job_results()` (missing definition). Should store via `_update_job_status(..., result_data=...)` or implement the function.
  - Two `list_jobs` definitions; the earlier one is dead and confusing.
- **Optimization paths**:
  - `OptimizationService._run_single_backtest()` calls `BacktestService.run_backtest_from_data(...)` which does not exist. Should call `run_backtest(data=csv_bytes, ...)` or `run_backtest_from_upload(...)`.
  - `backend/app/api/v1/optimization.py` instantiates a new `JobRunner()` and expects Enum `.value` in status; use global accessor and plain string statuses.
- **Router duplication**:
  - Engine option key bridging (`daily_profit_target` → `daily_target`) repeated across multiple routes; centralize to avoid drift.
  - Dataset path resolution logic duplicated between backtests and jobs routers; centralize via `utils/path_utils.resolve_dataset_path` and a small service helper.

---

## Proposed refactor plan (phased)

### Phase 1 – Safety and correctness (quick wins)
- Fix `OptimizationService` to call existing `BacktestService.run_backtest` with `data=csv_bytes`.
- Replace `JobRunner` string-class `JobStatus` with a real Enum, remove `.value` usages, and fix `is_cancelled` call.
- Remove the earlier (overridden) `list_jobs` method in `job_runner.py`.
- In `optimization` router, switch to global job runner accessor and treat statuses as strings.
- Centralize engine option bridging and dataset/strategy resolution in small helpers used by backtests/jobs routers.

### Phase 2 – De-duplication and modularization
- Port `get_chart_data()` out of legacy analytics into modular `analytics/analytics_service.py`, using `ChartGenerator` and a new `DataFetcher` helper.
- Delete unused legacy analytics methods and (optionally) the entire legacy module after verifying coverage.
- Consolidate progress logic on `ProgressTracker`; remove duplicate `ProgressCallback` classes.
- Split `dataset_service.py` into analyzer + repository submodules.

### Phase 3 – Structural cleanup
- Split `job_runner.py` into `job_store.py`, `backtest_runner.py`, and `optimization_runner.py`; keep `job_runner.py` as the thin facade/DI root.
- Extract router helpers to `api/_utils.py`; keep route functions concise and declarative.
- Optional: Move `ExecutionEngine` post-processing into `ResultProcessor` to reduce responsibilities.

### Phase 4 – Data model alignment (optional)
- Either implement `BacktestMetrics` persistence or remove the model to avoid confusion.
- If trades need persistence, add a `TradeRepository` and use it from `ResultProcessor.save_to_database`.

---

## Specific file-by-file notes
- **backend/app/main.py (~95 LOC)**: CORS list is verbose; consider env-driven configuration. Replace prints with `logging` in DB init.
- **backend/app/database/models.py (~255 LOC)**: Clear and organized. `init_db()` prints to stdout; prefer `logging`.
- **backend/app/api/v1/backtests.py**: Good validation and robust JSON parsing; factor common helpers; consider deprecating in-memory result storage.
- **backend/app/api/v1/analytics.py**: Solid; factor ETag headers into helper.
- **backend/app/api/v1/datasets.py**: Preview endpoint reads entire CSV; consider streaming/limit columns for very large files.
- **backend/app/api/v1/optimization.py**: Fix runner instantiation and status enum assumptions; centralize validation.
- **backend/app/services/backtest_service.py**: Bridge looks good; keep only what’s needed; rely on modular service.
- **backend/app/services/backtest/execution_engine.py**: Leans robust; defer serialization to `ResultProcessor` where possible.
- **backend/app/services/backtest/result_processor.py**: Canonical use of `backtester.metrics`; good JSON sanitation; consider repo split.
- **backend/app/services/analytics/**: Modular structure is strong; continue migrating away from legacy.
- **backend/app/utils/path_utils.py**: Useful cross-OS helpers; ensure routers/services consistently use `resolve_dataset_path`.

---

## Deletions and cleanup candidates (after verification)
- Remove `backend/app/services/backtest_service_legacy.py` if no tests import it.
- Remove dead `list_jobs` implementation in `job_runner.py`.
- Prune legacy analytics methods after `get_chart_data()` is ported.
- Consider removing `BacktestMetrics` model or implement its usage.

---

## Validation steps (manual)
- **Backend tests**: `pytest -c backend/pytest.ini -q`
- **Core tests**: `pytest tests -q`
- **Coverage (core)**: `pytest --cov=backtester -q`
- Ensure API smoke tests pass: `pytest -c backend/pytest.ini -q -k smoke`

---

## Suggested PR structure
- PR 1: Job runner fixes (Enum, missing methods, duplicate removal), and optimization service call fix.
- PR 2: Router helper extraction (dataset/strategy/engine options), replace direct runner instantiation.
- PR 3: Port `get_chart_data()` to modular analytics and delete legacy duplicates.
- PR 4: Split `dataset_service.py`; optional ExecutionEngine/ResultProcessor responsibility shift.
- PR 5: Optional model cleanup (`BacktestMetrics`) and trade persistence decision.

---

## Appendix: Largest files (approx LOC)
- `backend/app/services/analytics_service_legacy.py` ~1410
- `backend/app/tasks/job_runner.py` ~615
- `backend/app/services/dataset_service.py` ~565
- `backend/app/services/backtest/result_processor.py` ~452
- `backend/app/services/backtest/execution_engine.py` ~416
- `backend/app/api/v1/backtests.py` ~404
- `backend/app/services/analytics/chart_generator.py` ~402
- `backend/app/api/v1/strategies.py` ~400
- `backend/app/services/optimization_service.py` ~458
- `backend/app/services/analytics/analytics_service.py` ~460

These are the best candidates for targeted refactors to improve maintainability.
