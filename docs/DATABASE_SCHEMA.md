# Database Schema Overview

This document provides an overview of the SQLite schema used by the backend service. It summarizes tables, columns, data types, and high‑level relationships inferred from the SQLAlchemy models in `backend/app/database/models.py`.

Note: The current models define indexes via `index=True` on some columns, and use integer IDs as implicit foreign keys without explicit `ForeignKey` constraints.

## Tables

### backtest_jobs
- id: Integer (PK, indexed)
- status: String(50) — one of: pending, running, completed, failed, cancelled
- strategy: String(200) — fully-qualified strategy path or name
- strategy_params: JSON — strategy parameters
- engine_options: JSON — engine/run configuration
- dataset_path: String(500) — resolved path to dataset used
- progress: Float — 0.0 to 1.0
- current_step: String(200)
- total_steps: Integer
- created_at: DateTime (UTC)
- started_at: DateTime (UTC)
- completed_at: DateTime (UTC)
- result_data: Text — JSON string with run results (equity, trades, metrics)
- error_message: Text
- estimated_duration: Float (seconds)
- actual_duration: Float (seconds)

Relationships
- One-to-many with `trades` via `trades.backtest_job_id` (implicit)
- One-to-one with `backtest_metrics` via `backtest_metrics.backtest_job_id` (implicit unique)

Indexes
- Primary key on `id`
- Additional indexes: `id` (implicit), others not explicitly defined beyond `index=True` flags

---

### trades
- id: Integer (PK, indexed)
- backtest_job_id: Integer (indexed) — references `backtest_jobs.id`
- entry_time: DateTime (UTC, required)
- exit_time: DateTime (UTC, optional)
- entry_price: Float (required)
- exit_price: Float
- quantity: Float (required)
- side: String(10) — 'long' | 'short'
- pnl: Float
- pnl_percent: Float
- holding_time_minutes: Float
- entry_signal: String(100)
- exit_signal: String(100)
- max_profit: Float
- max_loss: Float
- created_at: DateTime (UTC)

Relationships
- Many trades belong to one backtest job (`backtest_jobs.id`)

Indexes
- Primary key on `id`
- Index on `backtest_job_id`

---

### backtest_metrics
- id: Integer (PK, indexed)
- backtest_job_id: Integer (indexed, unique) — references `backtest_jobs.id`
- total_return: Float
- total_return_percent: Float
- sharpe_ratio: Float
- sortino_ratio: Float
- max_drawdown: Float
- max_drawdown_percent: Float
- total_trades: Integer
- winning_trades: Integer
- losing_trades: Integer
- win_rate: Float
- profit_factor: Float
- largest_win: Float
- largest_loss: Float
- average_win: Float
- average_loss: Float
- average_holding_time: Float (minutes)
- max_consecutive_wins: Integer
- max_consecutive_losses: Integer
- volatility: Float
- var_95: Float
- cvar_95: Float
- total_trading_days: Integer
- profitable_days: Integer
- daily_target_hit_rate: Float
- created_at: DateTime (UTC)

Relationships
- One record per backtest job (1:1), keyed by `backtest_job_id`

Indexes
- Primary key on `id`
- Unique index on `backtest_job_id`

---

### datasets
- id: Integer (PK, indexed)
- name: String(200) — dataset display name
- filename: String(200) — original filename
- file_path: String(500) — absolute or project‑relative path
- file_size: Integer (bytes)
- rows_count: Integer — number of rows (exposed via property `rows`)
- columns: JSON — list of column names
- timeframe: String(20) — e.g., '1min', '5min'
- start_date: DateTime (UTC)
- end_date: DateTime (UTC)
- missing_data_pct: Float
- data_quality_score: Float
- has_gaps: Boolean
- timezone: String(50)
- symbol: String(20)
- exchange: String(50)
- data_source: String(100)
- quality_checks: JSON — results of validation
- backtest_count: Integer (default 0)
- last_used: DateTime (UTC)
- created_at: DateTime (UTC)
- last_accessed: DateTime (UTC)

Relationships
- Referenced by backtests via `backtests.dataset_id` (implicit)

Indexes
- Primary key on `id`
- Various columns marked `index=True`

---

### strategies
- id: Integer (PK, indexed)
- name: String(200)
- module_path: String(500) — import path to module
- class_name: String(200) — strategy class name
- description: Text
- parameters_schema: JSON — parameter schema
- default_parameters: JSON
- total_backtests: Integer (default 0)
- avg_performance: Float
- last_used: DateTime (UTC)
- created_at: DateTime (UTC)
- is_active: Boolean (default True)

Relationships
- Can be linked to backtests logically via names/paths (no explicit FK)

Indexes
- Primary key on `id`

---

### backtests
- id: Integer (PK, indexed)
- strategy_name: String(200)
- strategy_params: JSON
- dataset_id: Integer (indexed)
- status: String(50) — default 'completed'
- results: JSON — equity_curve, trades, metrics
- created_at: DateTime (UTC)
- completed_at: DateTime (UTC)

Relationships
- Many backtests map to one dataset via `dataset_id`
- Conceptually related to a `backtest_job` that produced it, but no direct FK present in the model

Indexes
- Primary key on `id`
- Index on `dataset_id`

## Relationship Diagram (Conceptual)

backtest_jobs (1) ─── (N) trades
backtest_jobs (1) ─── (1) backtest_metrics
datasets     (1) ─── (N) backtests

Note: Foreign keys are implicit in code; SQLite schema does not declare `FOREIGN KEY` constraints in the current models file.

## Notes and Recommendations
- If strict relational integrity is desired, add explicit `ForeignKey` constraints for:
  - `trades.backtest_job_id → backtest_jobs.id`
  - `backtest_metrics.backtest_job_id → backtest_jobs.id`
  - `backtests.dataset_id → datasets.id`
- Consider adding indexes on frequently filtered columns such as `backtest_jobs.status`, `backtest_jobs.created_at`, and `trades.backtest_job_id` if query volume grows.
- Migrations: adopt Alembic to manage schema changes over time.

