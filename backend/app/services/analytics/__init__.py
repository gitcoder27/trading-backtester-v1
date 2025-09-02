"""
Analytics Package
Modular analytics components for backtest analysis and visualization
"""

# Import individual components directly for standalone usage
from .data_formatter import DataFormatter
from .performance_calculator import PerformanceCalculator
from .chart_generator import ChartGenerator
from .trade_analyzer import TradeAnalyzer
from .risk_calculator import RiskCalculator

# Main analytics service for backward compatibility
# Import only when needed to avoid circular dependencies
def get_analytics_service():
    """Factory function to get the main analytics service"""
    from .analytics_service import AnalyticsService
    return AnalyticsService

# Legacy import compatibility
try:
    from .analytics_service import AnalyticsService
except ImportError:
    # If database dependencies are not available, provide a fallback
    AnalyticsService = None

__all__ = [
    'AnalyticsService',
    'PerformanceCalculator', 
    'ChartGenerator',
    'TradeAnalyzer',
    'RiskCalculator',
    'DataFormatter',
    'get_analytics_service'
]
