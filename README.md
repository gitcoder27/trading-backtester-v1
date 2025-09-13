# Trading Backtester Pro 🚀

High-performance, modular backtesting framework with a FastAPI backend and a modern React + TypeScript frontend. The previous Streamlit app is now legacy and archived.

## What’s Inside

- Core backtester engine (Numba-optimized) with rich metrics and HTML reporting
- FastAPI backend exposing backtesting, datasets, analytics, and optimization APIs
- React + Vite frontend for interactive analysis and workflow
- Strategy library with multiple examples (EMA scalpers, RSI, BBands, etc.)

Legacy notice: The old Streamlit app is no longer used. It remains available under `archive/streamlit-app/` for reference.

---

## Performance Highlights

- Processes large intraday datasets quickly using vectorized operations + numba
- Real-time progress and robust analytics via the backend services
- HTML reports, trade logs, and detailed performance metrics available from the engine
- Phase 2 analytics improvements:
  - Server-side downsampling for charts via `max_points` to keep payloads small
  - Selective performance sections with server caching for faster loads
  - ETag/Last-Modified headers on analytics endpoints + GZip compression

---

## Project Structure

```
backtester/   # Core engine, metrics, reporting, plotting
strategies/   # User strategies (snake_case.py with CamelCaseStrategy)
backend/      # FastAPI API (entry: backend/app/main.py)
frontend/     # React + TypeScript app (Vite)
tests/        # Pytest suite for core backtester
data/         # Sample CSVs (avoid large/private data)
archive/      # Legacy Streamlit app and docs
```

---

## Quickstart (WSL2 Ubuntu)

Recommended to run inside a virtual environment within WSL2.

```bash
# From project root in Ubuntu WSL2
python3 -m venv venv
source venv/bin/activate

# Install Python deps (core + API)
pip install -r requirements.txt
pip install -r backend/requirements.txt

# Frontend deps
npm -C frontend install
```

---

## Run (Development)

### Backend (FastAPI)

```bash
uvicorn backend.app.main:app --reload
# Open http://localhost:8000 (Docs: http://localhost:8000/docs)
```

### Frontend (React + Vite)

```bash
npm -C frontend run dev
# Open the printed localhost URL (typically http://localhost:5173)
```

---

## Testing

- Core tests: `pytest tests -q`
- Core coverage: `pytest --cov=backtester -q`
- Backend tests: `pytest -c backend/pytest.ini -q` (or `cd backend && pytest -q`)
- Frontend: `npm -C frontend run test:coverage`

---

## Analytics API (Phase 2 Updates)

Endpoints now support selective sections and downsampling for improved performance.

- Performance summary (selective compute + server cache)
  - `GET /api/v1/analytics/performance/{backtest_id}?sections=basic_metrics&sections=advanced_analytics`
  - Notes: accepts repeated `sections` keys; caches computed sections under `Backtest.results.analytics_summary`. Returns `ETag` and `Last-Modified` headers; always responds 200 with a body.

- Charts (downsampled)
  - `GET /api/v1/analytics/charts/{backtest_id}?chart_types=equity&chart_types=drawdown&max_points=1500`
  - Focused endpoints: `/equity`, `/drawdown`, `/trades` each accept `max_points`.
  - Notes: downsampling preserves the last point and samples evenly across the series.

- TradingView chart data
  - `GET /api/v1/analytics/chart-data/{backtest_id}?include_trades=true&include_indicators=true&max_candles=3000&start=YYYY-MM-DD&end=YYYY-MM-DD&tz=Zone`
  - Notes: `max_candles` supports 1–200000 (1 is used by the UI for a prime query).

Curl examples

```bash
curl -s "http://localhost:8000/api/v1/analytics/performance/42?sections=basic_metrics&sections=risk_metrics" | jq .

curl -s "http://localhost:8000/api/v1/analytics/charts/42/equity?max_points=600" | jq .

curl -s "http://localhost:8000/api/v1/analytics/charts/42?chart_types=equity&chart_types=drawdown&max_points=1500" | jq .
```

Frontend defaults

- Overview quick charts request `maxPoints≈600`; Analytics tab charts request `≈1500`.
- Performance metrics request a full set of sections on first view and then rely on server cache.

---

## CLI Usage (Optional)

Run backtests directly from the command line and print full performance metrics.

- Basic: `python cli.py --file data/your.csv`
- With strategy: `python cli.py --file data/your.csv --strategy strategies.ema50_scalper.EMA50ScalperStrategy`
- Dates: `--start 2025-08-01 --end 2025-08-15`
- Engine options: `--initial-cash 100000 --lots 1 --option-delta 0.5 --fee-per-trade 4 --intraday`
- Strategy params: repeat `--param key=value` or `--params-json '{"ema_period":50}'`
- Output JSON: `--output-json results.json`

Default strategy: `strategies.rsi_midday_reversion_scalper.RSIMiddayReversionScalper`.

Outputs include Performance Metrics, Advanced Analytics, and Risk Metrics; equity curve and trades can be saved with `--output-json`.

Example

```bash
# EMA50 scalper over a date window with engine options
python cli.py \
  --file data/nifty_2025_1min_08Aug_12Aug.csv \
  --strategy strategies.ema50_scalper.EMA50ScalperStrategy \
  --start 2025-08-08 --end 2025-08-12 \
  --initial-cash 100000 --lots 1 --option-delta 0.5 --fee-per-trade 4 \
  --output-json results.json

# Or RSI strategy with params
python cli.py \
  --file data/nifty_2025_1min_08Aug_12Aug.csv \
  --strategy strategies.rsi_midday_reversion_scalper.RSIMiddayReversionScalper \
  --param rsi_period=14 --param atr_period=14
```

---

## Adding New Strategies

1) Create a new file in `strategies/` (e.g., `my_strategy.py`).
2) Create a class that inherits from `StrategyBase` (`backtester.strategy_base`).
3) Implement `generate_signals(self, data: pd.DataFrame) -> pd.DataFrame` returning a `signal` column (`1` long, `-1` short, `0` none).
4) Keep strategies small, pure, deterministic; prefer logging over print.

---

## Engine Outputs

- Trade logs: CSV export for all trades
- HTML reports: rich performance summary with charts and tables

---

## Data Format

CSV should include at minimum:
- `timestamp` (parseable by pandas)
- `open`, `high`, `low`, `close`

---

## Troubleshooting

- Environment: Ensure you install Python packages inside a WSL2 venv (don’t use global installs).
- Backend: If CORS errors occur, verify the frontend URL matches the allowed origins in `backend/app/main.py`.
- Tests: Backend tests require FastAPI deps from `backend/requirements.txt`.
- Streamlit: The legacy Streamlit UI is archived and not used in this setup.
- Analytics: If you see 422 on analytics endpoints, ensure array params use repeated keys (e.g., `&sections=a&sections=b`), and that `max_candles` is within allowed bounds (1–200000).

---

## Additional Docs

- Backend details: `backend/README.md`
- Frontend details: `frontend/README_COMPREHENSIVE.md`
- Handoff: `docs/HANDOFF.md` (Phase 2 summary, next steps)

---

## License

MIT License. See `LICENSE` for details.
