"""
Analytics Service - Modular Version
Main orchestrator for analytics operations with clean separation of concerns
"""

import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.app.database.models import get_session_factory, Backtest, Dataset
from .performance_calculator import PerformanceCalculator
from .chart_generator import ChartGenerator
from .trade_analyzer import TradeAnalyzer
from .risk_calculator import RiskCalculator
from .data_formatter import DataFormatter


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
        self.performance_calc = PerformanceCalculator()
        self.chart_gen = ChartGenerator()
        self.trade_analyzer = TradeAnalyzer()
        self.risk_calc = RiskCalculator()
        self.formatter = DataFormatter()
    
    def get_performance_summary(self, backtest_id: int) -> Dict[str, Any]:
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
            
            # Compute analytics using specialized components
            advanced_analytics = self.performance_calc.compute_basic_analytics(equity_curve, trades)
            risk_metrics = self.risk_calc.compute_risk_metrics(equity_curve)
            trade_analysis = self.trade_analyzer.analyze_trades_comprehensive(trades)
            
            response = {
                'success': True,
                'backtest_id': backtest_id,
                'performance': {
                    'basic_metrics': metrics,
                    'advanced_analytics': advanced_analytics,
                    'risk_metrics': risk_metrics,
                    'trade_analysis': trade_analysis
                }
            }
            # Sanitize for JSON (avoid NaN/Inf causing 500s)
            return self.formatter.sanitize_json(response)
        finally:
            db.close()
    
    def get_charts(self, backtest_id: int, chart_types: Optional[List[str]] = None) -> Dict[str, Any]:
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
                charts['equity'] = self.chart_gen.create_equity_chart(equity_curve)
            
            if 'drawdown' in chart_types:
                charts['drawdown'] = self.chart_gen.create_drawdown_chart(equity_curve)
            
            if 'returns' in chart_types:
                charts['returns'] = self.chart_gen.create_returns_distribution_chart(equity_curve)
            
            if 'trades' in chart_types:
                charts['trades'] = self.chart_gen.create_trades_scatter_chart(trades, equity_curve)
            
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
    ) -> Dict[str, Any]:
        """
        Get TradingView Lightweight Charts formatted data with actual dataset data.
        
        This method is delegated from the original analytics service to maintain
        backward compatibility while using the new modular structure.
        """
        # Import here to avoid circular imports
        from ..analytics_service import AnalyticsService as LegacyAnalyticsService
        
        # Create a temporary instance of the legacy service for this complex method
        # TODO: Gradually migrate this method to use the new modular components
        legacy_service = LegacyAnalyticsService()
        
        return legacy_service.get_chart_data(
            backtest_id,
            include_trades,
            include_indicators,
            max_candles,
            start=start,
            end=end,
            tz=tz,
        )
    
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
