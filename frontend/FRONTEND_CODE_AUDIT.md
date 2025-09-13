### Frontend Codebase Audit (trading-backtester-v1)

Date: 2025-09-13
Scope: `frontend/src/` (React + TypeScript + Vite)

---

## Executive Summary

- Overall quality is solid: modular UI primitives, typed services, good query patterns, dark-first styling, and error boundaries.
- Several files are long and can be split for maintainability.
- A few duplications and mixed patterns exist (two parameter forms, two analytics pages).
- Some debug logs, TODOs, mock/demo code remain in production pages.
- Widespread `any` usage in a few places can be tightened with shared types.

Recommended priorities (high → low):
- Refactor very long files (`Backtests.tsx`, `BacktestConfigForm.tsx`, `TradingViewChart.tsx`, `Strategies.tsx`, `Datasets.tsx`, `JobProgressTracker.tsx`).
- Remove debug `console.log` and resolve TODOs.
- Consolidate duplicate components (`StrategyParameters` vs `StrategyParameterForm`).
- Remove or clearly mark demo pages/components (e.g., `AnalyticsNew.tsx`, mock sections of `Datasets.tsx`).
- Reduce `any` types by leveraging `types/api.ts` and local interfaces.

---

## Long Files to Refactor with Proposed Plans

1) `src/pages/Backtests/Backtests.tsx` (~650+ LOC)
- Issues:
  - Large component handling data fetching, transformation, stats, filters, list rendering, and modals.
  - Debug `console.log` statements; unimplemented TODO for report download.
  - Inline mappers/formatters add cognitive load.
- Refactor Plan:
  - Extract hooks: `useBacktestsList()` (fetch/normalize/sort), `useBacktestStats(backtests)`.
  - Move UI fragments to components: `BacktestCard`, `BacktestFilterTabs`, `BacktestStatsRow`.
  - Create `formatters.ts` for `formatDuration`, `getStatusIcon/Variant`, `getReturnColor`.
  - Implement report download via `BacktestService.getBacktestResults()` then CSV/HTML export util.
  - Remove debug logs.

2) `src/components/backtests/BacktestConfigForm.tsx` (~600+ LOC)
- Issues:
  - Monolithic form (strategy, dataset, config, parameters) with bespoke rendering logic.
  - Uses local `Strategy`/`Dataset` shapes; some `any` in parameter rendering.
- Refactor Plan:
  - Split into subcomponents: `StrategyPicker`, `DatasetPicker`, `CapitalRiskFields`, `ParametersGrid`.
  - Extract parameter field rendering to `ParameterField` with strict `ParameterSchema` types from `types/api.ts`.
  - Reuse list fetching via dedicated hooks `useStrategies`, `useDatasets`.
  - Move validations into a small `validators.ts`.

3) `src/components/charts/TradingViewChart.tsx` (~530 LOC)
- Issues:
  - Combines chart setup, resize handling, markers plugin, indicators, controls, and downloads.
  - Some `any` typings and inline options blocks.
- Refactor Plan:
  - Split: `useTradingViewChart` (init, series refs, resize), `ChartControls` (buttons), `useIndicators` (lines), `useSeriesMarkers` (plugin).
  - Extract `getChartOptions`, `getCandlestickOptions` into `chartOptions.ts` and type `timeFormatter`.
  - Replace `any` with `UTCTimestamp`, `SeriesMarker<UTCTimestamp>`, and explicit types for indicators.

4) `src/pages/Strategies/Strategies.tsx` (~450+ LOC)
- Issues:
  - Contains list, filters, stats loading, detail navigation, and local backtest modal configuration.
- Refactor Plan:
  - Extract `useStrategiesData` (list + stats) and `StrategiesGrid` component.
  - Move search/filter UI into `StrategiesToolbar`.
  - Keep detail routing; favor reusing `StrategyDetailView` (already exists).

5) `src/pages/Datasets/Datasets.tsx` (~420+ LOC)
- Issues:
  - Page mixes mock datasets, upload modal, preview modal, and stats cards.
  - Uses `react-hot-toast` directly instead of `showToast` wrapper.
- Refactor Plan:
  - Replace mock data with `DatasetService.listDatasets()`; move preview to `DatasetPreviewModal.tsx`.
  - Extract `UploadDatasetModal` to `components/datasets/`.
  - Use unified `showToast` from `components/ui/Toast` for consistency.

6) `src/components/backtests/JobProgressTracker.tsx` (~350+ LOC)
- Issues:
  - Polling, formatting, actions, and rendering in one file.
- Refactor Plan:
  - Extract `useJobPolling(job)` to encapsulate setInterval and ETA logic.
  - Create `JobProgressBar` and `JobActionsBar` components.
  - Share status helpers with `JobsList/JobCard.tsx` to avoid duplication.

7) Other medium-large files
- `src/components/strategies/StrategyDiscovery.tsx` (~320 LOC): Split API actions (discover/register) into a hook; break list item into `StrategyDiscoveryItem`.
- `src/components/strategies/StrategyParameterForm.tsx` (~270 LOC): Keep; but consolidate with `StrategyParameters` (see duplicates).

---

## Duplications and Consolidation

