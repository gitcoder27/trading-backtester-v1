"""TradingView-friendly payload builder used by the analytics service."""

from __future__ import annotations

import logging
from bisect import bisect_left, bisect_right
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy.orm import Session


class TradingViewChartService:
    def __init__(self, data_fetcher, tradingview_builder, formatter) -> None:
        self._data_fetcher = data_fetcher
        self._tradingview_builder = tradingview_builder
        self._formatter = formatter
        self._logger = logging.getLogger(__name__)

    def build_chart_data(
        self,
        session: Session,
        backtest,
        *,
        include_trades: bool,
        include_indicators: bool,
        max_candles: Optional[int],
        start: Optional[str],
        end: Optional[str],
        tz: Optional[str],
        single_day: Optional[bool],
        cursor: Optional[str],
        navigate: Optional[str],
    ) -> Dict[str, Any]:
        results: Dict[str, Any] = backtest.results

        try:
            bundle = self._data_fetcher.load_price_data(
                backtest,
                results,
                session,
                tz=tz,
                start=start,
                end=end,
                max_candles=max_candles,
                single_day=single_day,
                cursor=cursor,
                navigate=navigate,
            )
        except Exception as exc:
            from .data_fetcher import PriceDataError  # local import to avoid cycle

            if isinstance(exc, PriceDataError):
                return {'success': False, 'error': str(exc)}
            self._logger.exception('Unexpected error loading price data for backtest_id=%s', backtest.id)
            return {'success': False, 'error': 'Error generating chart data'}

        navigation = self._build_navigation(bundle, tz, start=start, end=end, cursor=cursor)

        candles = self._tradingview_builder.build_candles(bundle.dataframe)
        if not candles:
            payload = {
                'success': False,
                'error': 'No valid candlestick data could be generated',
                'navigation': navigation,
            }
            return self._formatter.sanitize_json(payload)

        response: Dict[str, Any] = {
            'success': True,
            'backtest_id': backtest.id,
            'dataset_name': bundle.dataset_name,
            'candlestick_data': candles,
            'total_candles': bundle.total_candles,
            'returned_candles': len(candles),
            'sampled': bundle.sampled,
            'filtered': bundle.filtered,
            'date_range': {
                'start': candles[0]['time'] if candles else None,
                'end': candles[-1]['time'] if candles else None,
            },
            'navigation': navigation,
        }

        if include_trades:
            response['trade_markers'] = self._tradingview_builder.build_trade_markers(
                results,
                bundle.dataframe,
                tz=tz,
                start_ts=bundle.start_bound,
                end_ts=bundle.end_bound,
            )

            trades_list, trades_meta = self._build_trade_records(
                results,
                tz=tz,
                limit=200,
            )
            response['trades'] = trades_list
            response['trades_meta'] = trades_meta

        if include_indicators:
            strategy_params = getattr(backtest, 'strategy_params', None)
            response['indicators'] = self._tradingview_builder.build_indicator_series(
                results,
                bundle.dataframe,
                strategy_params=strategy_params,
            )
            response['indicator_config'] = results.get('indicator_cfg') or []

        return self._formatter.sanitize_json(response)

    def _build_trade_records(
        self,
        results: Dict[str, Any],
        *,
        tz: Optional[str],
        limit: int,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """Return a trimmed, JSON-safe list of trades for quick inspection."""

        raw_trades = results.get('trades') or results.get('trade_log') or []
        total_trades = len(raw_trades) if isinstance(raw_trades, list) else 0

        if not total_trades:
            return [], {
                'total': 0,
                'returned': 0,
                'limit': limit,
                'has_more': False,
                'timezone': tz or 'UTC',
            }

        trades_df = pd.DataFrame(raw_trades)
        if trades_df.empty:
            return [], {
                'total': total_trades,
                'returned': 0,
                'limit': limit,
                'has_more': total_trades > 0,
                'timezone': tz or 'UTC',
            }

        df = trades_df.copy()

        entry_col = next((col for col in ('entry_time', 'entry_timestamp', 'entry_at', 'timestamp') if col in df.columns), None)
        exit_col = next((col for col in ('exit_time', 'exit_timestamp', 'exit_at', 'close_time') if col in df.columns), None)

        if entry_col:
            df['_entry_ts'] = pd.to_datetime(df[entry_col], errors='coerce')
            df = df.sort_values(by='_entry_ts', ascending=False, na_position='last')
        else:
            df['_entry_ts'] = range(len(df), 0, -1)

        trimmed_df = df.head(limit).copy()

        if entry_col and entry_col in trimmed_df.columns:
            trimmed_df.loc[:, entry_col] = trimmed_df[entry_col].apply(self._formatter.format_timestamp)
        if exit_col and exit_col in trimmed_df.columns:
            trimmed_df.loc[:, exit_col] = trimmed_df[exit_col].apply(self._formatter.format_timestamp)

        trimmed_df = trimmed_df.drop(columns=['_entry_ts'], errors='ignore')

        records = self._formatter.clean_dataframe_for_json(trimmed_df)

        meta = {
            'total': total_trades,
            'returned': len(records),
            'limit': limit,
            'has_more': total_trades > len(records),
            'timezone': tz or 'UTC',
        }

        return records, meta

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------
    def _build_navigation(
        self,
        bundle,
        tz: Optional[str],
        *,
        start: Optional[str],
        end: Optional[str],
        cursor: Optional[str],
    ) -> Dict[str, Any]:
        local_tz = tz or 'UTC'
        available_dates = self._sessions_to_dates(bundle.available_sessions, local_tz)
        resolved_dates = sorted(set(self._sessions_to_dates(bundle.resolved_sessions, local_tz)))

        requested_start = self._timestamp_to_date(bundle.requested_start, local_tz)
        requested_end = self._timestamp_to_date(bundle.requested_end, local_tz)
        requested_cursor = self._parse_date(cursor, local_tz) if cursor else None

        ordered_dates = sorted(set(available_dates))
        previous_date: Optional[date] = None
        next_date: Optional[date] = None

        if ordered_dates:
            anchor_start = resolved_dates[0] if resolved_dates else (requested_start or requested_end)
            anchor_end = resolved_dates[-1] if resolved_dates else (requested_end or requested_start or anchor_start)

            previous_date = self._find_previous(ordered_dates, anchor_start)
            next_date = self._find_next(ordered_dates, anchor_end)

        navigation = {
            'available_dates': [d.isoformat() for d in ordered_dates],
            'resolved_dates': [d.isoformat() for d in resolved_dates],
            'previous_date': previous_date.isoformat() if previous_date else None,
            'next_date': next_date.isoformat() if next_date else None,
            'requested_start': requested_start.isoformat() if requested_start else start,
            'requested_end': requested_end.isoformat() if requested_end else end,
            'requested_cursor': requested_cursor.isoformat() if requested_cursor else cursor,
            'resolved_start': resolved_dates[0].isoformat() if resolved_dates else None,
            'resolved_end': resolved_dates[-1].isoformat() if resolved_dates else None,
            'has_data': bool(bundle.dataframe is not None and not bundle.dataframe.empty),
        }

        return navigation

    @staticmethod
    def _parse_date(value: Optional[str], tz: str) -> Optional[date]:
        if not value:
            return None
        try:
            ts = pd.to_datetime(value)
            if isinstance(value, str) and len(value) == 10:
                ts = ts.replace(hour=0, minute=0, second=0, microsecond=0)
            if ts.tzinfo is None:
                ts = ts.tz_localize(tz)
            else:
                ts = ts.tz_convert(tz)
            return ts.date()
        except Exception:
            return None

    def _sessions_to_dates(self, sessions: List[pd.Timestamp], tz: str) -> List[date]:
        dates: List[date] = []
        for session in sessions:
            local_date = self._timestamp_to_date(session, tz)
            if local_date is not None:
                dates.append(local_date)
        return dates

    @staticmethod
    def _timestamp_to_date(ts: Optional[pd.Timestamp], tz: str) -> Optional[date]:
        if ts is None:
            return None

        try:
            stamp = pd.Timestamp(ts)
        except Exception:
            return None

        if stamp.tzinfo is None:
            try:
                stamp = stamp.tz_localize('UTC')
            except Exception:
                stamp = stamp.tz_localize('UTC', nonexistent='shift_forward', ambiguous='infer')

        try:
            stamp = stamp.tz_convert(tz)
        except Exception:
            stamp = stamp.tz_convert('UTC')

        return stamp.date()

    @staticmethod
    def _find_previous(ordered_dates: List[date], anchor: Optional[date]) -> Optional[date]:
        if not ordered_dates or anchor is None:
            return None

        idx = bisect_left(ordered_dates, anchor)
        if idx == 0:
            return None
        return ordered_dates[idx - 1]

    @staticmethod
    def _find_next(ordered_dates: List[date], anchor: Optional[date]) -> Optional[date]:
        if not ordered_dates:
            return None

        if anchor is None:
            return ordered_dates[0]

        idx = bisect_right(ordered_dates, anchor)
        if idx >= len(ordered_dates):
            return None
        return ordered_dates[idx]
