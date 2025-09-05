"""
Backtest Service - Backward Compatibility Bridge
Maintains full backward compatibility while using the new modular architecture
"""

# Import the modular backtest service
from .backtest.backtest_service import BacktestService as ModularBacktestService
from .backtest.progress_tracker import ProgressCallback

# For any complex methods not yet migrated, import from legacy
# (Currently all major methods are migrated, but keeping this for safety)
# from .backtest_service_legacy import BacktestService as LegacyBacktestService


class BacktestService:
    """
    Backward compatibility bridge for the Backtest Service.
    
    This class maintains the exact same API as the original BacktestService
    while delegating operations to the new modular components.
    
    The new modular architecture provides:
    - Better separation of concerns
    - Improved error handling
    - Enhanced testability
    - Cleaner code organization
    """
    
    def __init__(self):
        """Initialize with modular service"""
        self.modular_service = ModularBacktestService()
        # self.legacy_service = LegacyBacktestService()  # If needed for complex methods
    
    def run_backtest(
        self,
        data=None,
        strategy: str = None,
        strategy_params=None,
        engine_options=None,
        progress_callback=None,
        dataset_path: str = None,
        csv_bytes: bytes = None,
    ):
        """Run backtest - uses modular service with full compatibility.
        Accepts legacy arguments like dataset_path/csv_bytes in addition to data.
        """
        # Coerce legacy args into the unified 'data' parameter
        input_data = data
        if input_data is None:
            if csv_bytes is not None:
                input_data = csv_bytes
            elif dataset_path is not None:
                input_data = dataset_path
        if input_data is None:
            raise ValueError("No data source provided: pass data, dataset_path, or csv_bytes")

        return self.modular_service.run_backtest(
            data=input_data,
            strategy=strategy,
            strategy_params=strategy_params,
            engine_options=engine_options,
            progress_callback=progress_callback
        )
    
    def run_backtest_from_upload(
        self,
        csv_content: bytes,
        strategy: str,
        strategy_params=None,
        engine_options=None,
        progress_callback=None
    ):
        """Run backtest from upload - uses modular service"""
        return self.modular_service.run_backtest_from_upload(
            csv_content=csv_content,
            strategy=strategy,
            strategy_params=strategy_params,
            engine_options=engine_options,
            progress_callback=progress_callback
        )
    
    def save_backtest_to_db(self, job_id: int, result):
        """Save to database - uses modular service"""
        return self.modular_service.save_backtest_to_db(job_id, result)
    
    def _call_progress_callback(self, callback, progress: float, message: str):
        """Legacy progress callback support - maintains exact compatibility"""
        return self.modular_service._call_progress_callback(callback, progress, message)
    
    def _load_strategy_class(self, strategy_path: str):
        """Legacy strategy loading - delegates to new strategy loader"""
        return self.modular_service.strategy_loader.load_strategy_class(strategy_path)
    
    def _calculate_metrics(self, equity_curve, trades, initial_cash):
        """Legacy metrics calculation - uses new result processor"""
        # Convert data to expected format for result processor
        equity_data = []
        if hasattr(equity_curve, 'iterrows'):
            for idx, row in equity_curve.iterrows():
                equity_data.append({
                    'timestamp': idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    'equity': float(row.iloc[0]) if len(row) > 0 else 0.0
                })
        
        trades_data = []
        if hasattr(trades, 'iterrows'):
            for _, row in trades.iterrows():
                trade_record = {}
                for col, value in row.items():
                    if hasattr(value, 'isoformat'):
                        trade_record[col] = value.isoformat()
                    else:
                        trade_record[col] = value
                trades_data.append(trade_record)
        
        # Use result processor to calculate metrics
        raw_results = {
            'equity_curve': equity_data,
            'trades': trades_data
        }
        
        processed = self.modular_service.result_processor.process_backtest_results(
            raw_results, initial_cash
        )
        
        return processed.get('metrics', {})
    
    def _serialize_results(self, equity_curve, trades, metrics):
        """Legacy serialization - uses new result processor"""
        # Convert inputs to expected format
        equity_data = []
        trades_data = []
        
        # Handle equity curve
        if hasattr(equity_curve, 'iterrows'):
            for idx, row in equity_curve.iterrows():
                equity_data.append({
                    'timestamp': idx.isoformat() if hasattr(idx, 'isoformat') else str(idx),
                    'equity': float(row.iloc[0]) if len(row) > 0 else 0.0
                })
        
        # Handle trades
        if hasattr(trades, 'iterrows'):
            for _, row in trades.iterrows():
                trade_record = {}
                for col, value in row.items():
                    if hasattr(value, 'isoformat'):
                        trade_record[col] = value.isoformat()
                    elif hasattr(value, 'item'):
                        trade_record[col] = value.item()
                    else:
                        trade_record[col] = value
                trades_data.append(trade_record)
        
        # Use result processor serialization
        return self.modular_service.result_processor._serialize_results(
            equity_data, trades_data, metrics, {}
        )

    # Compatibility helpers expected by existing tests
    def load_strategy(self, strategy_path: str):
        """Load a strategy class by module path."""
        try:
            return self.modular_service.strategy_loader.load_strategy_class(strategy_path)
        except Exception as e:
            # Match legacy behavior of raising ValueError
            raise ValueError(str(e))

    def load_data(self, data=None, dataset_path: str = None, csv_bytes: bytes = None):
        """Load dataset from path or CSV bytes into a DataFrame."""
        source = data if data is not None else (csv_bytes if csv_bytes is not None else dataset_path)
        if source is None:
            raise ValueError("No data source provided: pass data, dataset_path, or csv_bytes")
        # Use execution engine's loader
        return self.modular_service.execution_engine._load_and_validate_data(source)

    def _serialize_timestamp(self, ts):
        """Serialize timestamps to ISO string, handle NaT gracefully."""
        import pandas as pd
        try:
            if ts is None or (hasattr(pd, 'isna') and pd.isna(ts)):
                return None
        except Exception:
            return None
        if hasattr(ts, 'isoformat'):
            return ts.isoformat()
        return str(ts) if ts is not None else None

    def _serialize_trade(self, trade: dict) -> dict:
        """Serialize a trade record with robust type coercion."""
        out = {}
        import numpy as np
        import pandas as pd
        for k, v in (trade or {}).items():
            # Handle NaT/NaN early
            try:
                if hasattr(pd, 'isna') and pd.isna(v):
                    out[k] = None
                    continue
            except Exception:
                pass

            if hasattr(v, 'isoformat'):
                out[k] = v.isoformat()
            elif isinstance(v, (np.integer,)):
                out[k] = float(v)
            elif isinstance(v, (np.floating,)):
                out[k] = float(v)
            elif isinstance(v, (np.bool_,)):
                out[k] = bool(v)
            else:
                out[k] = v
        return out
    
    # Enhanced methods available through modular architecture
    def discover_strategies(self):
        """Discover available strategies - new enhanced method"""
        return self.modular_service.discover_strategies()
    
    def validate_strategy(self, strategy_path: str):
        """Validate strategy - new enhanced method"""
        return self.modular_service.validate_strategy(strategy_path)
    
    def validate_strategy_parameters(self, strategy_path: str, params):
        """Validate strategy parameters - new enhanced method"""
        return self.modular_service.validate_strategy_parameters(strategy_path, params)
    
    def validate_market_data(self, data):
        """Validate market data - new enhanced method"""
        return self.modular_service.validate_market_data(data)
    
    def get_default_engine_options(self):
        """Get default engine options - new enhanced method"""
        return self.modular_service.get_default_engine_options()
    
    def get_service_info(self):
        """Get service information - new enhanced method"""
        return self.modular_service.get_service_info()
    
    # Delegate any other methods to modular service
    def __getattr__(self, name):
        """Delegate any missing methods to modular service"""
        if hasattr(self.modular_service, name):
            return getattr(self.modular_service, name)
        raise AttributeError(f"'BacktestService' object has no attribute '{name}'")
