# AI Agent Instructions for Trading Backtester

## Architecture Overview

This is a full-stack trading strategy backtesting platform with three layers:
- **Core Engine** (`backtester/`) - Numba-optimized vectorized backtesting with bar-by-bar fallback
- **Backend API** (`backend/`) - FastAPI service with background job execution, SQLAlchemy persistence
- **Frontend** (`frontend/`) - React + TypeScript (Vite), React Query, Zustand state management

### Critical Data Flow
1. User uploads CSV → `Dataset` model persisted to SQLite
2. User selects strategy + params → `BacktestJob` created → threaded execution via `JobRunner`
3. `BacktestRunner` loads strategy → calls `engine.py` → writes `Backtest` + `Trade` + `BacktestMetrics`
4. Frontend polls `/api/v1/jobs/{id}` for progress → fetches results via `/api/v1/backtests/{id}`

## Strategy Development Pattern

**File:** `strategies/my_strategy.py` | **Class:** `MyStrategy(StrategyBase)`

Required methods:
```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    """Return DataFrame with 'signal' column: 1=long, -1=short, 0=none"""
    
def should_exit(self, position: str, row: pd.Series, entry_price: float) -> tuple[bool, str]:
    """Return (exit_now: bool, exit_reason: str) for bar-by-bar exits"""
```

Optional:
```python
def indicator_config(self) -> list[dict]:
    """Return list of indicator definitions for frontend charting"""
    return [{"name": "ema_20", "type": "line", "color": "blue"}]
```

**Critical:** Strategies must be deterministic, use `logging` (never `print`), and handle missing data gracefully.

## Development Workflows

### Setup (macOS/WSL2)
```bash
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt -r backend/requirements.txt
npm -C frontend install
```

### Running Services
**Backend:** `uvicorn backend.app.main:app --reload` (port 8000)  
**Frontend:** `npm -C frontend run dev` (port 5173)  
**Do NOT start servers unless explicitly requested** - assume user has them running.

### Testing Commands
- Core: `pytest tests -q` | Coverage: `pytest --cov=backtester -q`
- Backend: `pytest -c backend/pytest.ini -q`
- Frontend: `CI=1 npm -C frontend run test:coverage --silent -- --run`
  - **Critical:** Always use `--run` or `CI=1` to avoid watch-mode hangs

### Search Patterns
**Use `rg` (ripgrep), never `grep`:**
- Content search: `rg "pattern"`
- Find files: `rg --files | rg "name"` or `fd pattern`
- Language filter: `rg -t python "def"`

## Critical Patterns & Conventions

### Backend Service Architecture
**Services pattern:** Facade (`backtest_service.py`) → modular components (`backtest/execution_engine.py`, `backtest/result_processor.py`)
- Business logic in `services/`, routers delegate to services
- Background jobs: `JobRunner` submits to `ThreadPoolExecutor`, persists via `JobStore`
- Progress: `ProgressCallback` throttles DB writes (1s min interval)

### Frontend State Management
- **React Query:** All API calls via `@tanstack/react-query` with `queryClient.ts` config
- **Zustand:** UI state (`themeStore`, `uiStore`, `settingsStore`), dark mode enforced globally
- **API wrapper:** `services/api.ts` handles errors, repeated array params for FastAPI `List[str]`

### Database Models
SQLite at `backend/database/backtester.db`:
- `BacktestJob` → job metadata, progress, status (pending/running/completed/failed)
- `Backtest` → final results, metrics, equity curve JSON
- `Trade` → individual trades with PnL, entry/exit times
- `BacktestMetrics` → performance stats (Sharpe, drawdown, win rate, etc.)

### Engine Execution Modes
1. **Vectorized (fast):** Numba JIT when strategy only uses `generate_signals()`
2. **Bar-by-bar (flexible):** Fallback when `should_exit()` requires row-level logic
   - Supports daily profit targets, time-based exits, complex conditions

### Analytics Performance (Phase 2)
- **Selective sections:** `?sections=basic_metrics&sections=advanced_analytics` (repeated params)
- **Downsampling:** `?max_points=1500` on chart endpoints to reduce payload
- **Caching:** Results stored in `Backtest.results.analytics_summary` (JSON column)
- **Headers:** ETag/Last-Modified for cache validation, GZip compression via middleware

