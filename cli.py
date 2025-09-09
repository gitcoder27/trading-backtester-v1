"""
CLI for running backtests without the web UI.

Examples:
  python cli.py \
    --file data/sample.csv \
    --strategy strategies.rsi_midday_reversion_scalper.RSIMiddayReversionScalper \
    --param rsi_period=14 --param atr_period=14 \
    --initial-cash 100000 --lots 2 --option-delta 0.5 --fee-per-trade 4 --intraday

Outputs a metrics summary to stdout. Optionally writes full JSON results.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

import pandas as pd

# Core services
from backend.app.services.backtest_service import BacktestService

# Optional additional analytics for CLI detail
from backend.app.services.analytics.performance_calculator import PerformanceCalculator
from backend.app.services.analytics.risk_calculator import RiskCalculator

from backtester.data_loader import load_csv
from backtester.metrics import daily_profit_target_stats


DEFAULT_STRATEGY = (
    "strategies.rsi_midday_reversion_scalper.RSIMiddayReversionScalper"
)


def parse_kv_pairs(pairs: List[str]) -> Dict[str, Any]:
    """Parse repeated key=value pairs with basic type coercion."""
    out: Dict[str, Any] = {}
    for item in pairs or []:
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        out[key.strip()] = coerce_value(value.strip())
    return out


def coerce_value(v: str) -> Any:
    """Best-effort type coercion for CLI values."""
    s = v.strip()
    # bool
    if s.lower() in {"true", "false"}:
        return s.lower() == "true"
    # int
    try:
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            return int(s)
    except Exception:
        pass
    # float
    try:
        return float(s)
    except Exception:
        pass
    # JSON literal
    try:
        if (s.startswith("{") and s.endswith("}")) or (s.startswith("[") and s.endswith("]")):
            return json.loads(s)
    except Exception:
        pass
    return s


def filter_date_range(df: pd.DataFrame, start: str | None, end: str | None) -> pd.DataFrame:
    if start is None and end is None:
        return df
    if "timestamp" not in df.columns:
        return df
    data = df.copy()
    ts = pd.to_datetime(data["timestamp"], errors="coerce")
    # Normalize tz to naive UTC for consistent comparisons
    try:
        tz = getattr(ts.dt, "tz", None)
        if tz is not None:
            ts = ts.dt.tz_convert("UTC").dt.tz_localize(None)
    except Exception:
        # If tz_convert fails for any reason, best-effort drop tz
        try:
            ts = ts.dt.tz_localize(None)
        except Exception:
            pass
    data["timestamp"] = ts
    if start:
        data = data[data["timestamp"] >= pd.to_datetime(start)]
    if end:
        data = data[data["timestamp"] <= pd.to_datetime(end)]
    return data


def format_section(title: str) -> str:
    return f"\n=== {title} ===\n"


def print_metrics(metrics: Dict[str, Any], title: str = "Metrics") -> None:
    print(format_section(title))
    # Stable ordering for common keys, then the rest
    preferred = [
        "final_equity",
        "total_return",
        "total_return_pct",
        "sharpe_ratio",
        "max_drawdown",
        "max_drawdown_pct",
        "win_rate",
        "profit_factor",
        "total_trades",
        "largest_winning_trade",
        "largest_losing_trade",
        "max_consecutive_wins",
        "max_consecutive_losses",
        "average_holding_time",
        "trading_sessions_days",
        "data_points",
    ]
    seen = set()
    for k in preferred:
        if k in metrics:
            print(f"{k}: {metrics[k]}")
            seen.add(k)
    for k in sorted(metrics.keys()):
        if k not in seen:
            print(f"{k}: {metrics[k]}")


def main(argv: List[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run backtests from the CLI")
    parser.add_argument("--file", "-f", required=True, help="Path to CSV data file")
    parser.add_argument(
        "--strategy",
        "-s",
        default=DEFAULT_STRATEGY,
        help="Strategy path module.Class (default: %(default)s)",
    )
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        help="Strategy parameter (repeatable) as key=value",
    )
    parser.add_argument(
        "--params-json",
        help="Strategy parameters as JSON string (overrides --param)",
    )
    parser.add_argument(
        "--timeframe",
        default="1min",
        help="Resample timeframe passed to loader (e.g., 1min, 5min)",
    )
    parser.add_argument("--start", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", help="End date (YYYY-MM-DD)")

    # Engine options
    parser.add_argument("--initial-cash", type=float, default=None)
    parser.add_argument("--lots", type=float, default=None)
    parser.add_argument("--option-delta", type=float, default=None)
    parser.add_argument("--fee-per-trade", type=float, default=None)
    parser.add_argument("--slippage", type=float, default=None)
    parser.add_argument("--intraday", action="store_true")
    parser.add_argument("--daily-target", type=float, default=None)

    # Output options
    parser.add_argument(
        "--output-json",
        help="Path to write full JSON results (metrics, equity_curve, trades)",
    )

    args = parser.parse_args(argv)

    # Build strategy params
    if args.params_json:
        try:
            strategy_params = json.loads(args.params_json)
        except json.JSONDecodeError as e:
            print(f"Invalid --params-json: {e}")
            return 2
    else:
        strategy_params = parse_kv_pairs(args.param)

    # Build engine options
    engine_options: Dict[str, Any] = {}
    for name in [
        "initial_cash",
        "lots",
        "option_delta",
        "fee_per_trade",
        "slippage",
        "daily_target",
    ]:
        val = getattr(args, name.replace("_", "-"), None) if False else getattr(args, name)
        if val is not None:
            engine_options[name] = val
    if args.intraday:
        engine_options["intraday"] = True

    # Load data with timeframe and date filters
    df = load_csv(args.file, timeframe=args.timeframe)
    df = filter_date_range(df, args.start, args.end)

    # Run backtest
    service = BacktestService()
    result = service.run_backtest(
        data=df,
        strategy=args.strategy,
        strategy_params=strategy_params,
        engine_options=engine_options,
    )

    if not result or not result.get("success", False):
        print("Backtest failed")
        return 1

    # Extract metrics and print
    metrics = result.get("metrics", {})
    print(format_section("Backtest Summary"))
    print(f"Strategy: {args.strategy}")
    print(f"Data points: {len(df)} | From: {df['timestamp'].min()} | To: {df['timestamp'].max()}")
    # Start/Final equity summary for parity with legacy CLI
    equity_df = pd.DataFrame(result.get("equity_curve", []))
    try:
        start_amount = float(equity_df['equity'].iloc[0]) if not equity_df.empty else float(metrics.get('final_equity') or 0)
        final_amount = float(metrics.get('final_equity') or (equity_df['equity'].iloc[-1] if not equity_df.empty else 0))
        print(f"Start Amount: {start_amount:.2f}")
        print(f"Final Amount: {final_amount:.2f}")
    except Exception:
        pass
    print_metrics(metrics, title="Performance Metrics")

    # Add optional advanced analytics (volatility/sortino/var etc.)
    trades_df = pd.DataFrame(result.get("trade_log") or result.get("trades") or [])
    perf_calc = PerformanceCalculator()
    risk_calc = RiskCalculator()
    adv = perf_calc.compute_basic_analytics(equity_df, trades_df)
    risk = risk_calc.compute_risk_metrics(equity_df)
    # Show trade count if available
    try:
        trade_count = int(len(trades_df))
        print(f"\nTrades: {trade_count}")
    except Exception:
        pass
    if adv:
        print_metrics(adv, title="Advanced Analytics")
    if risk:
        print_metrics(risk, title="Risk Metrics")

    # Daily profit target statistics (parity with legacy output)
    try:
        engine_cfg = result.get('engine_config') or result.get('execution_info', {}).get('engine_config') or {}
        daily_target = engine_cfg.get('daily_target', 30.0)
        daily_stats = daily_profit_target_stats(trades_df, daily_target)
        print(format_section("Daily Target Stats"))
        print(f"Days Traded: {daily_stats.get('days_traded', 0)}")
        print(f"Days Target Hit: {daily_stats.get('days_target_hit', 0)}")
        thr = daily_stats.get('target_hit_rate')
        print(f"Daily Target Hit Rate: {thr*100:.2f}%" if isinstance(thr, (int, float)) and thr == thr else "Daily Target Hit Rate: N/A")
        mdp = daily_stats.get('max_daily_pnl')
        wdp = daily_stats.get('min_daily_pnl')
        adp = daily_stats.get('avg_daily_pnl')
        print(f"Best Day PnL: {mdp:.2f}" if isinstance(mdp, (int, float)) and mdp == mdp else "Best Day PnL: N/A")
        print(f"Worst Day PnL: {wdp:.2f}" if isinstance(wdp, (int, float)) and wdp == wdp else "Worst Day PnL: N/A")
        print(f"Average Day PnL: {adp:.2f}" if isinstance(adp, (int, float)) and adp == adp else "Average Day PnL: N/A")
    except Exception:
        pass

    # Optionally write JSON output
    if args.output_json:
        payload = {
            "strategy": args.strategy,
            "params": strategy_params,
            "engine_options": engine_options,
            "metrics": metrics,
            "advanced_analytics": adv,
            "risk_metrics": risk,
            "equity_curve": result.get("equity_curve", []),
            "trades": (result.get("trade_log") or result.get("trades") or []),
        }
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
        print(f"\nWrote JSON results to: {args.output_json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
