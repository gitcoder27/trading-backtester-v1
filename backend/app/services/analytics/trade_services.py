"""Trade-centric helpers used by the analytics service."""

from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd


class TradeServices:
    def __init__(self, trade_analyzer) -> None:
        self._trade_analyzer = trade_analyzer

    def get_trades_data(
        self,
        backtest,
        *,
        page: int,
        page_size: int,
        sort_by: str,
        sort_order: str,
        filter_profitable: Optional[bool],
    ) -> Dict[str, Any]:
        trades_raw = backtest.results.get('trades') or backtest.results.get('trade_log') or []

        if not trades_raw:
            return {
                'success': True,
                'trades': [],
                'total_trades': 0,
                'page': page,
                'page_size': page_size,
                'total_pages': 0,
            }

        trades_df = pd.DataFrame(trades_raw)
        payload = self._trade_analyzer.get_trades_data_paginated(
            trades_df,
            page,
            page_size,
            sort_by,
            sort_order,
            filter_profitable,
        )
        payload['success'] = True
        return payload

    def get_trade_streaks(self, backtest) -> Dict[str, Any]:
        trades_raw = backtest.results.get('trades') or backtest.results.get('trade_log') or []

        if not trades_raw:
            return {
                'success': True,
                'backtest_id': backtest.id,
                'streaks': {
                    'max_winning_streak': 0,
                    'max_losing_streak': 0,
                    'current_streak': 0,
                    'current_streak_type': 'none',
                },
            }

        trades_df = pd.DataFrame(trades_raw)
        streaks = self._trade_analyzer.calculate_trade_streaks(trades_df)

        return {
            'success': True,
            'backtest_id': backtest.id,
            'streaks': streaks,
        }
