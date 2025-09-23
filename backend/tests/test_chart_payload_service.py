# -*- coding: utf-8 -*-
"""
Unit tests for ChartPayloadService.
Testing library/framework: pytest + unittest.mock
"""
import pytest
import pandas as pd
from pandas.testing import assert_frame_equal
from unittest.mock import Mock


# Try common import paths for the service under test
try:  # most likely
    from backend.services.chart_payload_service import ChartPayloadService  # type: ignore
except ImportError:
    try:
        from services.chart_payload_service import ChartPayloadService  # type: ignore
    except ImportError:
        from chart_payload_service import ChartPayloadService  # type: ignore


class DummyBacktest:
    def __init__(self, id, strategy_name="Strategy", results=None):
        self.id = id
        self.strategy_name = strategy_name
        self.results = results or {}


def test_build_charts_no_chart_types_returns_empty_and_no_calls():
    chart_gen = Mock()
    s = ChartPayloadService(chart_gen)
    bt = DummyBacktest(
        id="bt-empty",
        results={"equity_curve": [], "trades": []},
    )

    resp = s.build_charts(backtest=bt, chart_types=[], max_points=None)

    assert resp["success"] is True
    assert resp["backtest_id"] == "bt-empty"
    assert resp["charts"] == {}
    # Ensure no generator methods were called
    for name in [
        "create_equity_chart",
        "create_drawdown_chart",
        "create_returns_distribution_chart",
        "create_trades_scatter_chart",
        "create_monthly_returns_heatmap",
    ]:
        assert not getattr(chart_gen, name).called, f"{name} should not be called"


def test_build_charts_all_types_calls_generators_with_correct_args_and_max_points():
    equity_data = [
        {"date": "2024-01-01", "equity": 100.0},
        {"date": "2024-01-02", "equity": 110.0},
    ]
    trades_data = [
        {"entry_date": "2024-01-01", "exit_date": "2024-01-02", "pnl": 10.0},
        {"entry_date": "2024-01-02", "exit_date": "2024-01-03", "pnl": -5.0},
    ]
    chart_gen = Mock()
    chart_gen.create_equity_chart.return_value = "equity-chart"
    chart_gen.create_drawdown_chart.return_value = "drawdown-chart"
    chart_gen.create_returns_distribution_chart.return_value = "returns-chart"
    chart_gen.create_trades_scatter_chart.return_value = "trades-chart"
    chart_gen.create_monthly_returns_heatmap.return_value = "monthly-returns-chart"

    s = ChartPayloadService(chart_gen)
    bt = DummyBacktest(
        id=1,
        strategy_name="Alpha",
        results={"equity_curve": equity_data, "trades": trades_data},
    )

    resp = s.build_charts(
        backtest=bt,
        chart_types=["equity", "drawdown", "returns", "trades", "monthly_returns"],
        max_points=100,
    )

    # Validate returned charts payload
    assert resp["success"] is True
    assert resp["backtest_id"] == 1
    assert resp["charts"] == {
        "equity": "equity-chart",
        "drawdown": "drawdown-chart",
        "returns": "returns-chart",
        "trades": "trades-chart",
        "monthly_returns": "monthly-returns-chart",
    }

    expected_equity_df = pd.DataFrame(equity_data)
    expected_trades_df = pd.DataFrame(trades_data)

    # equity
    args, kwargs = chart_gen.create_equity_chart.call_args
    assert_frame_equal(args[0].reset_index(drop=True), expected_equity_df)
    assert kwargs.get("max_points") == 100

    # drawdown
    args, kwargs = chart_gen.create_drawdown_chart.call_args
    assert_frame_equal(args[0].reset_index(drop=True), expected_equity_df)
    assert kwargs.get("max_points") == 100

    # returns (no max_points kw)
    args, kwargs = chart_gen.create_returns_distribution_chart.call_args
    assert_frame_equal(args[0].reset_index(drop=True), expected_equity_df)
    assert kwargs == {}

    # trades scatter gets trades then equity, forwards max_points
    args, kwargs = chart_gen.create_trades_scatter_chart.call_args
    trades_df_arg, equity_df_arg = args
    assert_frame_equal(trades_df_arg.reset_index(drop=True), expected_trades_df)
    assert_frame_equal(equity_df_arg.reset_index(drop=True), expected_equity_df)
    assert kwargs.get("max_points") == 100

    # monthly returns (no max_points)
    args, kwargs = chart_gen.create_monthly_returns_heatmap.call_args
    assert_frame_equal(args[0].reset_index(drop=True), expected_equity_df)
    assert kwargs == {}


