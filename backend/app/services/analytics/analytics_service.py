"""Modular analytics service bringing together individual components."""

import logging
from bisect import bisect_left, bisect_right
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.app.database.models import Backtest, get_session_factory
from backtester.metrics import daily_profit_target_stats

from .chart_generator import ChartGenerator
from .data_fetcher import AnalyticsDataFetcher, PriceDataBundle, PriceDataError
from .data_formatter import DataFormatter
from .performance_calculator import PerformanceCalculator
from .risk_calculator import RiskCalculator
from .trade_analyzer import TradeAnalyzer
from .tradingview_builder import TradingViewBuilder


logger = logging.getLogger(__name__)


class AnalyticsService:
    """
    Main analytics service that orchestrates all analytics operations.
    
    This modular service delegates specific operations to specialized components:
    - PerformanceCalculator: Performance metrics and ratios
    - ChartGenerator: Chart creation and visualization
    - TradeAnalyzer: Trade pattern analysis
    - RiskCalculator: Risk metrics and analysis
    - DataFormatter: Data formatting and conversion utilities
    """
    
    def __init__(self):
        self.SessionLocal = get_session_factory()
        
        # Initialize specialized components
        self.data_fetcher = AnalyticsDataFetcher()
        self.performance_calc = PerformanceCalculator()
        self.chart_gen = ChartGenerator()
        self.trade_analyzer = TradeAnalyzer()
        self.risk_calc = RiskCalculator()
        self.formatter = DataFormatter()
        self.tradingview_builder = TradingViewBuilder()
    
    def get_performance_summary(self, backtest_id: int, sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get comprehensive performance summary for a backtest.
        
        Returns:
        - Basic metrics (return, Sharpe, drawdown, etc.)
        - Advanced analytics (volatility, skewness, Sortino ratio, etc.)
        - Trade analysis (win rate, avg win/loss, consecutive trades, etc.)
        - Risk metrics (VaR, CVaR, max consecutive losses, etc.)
        """
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse results
            results = backtest.results
            equity_curve = pd.DataFrame(results.get('equity_curve', []))
            trades_list = results.get('trades') or results.get('trade_log') or []
            trades = pd.DataFrame(trades_list)
            metrics = results.get('metrics', {})
            engine_config = results.get('engine_config', {})

            # Determine which sections to compute/return
            allowed_sections = {
                'basic_metrics',
                'advanced_analytics',
                'risk_metrics',
                'trade_analysis',
                'daily_target_stats',
                'drawdown_analysis',
            }
            requested_sections: Optional[set]
            if sections is None:
                requested_sections = None  # Means all
            else:
                requested_sections = {s for s in sections if s in allowed_sections}
            
            # Attempt cache hit from results JSON
            cached_summary = results.get('analytics_summary') if isinstance(results, dict) else None
            cached_available = set(cached_summary.keys()) if isinstance(cached_summary, dict) else set()

            performance_payload: Dict[str, Any] = {}

            def need(section: str) -> bool:
                return (requested_sections is None or section in requested_sections)

            # basic_metrics comes from stored metrics always
            if need('basic_metrics'):
                performance_payload['basic_metrics'] = metrics

            # Use cached values when available
            if cached_summary and isinstance(cached_summary, dict):
                for key in allowed_sections - {'basic_metrics'}:
                    if need(key) and key in cached_summary:
                        performance_payload[key] = cached_summary[key]

            # Compute any missing requested sections
            missing_sections = [
                s for s in (requested_sections or allowed_sections)
                if s not in performance_payload and s in allowed_sections
            ]

            # Daily target stats (use configured daily_target if available)
            if 'daily_target_stats' in missing_sections:
                try:
                    daily_target = float(engine_config.get('daily_target', 30.0))
                except Exception:
                    daily_target = 30.0
                performance_payload['daily_target_stats'] = daily_profit_target_stats(trades, daily_target)

            if 'drawdown_analysis' in missing_sections:
                performance_payload['drawdown_analysis'] = self.risk_calc.compute_drawdown_analysis(equity_curve)

            if 'advanced_analytics' in missing_sections:
                performance_payload['advanced_analytics'] = self.performance_calc.compute_basic_analytics(equity_curve, trades)

            if 'risk_metrics' in missing_sections:
                performance_payload['risk_metrics'] = self.risk_calc.compute_risk_metrics(equity_curve)

            if 'trade_analysis' in missing_sections:
                performance_payload['trade_analysis'] = self.trade_analyzer.analyze_trades_comprehensive(trades)

            # Persist cache if first compute or filling gaps
            try:
                cache_dirty = False
                if not cached_summary or not isinstance(cached_summary, dict):
                    results['analytics_summary'] = {}
                    cached_summary = results['analytics_summary']
                    cache_dirty = True
                for k, v in performance_payload.items():
                    if k not in cached_summary and k in allowed_sections:
                        cached_summary[k] = v
                        cache_dirty = True
                # Always ensure basic metrics cached
                if 'basic_metrics' not in cached_summary:
                    cached_summary['basic_metrics'] = metrics
                    cache_dirty = True
                if cache_dirty:
                    results['analytics_cache'] = {
                        'cached_at': datetime.utcnow().isoformat() + 'Z',
                        'cache_version': 1,
                        'sections': sorted(list(cached_summary.keys())),
                        'backtest_completed_at': backtest.completed_at.isoformat() + 'Z' if backtest.completed_at else None,
                    }
                    backtest.results = results
                    db.add(backtest)
                    db.commit()
            except Exception:
                # Cache write failures should not break the response
                pass

            response = {
                'success': True,
                'backtest_id': backtest_id,
                'performance': performance_payload
            }
            # Sanitize for JSON (avoid NaN/Inf causing 500s)
            return self.formatter.sanitize_json(response)
        finally:
            db.close()
    
    def get_charts(self, backtest_id: int, chart_types: Optional[List[str]] = None, max_points: Optional[int] = None) -> Dict[str, Any]:
        """
        Generate charts for a backtest.
        
        Available chart types:
        - equity: Equity curve over time
        - drawdown: Drawdown chart with underwater curve
        - returns: Returns distribution histogram
        - trades: Trades scatter plot on equity curve
        - monthly_returns: Monthly returns heatmap
        """
        if chart_types is None:
            chart_types = ['equity', 'drawdown', 'returns', 'trades', 'monthly_returns']
        
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse results
            results = backtest.results
            equity_curve = pd.DataFrame(results.get('equity_curve', []))
            trades_list = results.get('trades') or results.get('trade_log') or []
            trades = pd.DataFrame(trades_list)
            
            # Generate charts using chart generator
            charts = {}
            
            if 'equity' in chart_types:
                charts['equity'] = self.chart_gen.create_equity_chart(equity_curve, max_points=max_points)
            
            if 'drawdown' in chart_types:
                charts['drawdown'] = self.chart_gen.create_drawdown_chart(equity_curve, max_points=max_points)
            
            if 'returns' in chart_types:
                charts['returns'] = self.chart_gen.create_returns_distribution_chart(equity_curve)
            
            if 'trades' in chart_types:
                charts['trades'] = self.chart_gen.create_trades_scatter_chart(trades, equity_curve, max_points=max_points)
            
            if 'monthly_returns' in chart_types:
                charts['monthly_returns'] = self.chart_gen.create_monthly_returns_heatmap(equity_curve)
            
            return {
                'success': True,
                'backtest_id': backtest_id,
                'charts': charts
            }
        finally:
            db.close()
    
    def compare_strategies(self, backtest_ids: List[int]) -> Dict[str, Any]:
        """Compare performance across multiple backtests"""
        db = self.SessionLocal()
        try:
            backtests = db.query(Backtest).filter(Backtest.id.in_(backtest_ids)).all()
            
            if len(backtests) != len(backtest_ids):
                return {'success': False, 'error': 'One or more backtests not found'}
            
            comparison_data = []
            equity_curves = {}
            
            for backtest in backtests:
                if not backtest.results:
                    continue
                
                results = backtest.results
                metrics = results.get('metrics', {})
                equity_curve = pd.DataFrame(results.get('equity_curve', []))
                
                comparison_data.append({
                    'backtest_id': backtest.id,
                    'strategy_name': backtest.strategy_name,
                    'total_return': metrics.get('total_return_pct', 0),
                    'sharpe_ratio': metrics.get('sharpe_ratio', 0),
                    'max_drawdown': metrics.get('max_drawdown_pct', 0),
                    'win_rate': metrics.get('win_rate', 0),
                    'profit_factor': metrics.get('profit_factor', 0),
                    'total_trades': metrics.get('total_trades', 0)
                })
                
                if not equity_curve.empty:
                    equity_curves[f"Strategy {backtest.id}"] = equity_curve
            
            # Create comparison chart
            comparison_chart = self.chart_gen.create_comparison_chart(equity_curves)
            
            return {
                'success': True,
                'comparison_data': comparison_data,
                'comparison_chart': comparison_chart
            }
        finally:
            db.close()
    
    def get_trades_data(
        self, 
        backtest_id: int,
        page: int = 1,
        page_size: int = 100,
        sort_by: str = "entry_time",
        sort_order: str = "desc",
        filter_profitable: Optional[bool] = None
    ) -> Dict[str, Any]:
        """Get paginated and filtered trade data for a backtest"""
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse trades data
            results = backtest.results
            trades_raw = results.get('trades') or results.get('trade_log') or []
            
            if not trades_raw:
                return {
                    'success': True,
                    'trades': [],
                    'total_trades': 0,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': 0
                }
            
            trades_df = pd.DataFrame(trades_raw)
            
            # Use trade analyzer for pagination and filtering
            result = self.trade_analyzer.get_trades_data_paginated(
                trades_df, page, page_size, sort_by, sort_order, filter_profitable
            )
            
            result['success'] = True
            return result
            
        finally:
            db.close()
    
    def get_chart_data(
        self,
        backtest_id: int,
        include_trades: bool = True,
        include_indicators: bool = True,
        max_candles: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        tz: Optional[str] = None,
        single_day: Optional[bool] = None,
        cursor: Optional[str] = None,
        navigate: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return TradingView-friendly candlesticks, trades, and indicators."""

        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()

            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}

            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}

            results: Dict[str, Any] = backtest.results

            try:
                bundle = self.data_fetcher.load_price_data(
                    backtest,
                    results,
                    db,
                    tz=tz,
                    start=start,
                    end=end,
                    max_candles=max_candles,
                    single_day=single_day,
                    cursor=cursor,
                    navigate=navigate,
                )
            except PriceDataError as exc:
                return {'success': False, 'error': str(exc)}

            navigation = self._build_navigation(bundle, tz, start=start, end=end, cursor=cursor)

            candles = self.tradingview_builder.build_candles(bundle.dataframe)
            if not candles:
                payload = {
                    'success': False,
                    'error': 'No valid candlestick data could be generated',
                    'navigation': navigation,
                }
                return self.formatter.sanitize_json(payload)

            response: Dict[str, Any] = {
                'success': True,
                'backtest_id': backtest_id,
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
                response['trade_markers'] = self.tradingview_builder.build_trade_markers(
                    results,
                    bundle.dataframe,
                    tz=tz,
                    start_ts=bundle.start_bound,
                    end_ts=bundle.end_bound,
                )

            if include_indicators:
                strategy_params = getattr(backtest, 'strategy_params', None)
                response['indicators'] = self.tradingview_builder.build_indicator_series(
                    results,
                    bundle.dataframe,
                    strategy_params=strategy_params,
                )
                response['indicator_config'] = results.get('indicator_cfg') or []

            return self.formatter.sanitize_json(response)
        except Exception:  # pragma: no cover - defensive logging
            logger.exception('Error generating chart data for backtest_id=%s', backtest_id)
            return {'success': False, 'error': 'Error generating chart data'}
        finally:
            db.close()

    def _build_navigation(
        self,
        bundle: PriceDataBundle,
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

    def get_rolling_metrics(self, backtest_id: int, window: int = 50) -> Dict[str, Any]:
        """Get rolling performance metrics for a backtest"""
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse results
            results = backtest.results
            equity_curve = pd.DataFrame(results.get('equity_curve', []))
            
            # Calculate rolling metrics
            rolling_data = self.performance_calc.compute_rolling_metrics(equity_curve, window)
            
            if rolling_data.empty:
                return {
                    'success': True,
                    'backtest_id': backtest_id,
                    'rolling_metrics': [],
                    'charts': {}
                }
            
            # Create rolling metrics charts
            charts = {
                'rolling_sharpe': self.chart_gen.create_rolling_metrics_chart(rolling_data, 'rolling_sharpe'),
                'rolling_volatility': self.chart_gen.create_rolling_metrics_chart(rolling_data, 'rolling_volatility'),
                'rolling_return': self.chart_gen.create_rolling_metrics_chart(rolling_data, 'rolling_return')
            }
            
            return {
                'success': True,
                'backtest_id': backtest_id,
                'rolling_metrics': self.formatter.clean_dataframe_for_json(rolling_data),
                'charts': charts
            }
            
        finally:
            db.close()
    
    def get_drawdown_analysis(self, backtest_id: int) -> Dict[str, Any]:
        """Get detailed drawdown analysis for a backtest"""
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse results
            results = backtest.results
            equity_curve = pd.DataFrame(results.get('equity_curve', []))
            
            # Calculate drawdown analysis
            drawdown_analysis = self.risk_calc.compute_drawdown_analysis(equity_curve)
            
            return {
                'success': True,
                'backtest_id': backtest_id,
                'drawdown_analysis': drawdown_analysis
            }
            
        finally:
            db.close()
    
    def get_trade_streaks(self, backtest_id: int) -> Dict[str, Any]:
        """Get trade streak analysis for a backtest"""
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse trades data
            results = backtest.results
            trades_raw = results.get('trades') or results.get('trade_log') or []
            
            if not trades_raw:
                return {
                    'success': True,
                    'backtest_id': backtest_id,
                    'streaks': {
                        'max_winning_streak': 0,
                        'max_losing_streak': 0,
                        'current_streak': 0,
                        'current_streak_type': 'none'
                    }
                }
            
            trades_df = pd.DataFrame(trades_raw)
            streaks = self.trade_analyzer.calculate_trade_streaks(trades_df)
            
            return {
                'success': True,
                'backtest_id': backtest_id,
                'streaks': streaks
            }
            
        finally:
            db.close()
