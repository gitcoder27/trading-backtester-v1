"""
Execution Engine
Handles the core backtest execution logic with clean separation of concerns
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional, Union
from io import StringIO

from backtester.engine import BacktestEngine
from backtester.data_loader import load_csv
from .progress_tracker import ProgressTracker

logger = logging.getLogger(__name__)


class ExecutionEngineError(Exception):
    """Custom exception for execution engine errors"""
    pass


class ExecutionEngine:
    """
    Handles the core backtest execution with clean architecture.
    
    This class encapsulates:
    - Data loading and validation
    - Engine configuration
    - Backtest execution
    - Result extraction
    - Error handling and logging
    """
    
    def __init__(self):
        """Initialize execution engine"""
        self.default_config = {
            'initial_cash': 100000,
            'lots': 2,
            'option_delta': 0.5,
            'fee_per_trade': 4.0,
            'slippage': 0.0,
            'intraday': True,
            'daily_target': 30.0
        }
    
    def execute_backtest(
        self,
        data: Union[pd.DataFrame, str, bytes],
        strategy_instance: Any,
        engine_options: Optional[Dict[str, Any]] = None,
        progress_tracker: Optional[ProgressTracker] = None
    ) -> Dict[str, Any]:
        """
        Execute backtest with comprehensive error handling and progress tracking.
        
        Args:
            data: Market data (DataFrame, file path, or CSV bytes)
            strategy_instance: Instantiated strategy object
            engine_options: Optional engine configuration
            progress_tracker: Optional progress tracking
            
        Returns:
            Dict containing backtest results
            
        Raises:
            ExecutionEngineError: If execution fails
        """
        try:
            # Update progress
            if progress_tracker:
                progress_tracker.update(0.1, "Loading and validating data")
            
            # Load and validate data
            validated_data = self._load_and_validate_data(data)
            
            if progress_tracker:
                progress_tracker.update(0.2, "Configuring engine")
            
            # Configure engine
            engine_config = self._prepare_engine_config(engine_options)
            
            if progress_tracker:
                progress_tracker.update(0.3, "Initializing backtest engine")
            
            # Create and configure engine
            engine = self._create_engine(validated_data, strategy_instance, engine_config)
            
            if progress_tracker:
                progress_tracker.update(0.4, "Running backtest")
            
            # Execute backtest
            engine_result = self._run_engine(engine)
            
            if progress_tracker:
                progress_tracker.update(0.8, "Processing results")
            
            # Process and validate results
            processed_result = self._process_results(engine_result, engine_config)
            
            if progress_tracker:
                progress_tracker.update(0.9, "Finalizing results")
            
            # Add execution metadata
            processed_result['execution_info'] = {
                'data_points': len(validated_data),
                'engine_config': engine_config,
                'strategy_type': type(strategy_instance).__name__
            }
            
            if progress_tracker:
                progress_tracker.complete("Backtest execution completed successfully")
            
            logger.info(f"Backtest executed successfully with {len(validated_data)} data points")
            return processed_result
            
        except Exception as e:
            error_msg = f"Backtest execution failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            
            if progress_tracker:
                progress_tracker.fail(str(e))
            
            raise ExecutionEngineError(error_msg) from e
    
    def _load_and_validate_data(self, data: Union[pd.DataFrame, str, bytes]) -> pd.DataFrame:
        """Load and validate market data"""
        try:
            if isinstance(data, pd.DataFrame):
                validated_data = data.copy()
                logger.debug("Using provided DataFrame")
                
            elif isinstance(data, str):
                # Assume it's a file path
                validated_data = load_csv(data)
                logger.debug(f"Loaded data from file: {data}")
                
            elif isinstance(data, bytes):
                # CSV bytes data
                csv_string = data.decode('utf-8')
                validated_data = pd.read_csv(StringIO(csv_string))
                logger.debug("Loaded data from CSV bytes")
            
            else:
                raise ExecutionEngineError(f"Unsupported data type: {type(data)}")
            
            # Normalize timestamp column if present
            if 'timestamp' in validated_data.columns:
                try:
                    validated_data['timestamp'] = pd.to_datetime(validated_data['timestamp'])
                except Exception:
                    # Best-effort conversion with coercion
                    validated_data['timestamp'] = pd.to_datetime(validated_data['timestamp'], errors='coerce')

            # Validate data structure
            self._validate_data_structure(validated_data)
            
            return validated_data
            
        except Exception as e:
            raise ExecutionEngineError(f"Data loading failed: {str(e)}") from e
    
    def _validate_data_structure(self, data: pd.DataFrame):
        """Validate that data has required structure"""
        if data.empty:
            raise ExecutionEngineError("Data is empty")
        
        # Check for required columns (flexible validation)
        expected_columns = {'open', 'high', 'low', 'close'}
        data_columns = set(data.columns.str.lower())
        
        missing_columns = expected_columns - data_columns
        if missing_columns:
            logger.warning(f"Missing recommended columns: {missing_columns}")
            # Don't fail - let the backtester handle it
        
        # Basic data quality checks
        if len(data) < 2:
            raise ExecutionEngineError("Insufficient data points (minimum 2 required)")
        
        logger.debug(f"Data validation passed: {len(data)} rows, columns: {list(data.columns)}")
    
    def _prepare_engine_config(self, engine_options: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare engine configuration with defaults and validation"""
        config = self.default_config.copy()
        
        if engine_options:
            # Update with provided options
            config.update(engine_options)
        
        # Validate configuration values
        config = self._validate_engine_config(config)
        
        logger.debug(f"Engine configuration prepared: {config}")
        return config
    
    def _validate_engine_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate and sanitize engine configuration"""
        validated_config = {}
        
        # Validate numeric values
        numeric_fields = {
            'initial_cash': (1000, float('inf')),
            'lots': (1, 1000),
            'option_delta': (0.01, 1.0),
            'fee_per_trade': (0.0, 1000.0),
            'slippage': (0.0, 1.0),
            'daily_target': (0.0, float('inf'))
        }
        
        for field, (min_val, max_val) in numeric_fields.items():
            value = config.get(field, self.default_config[field])
            try:
                validated_value = float(value)
                if not (min_val <= validated_value <= max_val):
                    logger.warning(f"Value {field}={validated_value} outside recommended range [{min_val}, {max_val}]")
                validated_config[field] = validated_value
            except (ValueError, TypeError):
                logger.warning(f"Invalid {field} value: {value}, using default: {self.default_config[field]}")
                validated_config[field] = self.default_config[field]
        
        # Validate boolean fields
        validated_config['intraday'] = bool(config.get('intraday', self.default_config['intraday']))
        
        return validated_config
    
    def _create_engine(
        self, 
        data: pd.DataFrame, 
        strategy_instance: Any, 
        config: Dict[str, Any]
    ) -> BacktestEngine:
        """Create and configure backtest engine"""
        try:
            engine = BacktestEngine(
                data=data,
                strategy=strategy_instance,
                initial_cash=config['initial_cash'],
                lots=config['lots'],
                option_delta=config['option_delta'],
                fee_per_trade=config['fee_per_trade'],
                slippage=config['slippage'],
                intraday=config['intraday'],
                daily_profit_target=config['daily_target']
            )
            
            logger.debug("Backtest engine created successfully")
            return engine
            
        except Exception as e:
            raise ExecutionEngineError(f"Engine creation failed: {str(e)}") from e
    
    def _run_engine(self, engine: BacktestEngine) -> Dict[str, Any]:
        """Run the backtest engine with error handling"""
        try:
            logger.debug("Starting backtest engine execution")
            result = engine.run()
            
            if not result:
                raise ExecutionEngineError("Engine returned empty result")
            
            # Validate engine result structure
            self._validate_engine_result(result)
            
            logger.debug("Backtest engine execution completed")
            return result
            
        except Exception as e:
            raise ExecutionEngineError(f"Engine execution failed: {str(e)}") from e
    
    def _validate_engine_result(self, result: Dict[str, Any]):
        """Validate engine result structure"""
        required_keys = ['equity_curve', 'trade_log']
        missing_keys = [key for key in required_keys if key not in result]
        
        if missing_keys:
            raise ExecutionEngineError(f"Engine result missing required keys: {missing_keys}")
        
        # Validate equity curve
        equity_curve = result['equity_curve']
        if isinstance(equity_curve, pd.DataFrame) and equity_curve.empty:
            logger.warning("Equity curve is empty")
        
        # Validate trade log
        trade_log = result['trade_log']
        if isinstance(trade_log, pd.DataFrame):
            logger.debug(f"Trade log contains {len(trade_log)} trades")
        else:
            logger.warning(f"Trade log has unexpected type: {type(trade_log)}")
    
    def _process_results(self, engine_result: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Process and clean engine results"""
        try:
            # Extract core results
            equity_curve = engine_result.get('equity_curve', pd.DataFrame())
            trades = engine_result.get('trade_log', pd.DataFrame())
            
            # Process equity curve
            processed_equity = self._process_equity_curve(equity_curve)
            
            # Process trades
            processed_trades = self._process_trades(trades)
            
            # Build final result
            result = {
                'success': True,
                'equity_curve': processed_equity,
                'trades': processed_trades,
                'raw_engine_result': engine_result  # Keep original for debugging
            }
            
            logger.debug("Results processed successfully")
            return result
            
        except Exception as e:
            raise ExecutionEngineError(f"Result processing failed: {str(e)}") from e
    
    def _process_equity_curve(self, equity_curve: pd.DataFrame) -> list:
        """Convert equity curve to JSON-serializable format"""
        if equity_curve.empty:
            return []
        
        try:
            # Convert to list of dictionaries
            processed = []
            has_ts_col = 'timestamp' in equity_curve.columns
            for idx, row in equity_curve.iterrows():
                record = {}
                
                # Prefer explicit timestamp column if present
                if has_ts_col:
                    ts_val = row['timestamp']
                    try:
                        ts = pd.to_datetime(ts_val)
                        record['timestamp'] = ts.isoformat()
                    except Exception:
                        record['timestamp'] = str(ts_val)
                else:
                    # Fallback to index
                    if hasattr(idx, 'isoformat'):
                        record['timestamp'] = idx.isoformat()
                    else:
                        record['timestamp'] = str(idx)
                
                # Handle equity value
                if 'equity' in row:
                    record['equity'] = float(row['equity'])
                elif len(row) > 0:
                    record['equity'] = float(row.iloc[0])  # First column
                else:
                    record['equity'] = 0.0
                
                processed.append(record)
            
            logger.debug(f"Processed {len(processed)} equity curve points")
            return processed
            
        except Exception as e:
            logger.error(f"Equity curve processing failed: {e}")
            return []
    
    def _process_trades(self, trades: pd.DataFrame) -> list:
        """Convert trades to JSON-serializable format"""
        if trades.empty:
            return []
        
        try:
            # Convert to list of dictionaries with proper type handling
            processed = []
            for _, row in trades.iterrows():
                record = {}
                
                for col, value in row.items():
                    if pd.isna(value):
                        record[col] = None
                    elif isinstance(value, (pd.Timestamp, np.datetime64)):
                        record[col] = pd.Timestamp(value).isoformat()
                    elif isinstance(value, (np.int64, np.int32)):
                        record[col] = int(value)
                    elif isinstance(value, (np.float64, np.float32)):
                        record[col] = float(value)
                    else:
                        record[col] = str(value)
                
                processed.append(record)
            
            logger.debug(f"Processed {len(processed)} trades")
            return processed
            
        except Exception as e:
            logger.error(f"Trades processing failed: {e}")
            return []
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about the execution engine"""
        return {
            'default_config': self.default_config,
            'engine_type': 'BacktestEngine',
            'supported_data_types': ['DataFrame', 'file_path', 'csv_bytes']
        }
