"""
Analytics Service - Backward Compatibility Bridge
Maintains full backward compatibility while using the new modular architecture
"""

# Import the modular analytics service
from .analytics.analytics_service import AnalyticsService as ModularAnalyticsService

# For complex methods not yet migrated, import from legacy
from .analytics_service_legacy import AnalyticsService as LegacyAnalyticsService
from typing import Optional


class AnalyticsService:
    """
    Backward compatibility bridge for the Analytics Service.
    
    This class maintains the exact same API as the original AnalyticsService
    while delegating operations to the new modular components when possible,
    and falling back to the legacy implementation for complex methods that
    haven't been fully migrated yet.
    """
    
    def __init__(self):
        # Initialize both modular and legacy services
        self.modular_service = ModularAnalyticsService()
        self.legacy_service = LegacyAnalyticsService()
    
    def get_performance_summary(self, backtest_id: int):
        """Get comprehensive performance summary - uses modular service"""
        return self.modular_service.get_performance_summary(backtest_id)
    
    def get_charts(self, backtest_id: int, chart_types=None):
        """Generate charts - uses modular service"""
        return self.modular_service.get_charts(backtest_id, chart_types)
    
    def compare_strategies(self, backtest_ids):
        """Compare strategies - uses modular service"""
        return self.modular_service.compare_strategies(backtest_ids)
    
    def get_trades_data(self, backtest_id: int, page: int = 1, page_size: int = 100, 
                       sort_by: str = "entry_time", sort_order: str = "desc", 
                       filter_profitable=None):
        """Get trades data - uses modular service"""
        return self.modular_service.get_trades_data(
            backtest_id, page, page_size, sort_by, sort_order, filter_profitable
        )
    
    def get_chart_data(self, backtest_id: int, include_trades: bool = True, 
                      include_indicators: bool = True, max_candles: Optional[int] = None,
                      start: Optional[str] = None, end: Optional[str] = None,
                      tz: Optional[str] = None):
        """Get chart data - uses legacy service (complex method)"""
        return self.legacy_service.get_chart_data(
            backtest_id, include_trades, include_indicators, max_candles,
            start=start, end=end, tz=tz
        )
    
    # Additional methods for enhanced functionality using modular components
    def get_rolling_metrics(self, backtest_id: int, window: int = 50):
        """Get rolling metrics - new modular method"""
        return self.modular_service.get_rolling_metrics(backtest_id, window)
    
    def get_drawdown_analysis(self, backtest_id: int):
        """Get drawdown analysis - new modular method"""
        return self.modular_service.get_drawdown_analysis(backtest_id)
    
    def get_trade_streaks(self, backtest_id: int):
        """Get trade streaks - new modular method"""
        return self.modular_service.get_trade_streaks(backtest_id)
    
    # Delegate any other methods to legacy service for full compatibility
    def __getattr__(self, name):
        """Delegate any missing methods to legacy service"""
        if hasattr(self.legacy_service, name):
            return getattr(self.legacy_service, name)
        raise AttributeError(f"'AnalyticsService' object has no attribute '{name}'")