- Parameter Forms
  - `components/strategies/StrategyParameters.tsx` and `components/strategies/StrategyParameterForm.tsx` overlap in purpose.
  - Recommendation: Keep `StrategyParameterForm.tsx` (typed with `ParameterSchema`), deprecate `StrategyParameters.tsx` and migrate usages (`BacktestModal/StrategySection.tsx`) to the typed form.

- Status helpers duplication
  - `getStatusIcon/Color/Variant` are implemented in multiple files (`Backtests.tsx`, `JobProgressTracker.tsx`, `JobsList/JobCard.tsx`, `Analytics.tsx`).
  - Recommendation: Centralize in `src/utils/status.ts` and import where needed.

- Analytics pages
  - `pages/Analytics/Analytics.tsx` (current) and `pages/Analytics/AnalyticsNew.tsx` (demo with mock select) co-exist.
  - Recommendation: Remove `AnalyticsNew.tsx` if unused by routes, or clearly mark as demo and exclude from prod build. Current router uses `Analytics.tsx` only.

---

## Unused or Demo/Mock Code

- `pages/Analytics/AnalyticsNew.tsx`: Not routed in `App.tsx`; appears to be a legacy/demo page. Remove or move under `src/demo/`.
- `pages/Datasets/Datasets.tsx`: Contains mock dataset list and preview; replace with real `DatasetService` calls. Consider moving preview modal into `components/datasets/`.
- Debug logs in `pages/Backtests/Backtests.tsx`: Remove `console.log` lines 67, 128, 191, 285, 289.
- TODO in `Backtests.tsx` line 358: Implement report download (see plan above) or remove button.

---

## Any/Loose Typings Hotspots

- Services/components using `any`:
  - `services/backtest.ts` (engineOptions and return shapes), `services/analytics.ts` compare payloads, several mapping areas in pages.
  - Components: `BacktestConfigForm` parameter rendering, `TradingViewChart` formatters, charts expecting `any` traces.
- Recommendations:
  - Reuse `types/api.ts` for `BacktestResult`, `Job`, `ParameterSchema`, `PaginatedResponse<T>` across services and pages.
  - Introduce `BacktestListItem` and `BacktestDisplay` types centrally in `src/types/backtest.ts` and import.
  - Define `IndicatorLine` and `TradeMarker` types in a shared `types/chart.ts` and import in `TradingViewChart.tsx`.

---

## Inconsistencies and Minor Smells

- Toasts: Prefer `showToast` wrapper over direct `react-hot-toast` (e.g., in `pages/Datasets/Datasets.tsx`).
- Hardcoded fallback dataset label: `NIFTY Aug 2025 (1min)` in Backtests pages; move to a constant or remove.
- Mixed selection UIs: `BacktestConfigForm` uses searchable dropdowns; `BacktestModal/StrategySection` uses simple `<select>`. Consider converging on one UX.
- Two chart stacks (Plotly and Lightweight) are fine, but ensure data contracts are typed and normalized.

---

## Potentially Unused Files

- `pages/Analytics/AnalyticsNew.tsx`: Unused by router; safe to remove or mark demo.
- `components/analytics/index.ts`: Thin barrel; fine to keep. No action.

---

## Concrete Cleanup Checklist

- Remove debug logs and TODO:
  - `pages/Backtests/Backtests.tsx`: delete console logs; implement or remove report download.
- Consolidate parameter forms:
  - Replace `StrategyParameters` usage in `BacktestModal/StrategySection.tsx` with `StrategyParameterForm` and delete the former after migration.
- Refactor long files per plans above, in small PRs:
  - Backtests page → hooks + subcomponents + utils.
  - BacktestConfigForm → 4 subcomponents + validators.
  - TradingViewChart → hooks (init, indicators, markers) + controls.
- Replace mock dataset code with `DatasetService` and move preview modal out of page file.
- Reduce `any` by importing API types; add lightweight `types/chart.ts`.
- Standardize toast usage to `showToast`.

---

## Suggested File/Folder Additions

- `src/hooks/`:
  - `useBacktestsList.ts`, `useBacktestStats.ts`, `useStrategies.ts`, `useDatasets.ts`, `useJobPolling.ts`.
- `src/utils/`:
  - `formatters.ts` (date, duration, returns), `status.ts` (icon/color/variant helpers), `chartOptions.ts`.
- `src/types/`:
  - `chart.ts` (candles, indicators, markers), `backtest.ts` (list/display models).
- `src/components/backtests/`:
  - `BacktestCard.tsx`, `BacktestFilterTabs.tsx`, `BacktestStatsRow.tsx`.
- `src/components/datasets/`:
  - `UploadDatasetModal.tsx`, `DatasetPreviewModal.tsx`.

---

## Removal Candidates (pending confirmation)

- `pages/Analytics/AnalyticsNew.tsx` (legacy/demo).
- `components/strategies/StrategyParameters.tsx` (superseded by `StrategyParameterForm.tsx`).

---

## Notes on Testing

- Update or add tests for new hooks and components, especially for data mappers and validators.
- Keep MSW handlers aligned if API shapes evolve; expand tests in `services/__tests__/` accordingly.

---

## Closing

These changes reduce file complexity, remove duplication, and tighten typings, improving maintainability and onboarding speed. Implement in small, scoped PRs to keep review manageable.


