"""
Backtest Service - Modular Version
Main orchestrator for backtest operations with clean separation of concerns
"""

import logging
from typing import Dict, Any, Optional, Union, Callable
from io import StringIO
import pandas as pd

from .strategy_loader import StrategyLoader, StrategyLoaderError
from .execution_engine import ExecutionEngine, ExecutionEngineError
from .result_processor import ResultProcessor, ResultProcessorError
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class BacktestServiceError(Exception):
    """Custom exception for backtest service errors"""
    pass


class BacktestService:
    """
    Main backtest service that orchestrates all backtest operations.
    
    This modular service delegates specific operations to specialized components:
    - StrategyLoader: Strategy discovery, loading, and validation
    - ExecutionEngine: Core backtest execution logic
    - ResultProcessor: Metrics calculation and serialization
    - ProgressTracker: Progress tracking and database updates
    """
    
    def __init__(self):
        """Initialize the modular backtest service"""
        # Initialize specialized components
        self.strategy_loader = StrategyLoader()
        self.execution_engine = ExecutionEngine()
        self.result_processor = ResultProcessor()
        
        logger.info("Modular BacktestService initialized")
    
    def run_backtest(
        self,
        data: Union[pd.DataFrame, str],
        strategy: str,
        strategy_params: Optional[Dict[str, Any]] = None,
        engine_options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run a complete backtest with comprehensive error handling.
        
        Args:
            data: Market data (DataFrame or file path)
            strategy: Strategy module.class name (e.g., "strategies.ema10_scalper.EMA10ScalperStrategy")
            strategy_params: Optional strategy parameters
            engine_options: Optional engine configuration
            progress_callback: Optional progress callback function
            
        Returns:
            Dict containing complete backtest results
            
        Raises:
            BacktestServiceError: If backtest fails at any stage
        """
        progress_tracker = None
        
        try:
            # Initialize progress tracking
            if progress_callback:
                # Extract job_id if it's the legacy callback format
                job_id = getattr(progress_callback, 'job_id', None)
                progress_tracker = ProgressTracker(job_id)
            
            logger.info(f"Starting backtest with strategy: {strategy}")
            
            if progress_tracker:
                progress_tracker.start("Initializing backtest")
            
            # Step 1: Load and validate strategy
            if progress_tracker:
                progress_tracker.update(0.1, "Loading strategy")
            
            strategy_instance = self.strategy_loader.create_strategy_instance(
                strategy, strategy_params
            )
            
            # Step 2: Execute backtest
            if progress_tracker:
                progress_tracker.update(0.2, "Starting backtest execution")
            
            execution_results = self.execution_engine.execute_backtest(
                data=data,
                strategy_instance=strategy_instance,
                engine_options=engine_options,
                progress_tracker=progress_tracker
            )
            
            # Step 3: Process results and calculate metrics
            if progress_tracker:
                progress_tracker.update(0.85, "Processing results and calculating metrics")
            
            initial_cash = engine_options.get('initial_cash', 100000) if engine_options else 100000
            
            processed_results = self.result_processor.process_backtest_results(
                raw_results=execution_results,
                initial_cash=initial_cash,
                strategy_name=strategy
            )
            
            # Step 4: Validate final results
            validation_result = self.result_processor.validate_results(processed_results)
            if not validation_result['valid']:
                logger.warning(f"Result validation issues: {validation_result['issues']}")
            
            if progress_tracker:
                progress_tracker.complete("Backtest completed successfully")
            
            logger.info(f"Backtest completed successfully for strategy: {strategy}")
            return processed_results
            
        except (StrategyLoaderError, ExecutionEngineError, ResultProcessorError) as e:
            # These are our custom exceptions with good error messages
            if progress_tracker:
                progress_tracker.fail(str(e))
            logger.error(f"Backtest failed: {e}")
            raise BacktestServiceError(str(e)) from e
            
        except Exception as e:
            # Unexpected errors
            error_msg = f"Unexpected error during backtest: {str(e)}"
            if progress_tracker:
                progress_tracker.fail(error_msg)
            logger.error(error_msg, exc_info=True)
            raise BacktestServiceError(error_msg) from e
    
    def run_backtest_from_upload(
        self,
        csv_content: bytes,
        strategy: str,
        strategy_params: Optional[Dict[str, Any]] = None,
        engine_options: Optional[Dict[str, Any]] = None,
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Run backtest from uploaded CSV data.
        
        Args:
            csv_content: CSV file content as bytes
            strategy: Strategy module.class name
            strategy_params: Optional strategy parameters
            engine_options: Optional engine configuration
            progress_callback: Optional progress callback
            
        Returns:
            Dict containing complete backtest results
        """
        try:
            logger.info("Running backtest from uploaded CSV data")
            
            # The execution engine handles CSV bytes directly
            return self.run_backtest(
                data=csv_content,
                strategy=strategy,
                strategy_params=strategy_params,
                engine_options=engine_options,
                progress_callback=progress_callback
            )
            
        except Exception as e:
            error_msg = f"Failed to run backtest from upload: {str(e)}"
            logger.error(error_msg)
            raise BacktestServiceError(error_msg) from e
    
    def save_backtest_to_db(self, job_id: int, result: Dict[str, Any]) -> bool:
        """
        Save backtest results to database.
        
        Args:
            job_id: Database job ID
            result: Processed backtest results
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            return self.result_processor.save_to_database(job_id, result)
        except Exception as e:
            logger.error(f"Failed to save backtest to database: {e}")
            return False
    
    # Strategy management methods
    def discover_strategies(self) -> Dict[str, str]:
        """Discover available strategies"""
        try:
            return self.strategy_loader.discover_strategies()
        except Exception as e:
            logger.error(f"Strategy discovery failed: {e}")
            return {}
    
    def validate_strategy(self, strategy_path: str) -> Dict[str, Any]:
        """Validate strategy can be loaded"""
        try:
            strategy_class = self.strategy_loader.load_strategy_class(strategy_path)
            return {
                'valid': True,
                'strategy_name': strategy_class.__name__,
                'message': 'Strategy validated successfully'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': f'Strategy validation failed: {str(e)}'
            }
    
    def validate_strategy_parameters(
        self, 
        strategy_path: str, 
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate strategy parameters"""
        return self.strategy_loader.validate_strategy_parameters(strategy_path, params)
    
    # Engine and configuration methods
    def get_default_engine_options(self) -> Dict[str, Any]:
        """Get default engine configuration"""
        return self.execution_engine.default_config.copy()
    
    def validate_engine_options(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Validate engine configuration options"""
        try:
            validated_config = self.execution_engine._prepare_engine_config(options)
            return {
                'valid': True,
                'validated_config': validated_config,
                'message': 'Engine options validated successfully'
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': f'Engine options validation failed: {str(e)}'
            }
    
    # Data validation methods
    def validate_market_data(self, data: Union[pd.DataFrame, str, bytes]) -> Dict[str, Any]:
        """Validate market data before running backtest"""
        try:
            # Use execution engine's data loading to validate
            if isinstance(data, bytes):
                # Convert bytes to DataFrame for validation
                csv_string = data.decode('utf-8')
                df = pd.read_csv(StringIO(csv_string))
            elif isinstance(data, str):
                df = pd.read_csv(data)
            elif isinstance(data, pd.DataFrame):
                df = data
            else:
                raise ValueError(f"Unsupported data type: {type(data)}")
            
            # Basic validation
            if df.empty:
                return {
                    'valid': False,
                    'error': 'Data is empty',
                    'message': 'Market data validation failed: empty dataset'
                }
            
            # Check columns
            required_columns = {'open', 'high', 'low', 'close'}
            available_columns = set(df.columns.str.lower())
            missing_columns = required_columns - available_columns
            
            validation_result = {
                'valid': len(missing_columns) == 0,
                'data_points': len(df),
                'columns': list(df.columns),
                'date_range': {
                    'start': str(df.index[0]) if hasattr(df.index, 'dtype') else 'N/A',
                    'end': str(df.index[-1]) if hasattr(df.index, 'dtype') else 'N/A'
                }
            }
            
            if missing_columns:
                validation_result.update({
                    'warning': f'Missing recommended columns: {missing_columns}',
                    'message': f'Data validation warning: missing columns {missing_columns}'
                })
            else:
                validation_result['message'] = 'Market data validated successfully'
            
            return validation_result
            
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
                'message': f'Market data validation failed: {str(e)}'
            }
    
    # Utility and information methods
    def get_service_info(self) -> Dict[str, Any]:
        """Get information about the backtest service and its components"""
        return {
            'service_type': 'ModularBacktestService',
            'components': {
                'strategy_loader': {
                    'cache_info': self.strategy_loader.get_cache_info(),
                    'strategies_dir': self.strategy_loader.strategies_dir
                },
                'execution_engine': self.execution_engine.get_engine_info(),
                'result_processor': {
                    'database_connected': True  # TODO: Add actual check
                }
            },
            'supported_operations': [
                'run_backtest',
                'run_backtest_from_upload', 
                'save_backtest_to_db',
                'discover_strategies',
                'validate_strategy',
                'validate_strategy_parameters',
                'validate_market_data',
                'validate_engine_options'
            ]
        }
    
    def clear_caches(self):
        """Clear all internal caches"""
        self.strategy_loader.clear_cache()
        logger.info("All caches cleared")
    
    # Legacy compatibility methods
    def _call_progress_callback(self, callback, progress: float, message: str):
        """Legacy progress callback support"""
        if hasattr(callback, 'update'):
            callback.update(progress, message)
        elif callable(callback):
            callback(progress, message)