## Code Style Enforcement

**Python:** PEP 8, 4-space indent, type hints mandatory  
**TypeScript:** ESLint + Prettier, `PascalCase` components, `camelCase` functions  
**Strategies:** `snake_case.py` files, `CamelCaseStrategy` classes

**Naming examples:**
- Backend service: `backtest_service.py` → `BacktestService`
- Frontend component: `BacktestCard.tsx` → `export function BacktestCard()`
- Frontend hook: `useBacktest.ts` → `export function useBacktest()`

## Best Practices

### Code Organization
- **Files < 300 lines:** Split large files into focused modules (see `backend/app/services/backtest/` modular refactor)
- **Functions < 30 lines:** Break down complex logic into smaller, testable units
- **SOLID Principles:** Single responsibility (e.g., `ProgressCallback` only throttles), extend via inheritance (`StrategyBase`)
- **DRY:** Extract common logic to utilities (`optimization_utils.py`, `data_loader.py`)

### Clean Code Rules
- Use descriptive names: `calculate_sharpe_ratio()` not `calc_sr()`
- Guard clauses over nested ifs: Early returns for invalid states
- Type hints mandatory: All function signatures must include types
- No `print()`: Use `logging` module for all output
- Dataclasses for configs: See `ema_rsi_swing.py` StrategyParams pattern

### Error Handling
- Validate inputs early: Check for empty data, missing params at function start
- Specific exceptions: `StrategyLoadError`, `ValidationError` over generic `Exception`
- Database transactions: Always use try/commit/rollback pattern with `session.flush()` for FK dependencies
- Handle edge cases: Empty lists, zero division, missing data explicitly

### Performance
- Vectorize: Use Pandas/NumPy operations over loops (`df['close'].pct_change()`)
- Numba JIT: Use `@jit(nopython=True)` for hot loops (see `engine.py`)
- Cache: `@lru_cache` for expensive computations, server-side caching in `analytics_summary`
- Lazy load: Paginate large queries (`limit`/`offset`)

### Security
- Never hardcode secrets: Use env vars via `get_settings()`
- Validate inputs: Check types, ranges, prevent path traversal
- Use ORM: SQLAlchemy parameterizes queries (no string concatenation)

### Testing
- AAA pattern: Arrange, Act, Assert
- Parametrize edge cases: Empty data, nulls, boundaries
- Mock dependencies: Use `Mock()` for external services, MSW for API calls
- 90% coverage: Focus on critical paths (engine, services)

## Testing Requirements

- **Coverage target:** 90%+ in modified areas
- **Fixtures:** Minimal, prefer parametrize over complex setup
- **Frontend MSW:** Mock API responses in `src/test/mocks/`
- **Backend isolation:** Use `TestingSessionLocal` from `conftest.py`
- **Numba coverage:** Set `NUMBA_DISABLE_JIT=1` (see `tests/conftest.py`)

## Common Pitfalls

1. **Frontend array params:** Use repeated keys (`url.searchParams.append()`) not arrays
2. **Strategy side effects:** Avoid mutable state, use pure functions in `generate_signals()`
3. **Background job cancellation:** Always check `cancel_event.is_set()` in long loops
4. **CSV loading:** Use `data_loader.load_csv()` with dtype hints, not raw `pd.read_csv()`
5. **Frontend tests:** Must use `--run` flag or `CI=1` env var to prevent watch hang

## Git Conventions

Commit format: `<type>: <description>` (feat, fix, refactor, test, docs, chore)  
Example: `feat: add EMA crossover strategy with RSI filter`

## Reference Files for Patterns

- Strategy template: `strategies/ema_rsi_swing.py`
- Service pattern: `backend/app/services/backtest_service.py`
- Background job: `backend/app/tasks/job_runner.py`
- Frontend hook: `frontend/src/pages/Backtests/useBacktests.ts`
- API wrapper: `frontend/src/services/api.ts`
- Engine core: `backtester/engine.py` (vectorized + bar-by-bar modes)
