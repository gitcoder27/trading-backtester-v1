"""Rolling and risk metric helpers."""

from __future__ import annotations

from typing import Dict

import pandas as pd


class MetricsService:
    def __init__(self, performance_calc, risk_calc, chart_generator, formatter) -> None:
        self._performance_calc = performance_calc
        self._risk_calc = risk_calc
        self._chart_gen = chart_generator
        self._formatter = formatter

    def rolling_metrics(self, backtest, *, window: int) -> Dict[str, object]:
        equity_curve = pd.DataFrame(backtest.results.get('equity_curve', []))
        rolling_data = self._performance_calc.compute_rolling_metrics(equity_curve, window)

        if rolling_data.empty:
            return {
                'success': True,
                'backtest_id': backtest.id,
                'rolling_metrics': [],
                'charts': {},
            }

        charts = {
            'rolling_sharpe': self._chart_gen.create_rolling_metrics_chart(rolling_data, 'rolling_sharpe'),
            'rolling_volatility': self._chart_gen.create_rolling_metrics_chart(rolling_data, 'rolling_volatility'),
            'rolling_return': self._chart_gen.create_rolling_metrics_chart(rolling_data, 'rolling_return'),
        }

        return {
            'success': True,
            'backtest_id': backtest.id,
            'rolling_metrics': self._formatter.clean_dataframe_for_json(rolling_data),
            'charts': charts,
        }

    def drawdown_analysis(self, backtest) -> Dict[str, object]:
        equity_curve = pd.DataFrame(backtest.results.get('equity_curve', []))
        drawdown_analysis = self._risk_calc.compute_drawdown_analysis(equity_curve)

        return {
            'success': True,
            'backtest_id': backtest.id,
            'drawdown_analysis': drawdown_analysis,
        }
