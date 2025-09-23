"""Services responsible for chart-related payloads."""

from __future__ import annotations

from typing import Dict, List, Optional

import pandas as pd


class ChartPayloadService:
    """Wraps chart generation helpers used by ``AnalyticsService``."""

    def __init__(self, chart_generator) -> None:
        self._chart_gen = chart_generator

    def build_charts(
        self,
        *,
        backtest,
        chart_types: List[str],
        max_points: Optional[int],
    ) -> Dict[str, object]:
        results = backtest.results
        equity_curve = pd.DataFrame(results.get('equity_curve', []))
        trades_list = results.get('trades') or results.get('trade_log') or []
        trades = pd.DataFrame(trades_list)

        charts: Dict[str, object] = {}

        if 'equity' in chart_types:
            charts['equity'] = self._chart_gen.create_equity_chart(equity_curve, max_points=max_points)

        if 'drawdown' in chart_types:
            charts['drawdown'] = self._chart_gen.create_drawdown_chart(equity_curve, max_points=max_points)

        if 'returns' in chart_types:
            charts['returns'] = self._chart_gen.create_returns_distribution_chart(equity_curve)

        if 'trades' in chart_types:
            charts['trades'] = self._chart_gen.create_trades_scatter_chart(trades, equity_curve, max_points=max_points)

        if 'monthly_returns' in chart_types:
            charts['monthly_returns'] = self._chart_gen.create_monthly_returns_heatmap(equity_curve)

        return {
            'success': True,
            'backtest_id': backtest.id,
            'charts': charts,
        }

    def compare_backtests(self, backtests) -> Dict[str, object]:
        comparison_data: List[Dict[str, object]] = []
        equity_curves: Dict[str, pd.DataFrame] = {}

        for backtest in backtests:
            if not backtest.results:
                continue

            results = backtest.results
            metrics = results.get('metrics', {})
            equity_curve = pd.DataFrame(results.get('equity_curve', []))

            comparison_data.append(
                {
                    'backtest_id': backtest.id,
                    'strategy_name': backtest.strategy_name,
                    'total_return': metrics.get('total_return_pct', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown_pct', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'profit_factor': metrics.get('profit_factor', 0),
                    'total_trades': metrics.get('total_trades', 0),
                }
            )

            if not equity_curve.empty:
                equity_curves[f"Strategy {backtest.id}"] = equity_curve

        comparison_chart = self._chart_gen.create_comparison_chart(equity_curves)

        return {
            'success': True,
            'comparison_data': comparison_data,
            'comparison_chart': comparison_chart,
        }
