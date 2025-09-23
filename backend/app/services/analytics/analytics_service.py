"""Facade service that coordinates analytics operations."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from backend.app.database.models import Backtest, get_session_factory

from .backtest_utils import load_backtest
from .chart_payload_service import ChartPayloadService
from .data_fetcher import AnalyticsDataFetcher
from .data_formatter import DataFormatter
from .metrics_service import MetricsService
from .performance_summary_service import PerformanceSummaryService
from .chart_generator import ChartGenerator
from .performance_calculator import PerformanceCalculator
from .risk_calculator import RiskCalculator
from .trade_analyzer import TradeAnalyzer
from .trade_services import TradeServices
from .tradingview_builder import TradingViewBuilder
from .tradingview_chart_service import TradingViewChartService


class AnalyticsService:
    """Orchestrates analytics operations by delegating to specialized helpers."""

    def __init__(self) -> None:
        self.SessionLocal = get_session_factory()

        # Shared component instances
        self.data_fetcher = AnalyticsDataFetcher()
        self.performance_calc = PerformanceCalculator()
        self.chart_gen = ChartGenerator()
        self.trade_analyzer = TradeAnalyzer()
        self.risk_calc = RiskCalculator()
        self.formatter = DataFormatter()
        self.tradingview_builder = TradingViewBuilder()

        # Service layers
        self._performance_summary_service = PerformanceSummaryService(
            self.performance_calc,
            self.trade_analyzer,
            self.risk_calc,
            self.formatter,
        )
        self._chart_payload_service = ChartPayloadService(self.chart_gen)
        self._trade_services = TradeServices(self.trade_analyzer)
        self._tradingview_chart_service = TradingViewChartService(
            self.data_fetcher,
            self.tradingview_builder,
            self.formatter,
        )
        self._metrics_service = MetricsService(
            self.performance_calc,
            self.risk_calc,
            self.chart_gen,
            self.formatter,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_performance_summary(
        self,
        backtest_id: int,
        sections: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        return self._with_backtest(
            backtest_id,
            lambda db, backtest: self._performance_summary_service.build(
                db,
                backtest,
                sections=sections,
            ),
        )

    def get_charts(
        self,
        backtest_id: int,
        chart_types: Optional[List[str]] = None,
        max_points: Optional[int] = None,
    ) -> Dict[str, Any]:
        chart_types = chart_types or ['equity', 'drawdown', 'returns', 'trades', 'monthly_returns']
        return self._with_backtest(
            backtest_id,
            lambda _db, backtest: self._chart_payload_service.build_charts(
                backtest=backtest,
                chart_types=chart_types,
                max_points=max_points,
            ),
        )

    def compare_strategies(self, backtest_ids: List[int]) -> Dict[str, Any]:
        session = self.SessionLocal()
        try:
            backtests = session.query(Backtest).filter(Backtest.id.in_(backtest_ids)).all()
            if len(backtests) != len(backtest_ids):
                return {'success': False, 'error': 'One or more backtests not found'}
            return self._chart_payload_service.compare_backtests(backtests)
        finally:
            session.close()

    def get_trades_data(
        self,
        backtest_id: int,
        page: int = 1,
        page_size: int = 100,
        sort_by: str = 'entry_time',
        sort_order: str = 'desc',
        filter_profitable: Optional[bool] = None,
    ) -> Dict[str, Any]:
        return self._with_backtest(
            backtest_id,
            lambda _db, backtest: self._trade_services.get_trades_data(
                backtest,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order,
                filter_profitable=filter_profitable,
            ),
        )

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
        return self._with_backtest(
            backtest_id,
            lambda session, backtest: self._tradingview_chart_service.build_chart_data(
                session,
                backtest,
                include_trades=include_trades,
                include_indicators=include_indicators,
                max_candles=max_candles,
                start=start,
                end=end,
                tz=tz,
                single_day=single_day,
                cursor=cursor,
                navigate=navigate,
            ),
        )

    def get_rolling_metrics(self, backtest_id: int, window: int = 50) -> Dict[str, Any]:
        return self._with_backtest(
            backtest_id,
            lambda _db, backtest: self._metrics_service.rolling_metrics(backtest, window=window),
        )

    def get_drawdown_analysis(self, backtest_id: int) -> Dict[str, Any]:
        return self._with_backtest(
            backtest_id,
            lambda _db, backtest: self._metrics_service.drawdown_analysis(backtest),
        )

    def get_trade_streaks(self, backtest_id: int) -> Dict[str, Any]:
        return self._with_backtest(
            backtest_id,
            lambda _db, backtest: self._trade_services.get_trade_streaks(backtest),
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _with_backtest(
        self,
        backtest_id: int,
        handler,
    ) -> Dict[str, Any]:
        session = self.SessionLocal()
        try:
            backtest, error = load_backtest(session, backtest_id)
            if error is not None:
                return error
            return handler(session, backtest)
        finally:
            session.close()

    # ------------------------------------------------------------------
    # Legacy compatibility helpers used by existing tests
    # ------------------------------------------------------------------
    def _compute_returns(self, equity_curve: pd.DataFrame) -> pd.Series:
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return pd.Series(dtype=float)

        equity = pd.to_numeric(equity_curve['equity'], errors='coerce')
        returns = equity.pct_change().dropna()
        returns.name = 'returns'
        return returns

    def _compute_drawdown(self, equity_curve: pd.DataFrame) -> pd.DataFrame:
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return pd.DataFrame(columns=['timestamp', 'equity', 'peak', 'drawdown'])

        equity = pd.to_numeric(equity_curve['equity'], errors='coerce').fillna(method='ffill')
        peak = equity.cummax()
        drawdown = (equity - peak) / peak

        timestamps = pd.to_datetime(equity_curve.get('timestamp', equity_curve.index), errors='coerce')

        return pd.DataFrame({
            'timestamp': timestamps,
            'equity': equity,
            'peak': peak,
            'drawdown': drawdown.fillna(0.0),
        })

    def _compute_rolling_sharpe(self, equity_curve: pd.DataFrame, window: int = 50) -> pd.DataFrame:
        returns = self._compute_returns(equity_curve)
        if returns.empty:
            return pd.DataFrame(columns=['timestamp', 'rolling_sharpe'])

        rolling_mean = returns.rolling(window=window).mean()
        rolling_std = returns.rolling(window=window).std().replace({0.0: pd.NA})
        annualization_factor = self.formatter.calculate_annualization_factor('minute')
        scaled = (rolling_mean / rolling_std) * (annualization_factor ** 0.5)
        scaled = scaled.fillna(0.0)

        timestamps = pd.to_datetime(equity_curve.get('timestamp', equity_curve.index), errors='coerce')
        timestamps = timestamps.iloc[1:]

        frame = pd.DataFrame({'timestamp': timestamps, 'rolling_sharpe': scaled.values})
        return frame

    def _compute_risk_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, Any]:
        if equity_curve.empty:
            return {}
        return self.risk_calc.compute_risk_metrics(equity_curve)

    def _analyze_trades(self, trades: pd.DataFrame) -> Dict[str, Any]:
        if trades is None or trades.empty:
            return {}

        basic = self.performance_calc._analyze_trades_basic(trades)
        comprehensive = self.trade_analyzer.analyze_trades_comprehensive(trades)

        time_analysis = comprehensive.get('time_analysis', {}) if isinstance(comprehensive, dict) else {}

        analysis = {**comprehensive, **basic}
        analysis['trades_by_hour'] = time_analysis.get('hourly_performance', [])
        analysis['trades_by_weekday'] = time_analysis.get('weekday_performance', [])

        return analysis