def test_build_charts_uses_trade_log_when_trades_missing():
    trade_log = [
        {"entry_date": "2024-02-01", "exit_date": "2024-02-05", "pnl": 3.0}
    ]
    chart_gen = Mock()
    chart_gen.create_trades_scatter_chart.return_value = "trades-chart"

    s = ChartPayloadService(chart_gen)
    bt = DummyBacktest(
        id="bt-trade-log",
        results={"equity_curve": [], "trade_log": trade_log},  # 'trades' absent
    )

    resp = s.build_charts(
        backtest=bt,
        chart_types=["trades"],
        max_points=None,
    )

    assert resp["charts"]["trades"] == "trades-chart"
    (trades_df_arg, equity_df_arg), kwargs = chart_gen.create_trades_scatter_chart.call_args
    assert isinstance(trades_df_arg, pd.DataFrame)
    assert len(trades_df_arg) == len(trade_log)
    assert isinstance(equity_df_arg, pd.DataFrame)
    assert equity_df_arg.empty
    assert "max_points" in kwargs and kwargs["max_points"] is None


def test_build_charts_handles_missing_equity_curve_and_trades_gracefully():
    chart_gen = Mock()
    chart_gen.create_equity_chart.return_value = "equity-chart"
    chart_gen.create_drawdown_chart.return_value = "drawdown-chart"

    s = ChartPayloadService(chart_gen)
    bt = DummyBacktest(id="bt-none", results={})  # no keys present

    resp = s.build_charts(backtest=bt, chart_types=["equity", "drawdown"], max_points=None)

    assert resp["charts"]["equity"] == "equity-chart"
    assert resp["charts"]["drawdown"] == "drawdown-chart"

    # Equity DF should be empty DataFrame object
    (equity_df_arg,), kwargs = chart_gen.create_equity_chart.call_args
    assert isinstance(equity_df_arg, pd.DataFrame)
    assert equity_df_arg.empty
    assert kwargs.get("max_points") is None

    (equity_df_arg2,), kwargs2 = chart_gen.create_drawdown_chart.call_args
    assert isinstance(equity_df_arg2, pd.DataFrame)
    assert equity_df_arg2.empty
    assert kwargs2.get("max_points") is None


def test_compare_backtests_filters_and_defaults_and_builds_chart():
    # Backtest A: full metrics, non-empty equity curve
    a_results = {
        "metrics": {
            "total_return_pct": 12.5,
            "sharpe_ratio": 1.2,
            "max_drawdown_pct": -5.0,
            "win_rate": 0.6,
            "profit_factor": 1.8,
            "total_trades": 123,
        },
        "equity_curve": [
            {"date": "2024-01-01", "equity": 100.0},
            {"date": "2024-01-02", "equity": 105.0},
        ],
    }
    bt_a = DummyBacktest(id=1, strategy_name="Alpha", results=a_results)

    # Backtest B: no results (should be skipped)
    bt_b = DummyBacktest(id=2, strategy_name="Beta", results={})

    # Backtest C: partial metrics, empty equity curve (included in data, excluded from curves)
    c_results = {
        "metrics": {
            "win_rate": 0.55,  # others default to 0
        },
        "equity_curve": [],  # empty
    }
    bt_c = DummyBacktest(id=3, strategy_name="Gamma", results=c_results)

    chart_gen = Mock()
    chart_gen.create_comparison_chart.return_value = "comparison-chart"

    s = ChartPayloadService(chart_gen)
    resp = s.compare_backtests([bt_a, bt_b, bt_c])

    assert resp["success"] is True
    assert resp["comparison_chart"] == "comparison-chart"

    # Validate comparison_data contents (order preserved for present backtests)
    data_by_id = {row["backtest_id"]: row for row in resp["comparison_data"]}
    assert set(data_by_id.keys()) == {1, 3}

    row_a = data_by_id[1]
    assert row_a["strategy_name"] == "Alpha"
    assert row_a["total_return"] == 12.5
    assert row_a["sharpe_ratio"] == 1.2
    assert row_a["max_drawdown"] == -5.0
    assert row_a["win_rate"] == 0.6
    assert row_a["profit_factor"] == 1.8
    assert row_a["total_trades"] == 123

    row_c = data_by_id[3]
    assert row_c["strategy_name"] == "Gamma"
    # Defaults for missing metrics
    assert row_c["total_return"] == 0
    assert row_c["sharpe_ratio"] == 0
    assert row_c["max_drawdown"] == 0
    assert row_c["win_rate"] == 0.55
    assert row_c["profit_factor"] == 0
    assert row_c["total_trades"] == 0

    # Validate create_comparison_chart input: only non-empty equity curves, keyed by "Strategy {id}"
    (equity_curves_arg,), _ = chart_gen.create_comparison_chart.call_args
    assert isinstance(equity_curves_arg, dict)
    assert set(equity_curves_arg.keys()) == {"Strategy 1"}
    df_for_a = equity_curves_arg["Strategy 1"]
    assert isinstance(df_for_a, pd.DataFrame)
    assert not df_for_a.empty