"""
Backtest Service
Core service that wraps the existing backtester framework for web API usage
"""

import os
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional, Callable
import json
from datetime import datetime, timezone
import importlib.util
import logging

from backtester.engine import BacktestEngine
from backtester.data_loader import load_csv
from backtester.metrics import (
    total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor,
    largest_winning_trade, largest_losing_trade, average_holding_time,
    max_consecutive_wins, max_consecutive_losses, trading_sessions_days
)
from backend.app.database.models import get_session_factory, BacktestJob, Trade, BacktestMetrics, Dataset

logger = logging.getLogger(__name__)


class ProgressCallback:
    """Callback class for tracking backtest progress"""
    
    def __init__(self, job_id: int):
        self.job_id = job_id
        self.SessionLocal = get_session_factory()
    
    def update(self, progress: float, step: str = None):
        """Update progress in database"""
        try:
            db = self.SessionLocal()
            job = db.query(BacktestJob).filter(BacktestJob.id == self.job_id).first()
            if job:
                job.progress = min(progress, 1.0)
                if step:
                    job.current_step = step
                db.commit()
            db.close()
        except Exception as e:
            logger.error(f"Failed to update progress for job {self.job_id}: {e}")


class BacktestService:
    """Service for running backtests using the existing framework"""
    
    def __init__(self):
        self.SessionLocal = get_session_factory()
    
    def _call_progress_callback(self, callback, progress: float, message: str):
        """Helper method to call progress callback regardless of type"""
        if callback:
            if hasattr(callback, 'update'):
                callback.update(progress, message)
            elif callable(callback):
                callback(progress, message)

    def run_backtest(
        self,
        strategy: str,
        strategy_params: Dict[str, Any],
        dataset_path: str,
        engine_options: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict[str, Any]:
        """
        Run a backtest and return JSON-serializable results
        
        Args:
            strategy: Strategy module.class name (e.g., "strategies.ema10_scalper.EMA10ScalperStrategy")
            strategy_params: Parameters to pass to strategy
            dataset_path: Path to CSV data file
            engine_options: Engine configuration (initial_cash, lots, etc.)
            progress_callback: Optional callback for progress updates
            
        Returns:
            Dict with equity_curve, trades, metrics, and metadata
        """
        try:
            self._call_progress_callback(progress_callback, 0.1, "Loading data")
            
            # Load data
            data = load_csv(dataset_path)
            if data is None or data.empty:
                raise ValueError(f"Failed to load data from {dataset_path}")
            
            if progress_callback:
                self._call_progress_callback(progress_callback, 0.2, "Loading strategy")
            
            # Load strategy class
            strategy_class = self._load_strategy_class(strategy)
            
            # Prepare strategy parameters
            if strategy_params:
                strategy_instance = strategy_class(params=strategy_params)
            else:
                strategy_instance = strategy_class()
            
            if progress_callback:
                self._call_progress_callback(progress_callback, 0.3, "Initializing engine")
            
            # Configure engine options
            engine_config = {
                'initial_cash': engine_options.get('initial_cash', 100000),
                'lots': engine_options.get('lots', 2),
                'option_delta': engine_options.get('option_delta', 0.5),
                'fee_per_trade': engine_options.get('fee_per_trade', 4.0),
                'slippage': engine_options.get('slippage', 0.0),
                'intraday': engine_options.get('intraday', True),
                'daily_target': engine_options.get('daily_target', 30.0)
            }
            
            # Initialize engine
            engine = BacktestEngine(
                data=data,
                strategy=strategy_instance,
                initial_cash=engine_config['initial_cash'],
                lots=engine_config['lots'],
                option_delta=engine_config['option_delta'],
                fee_per_trade=engine_config['fee_per_trade'],
                slippage=engine_config['slippage'],
                intraday=engine_config['intraday'],
                daily_profit_target=engine_config['daily_target']
            )
            
            if progress_callback:
                self._call_progress_callback(progress_callback, 0.4, "Running backtest")
            
            # Run backtest
            engine_result = engine.run()
            
            if progress_callback:
                self._call_progress_callback(progress_callback, 0.8, "Calculating metrics")
            
            # Extract equity curve and trades from engine result
            equity_curve = engine_result['equity_curve']
            trades = engine_result['trade_log']
            
            # Calculate metrics
            metrics = self._calculate_metrics(equity_curve, trades, engine_config['initial_cash'])
            
            if progress_callback:
                self._call_progress_callback(progress_callback, 0.9, "Serializing results")
            
            # Convert to JSON-serializable format
            result = self._serialize_results(equity_curve, trades, metrics, engine_config)
            
            if progress_callback:
                self._call_progress_callback(progress_callback, 1.0, "Completed")
            
            return {
                'success': True,
                'result': result,
                'metadata': {
                    'strategy': strategy,
                    'strategy_params': strategy_params,
                    'dataset_path': dataset_path,
                    'engine_options': engine_config,
                    'data_rows': len(data),
                    'completed_at': datetime.now(timezone.utc).isoformat()
                }
            }
            
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            if progress_callback:
                self._call_progress_callback(progress_callback, 0.0, f"Failed: {str(e)}")
            
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def run_backtest_from_upload(
        self,
        strategy: str,
        strategy_params: Dict[str, Any],
        csv_content: bytes,
        engine_options: Dict[str, Any],
        progress_callback: Optional[ProgressCallback] = None
    ) -> Dict[str, Any]:
        """Run backtest from uploaded CSV content"""
        try:
            # Save uploaded content to temporary file
            temp_path = f"temp/upload_{datetime.now().timestamp()}.csv"
            os.makedirs("temp", exist_ok=True)
            
            with open(temp_path, 'wb') as f:
                f.write(csv_content)
            
            # Run backtest
            result = self.run_backtest(
                strategy=strategy,
                strategy_params=strategy_params,
                dataset_path=temp_path,
                engine_options=engine_options,
                progress_callback=progress_callback
            )
            
            # Clean up temp file
            try:
                os.remove(temp_path)
            except:
                pass  # Ignore cleanup errors
            
            return result
            
        except Exception as e:
            logger.error(f"Upload backtest failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _load_strategy_class(self, strategy_path: str):
        """Load strategy class from module.class path"""
        try:
            # Parse module.class format
            if '.' not in strategy_path:
                raise ValueError(f"Invalid strategy path format: {strategy_path}")
            
            module_path, class_name = strategy_path.rsplit('.', 1)
            
            # Import module
            module = importlib.import_module(module_path)
            
            # Get class
            if not hasattr(module, class_name):
                raise ValueError(f"Class {class_name} not found in module {module_path}")
            
            strategy_class = getattr(module, class_name)
            
            return strategy_class
            
        except Exception as e:
            raise ValueError(f"Failed to load strategy {strategy_path}: {e}")
    
    def _calculate_metrics(self, equity_curve: pd.DataFrame, trades: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """Calculate comprehensive performance metrics"""
        try:
            if equity_curve.empty:
                return {'error': 'No equity curve data'}
            
            # Basic metrics
            total_ret = total_return(equity_curve)
            total_ret_pct = total_ret * 100  # total_return already returns percentage as decimal
            
            sharpe = sharpe_ratio(equity_curve)
            max_dd = max_drawdown(equity_curve)
            max_dd_pct = (max_dd / initial_cash) * 100
            
            # Trade-based metrics
            if not trades.empty:
                win_rt = win_rate(trades)
                profit_fac = profit_factor(trades)
                largest_win = largest_winning_trade(trades)
                largest_loss = largest_losing_trade(trades)
                avg_hold_time = average_holding_time(trades)
                max_cons_wins = max_consecutive_wins(trades)
                max_cons_losses = max_consecutive_losses(trades)
            else:
                win_rt = profit_fac = largest_win = largest_loss = 0
                avg_hold_time = max_cons_wins = max_cons_losses = 0
            
            # Additional metrics
            total_trades = len(trades) if not trades.empty else 0
            trading_days = trading_sessions_days(equity_curve) if not equity_curve.empty else 0
            
            return {
                'total_return': float(total_ret),
                'total_return_percent': float(total_ret_pct),
                'sharpe_ratio': float(sharpe) if not np.isnan(sharpe) else 0.0,
                'max_drawdown': float(max_dd),
                'max_drawdown_percent': float(max_dd_pct),
                'win_rate': float(win_rt),
                'profit_factor': float(profit_fac),
                'total_trades': int(total_trades),
                'largest_winning_trade': float(largest_win),
                'largest_losing_trade': float(largest_loss),
                'average_holding_time': float(avg_hold_time),
                'max_consecutive_wins': int(max_cons_wins),
                'max_consecutive_losses': int(max_cons_losses),
                'trading_days': int(trading_days)
            }
            
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")
            return {'error': str(e)}
    
    def _serialize_results(
        self,
        equity_curve: pd.DataFrame,
        trades: pd.DataFrame,
        metrics: Dict[str, Any],
        engine_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Convert pandas objects to JSON-serializable format"""
        
        # Convert equity curve
        equity_data = []
        if not equity_curve.empty:
            for _, row in equity_curve.iterrows():
                equity_data.append({
                    'timestamp': row.name.isoformat() if hasattr(row.name, 'isoformat') else str(row.name),
                    'equity': float(row['equity']) if 'equity' in row else float(row.iloc[0])
                })
        
        # Convert trades
        trades_data = []
        if not trades.empty:
            for _, trade in trades.iterrows():
                trade_dict = {}
                for col in trade.index:
                    value = trade[col]
                    if pd.isna(value):
                        trade_dict[col] = None
                    elif hasattr(value, 'isoformat'):  # datetime
                        trade_dict[col] = value.isoformat()
                    elif isinstance(value, (np.integer, np.floating)):
                        trade_dict[col] = float(value)
                    else:
                        trade_dict[col] = str(value)
                trades_data.append(trade_dict)
        
        return {
            'equity_curve': equity_data,
            'trades': trades_data,
            'metrics': metrics,
            'engine_config': engine_config
        }
    
    def save_backtest_to_db(self, job_id: int, result: Dict[str, Any]) -> bool:
        """Save backtest results to database for analytics"""
        try:
            db = self.SessionLocal()
            
            # Update job with results
            job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
            if job:
                job.result_data = json.dumps(result)
                job.status = "completed"
                job.completed_at = datetime.utcnow()
                
                # Calculate actual duration
                if job.started_at:
                    duration = (job.completed_at - job.started_at).total_seconds()
                    job.actual_duration = duration
                
                db.commit()
            
            db.close()
            return True
            
        except Exception as e:
            logger.error(f"Failed to save backtest to DB: {e}")
            return False
