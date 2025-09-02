"""
Backtest Package
Modular backtest components for clean architecture and separation of concerns
"""

# Import individual components directly for standalone usage
from .strategy_loader import StrategyLoader
from .progress_tracker import ProgressTracker

# Main backtest service for backward compatibility
# Import only when needed to avoid dependency issues
def get_backtest_service():
    """Factory function to get the main backtest service"""
    from .backtest_service import BacktestService
    return BacktestService

# Legacy import compatibility
try:
    from .backtest_service import BacktestService
    from .execution_engine import ExecutionEngine
    from .result_processor import ResultProcessor
except ImportError:
    # If dependencies are not available, provide fallbacks
    BacktestService = None
    ExecutionEngine = None
    ResultProcessor = None

__all__ = [
    'BacktestService',
    'StrategyLoader',
    'ExecutionEngine', 
    'ResultProcessor',
    'ProgressTracker',
    'get_backtest_service'
]
