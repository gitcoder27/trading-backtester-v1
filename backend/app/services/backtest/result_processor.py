"""
Result Processor
Handles metrics calculation, data serialization, and database storage
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from backtester.metrics import (
    total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor,
    largest_winning_trade, largest_losing_trade, average_holding_time,
    max_consecutive_wins, max_consecutive_losses, trading_sessions_days
)
from backend.app.database.models import get_session_factory, BacktestJob

logger = logging.getLogger(__name__)


class ResultProcessorError(Exception):
    """Custom exception for result processing errors"""
    pass


class ResultProcessor:
    """
    Handles result processing with clean architecture principles.
    
    This class encapsulates:
    - Metrics calculation
    - Data serialization
    - Database storage
    - Result validation
    - Error handling
    """
    
    def __init__(self):
        """Initialize result processor"""
        self.SessionLocal = get_session_factory()
    
    def process_backtest_results(
        self,
        raw_results: Dict[str, Any],
        initial_cash: float,
        strategy_name: str = "Unknown"
    ) -> Dict[str, Any]:
        """
        Process raw backtest results into complete, serialized format.
        
        Args:
            raw_results: Raw results from execution engine
            initial_cash: Initial cash amount for metrics calculation
            strategy_name: Name of the strategy used
            
        Returns:
            Dict containing processed results with metrics
            
        Raises:
            ResultProcessorError: If processing fails
        """
        try:
            logger.debug(f"Processing backtest results for strategy: {strategy_name}")
            
            # Extract data from raw results
            equity_curve_data = raw_results.get('equity_curve', [])
            # Accept both 'trades' and 'trade_log' from execution engine
            trades_data = raw_results.get('trades') or raw_results.get('trade_log') or []
            
            # Convert to DataFrames for metrics calculation
            equity_df = self._create_equity_dataframe(equity_curve_data)
            trades_df = self._create_trades_dataframe(trades_data)
            
            # Calculate comprehensive metrics
            metrics = self._calculate_comprehensive_metrics(equity_df, trades_df, initial_cash)
            
            # Serialize all data
            serialized_results = self._serialize_results(
                equity_curve_data, trades_data, metrics, raw_results
            )
            
            # Add processing metadata
            serialized_results.update({
                'processing_info': {
                    'processed_at': datetime.now(timezone.utc).isoformat(),
                    'strategy_name': strategy_name,
                    'initial_cash': initial_cash,
                    'data_points': len(equity_curve_data),
                    'total_trades': len(trades_data)
                }
            })
            
            logger.info(f"Results processed successfully: {len(trades_data)} trades, "
                       f"{len(equity_curve_data)} equity points")
            
            return serialized_results
            
        except Exception as e:
            error_msg = f"Result processing failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ResultProcessorError(error_msg) from e
    
    def _create_equity_dataframe(self, equity_data: list) -> pd.DataFrame:
        """Create equity DataFrame from serialized data"""
        if not equity_data:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(equity_data)
            
            # Ensure timestamp column exists and is properly formatted
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')
            
            # Ensure equity column exists
            if 'equity' not in df.columns and len(df.columns) > 0:
                df['equity'] = df.iloc[:, 0]  # Use first column as equity
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to create equity DataFrame: {e}")
            return pd.DataFrame()
    
    def _create_trades_dataframe(self, trades_data: list) -> pd.DataFrame:
        """Create trades DataFrame from serialized data"""
        if not trades_data:
            return pd.DataFrame()
        
        try:
            df = pd.DataFrame(trades_data)
            
            # Convert timestamp columns
            timestamp_columns = ['entry_time', 'exit_time', 'timestamp']
            for col in timestamp_columns:
                if col in df.columns:
                    df[col] = pd.to_datetime(df[col], errors='coerce')
            
            # Ensure numeric columns are properly typed
            numeric_columns = ['pnl', 'entry_price', 'exit_price', 'quantity', 'size']
            for col in numeric_columns:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            return df
            
        except Exception as e:
            logger.error(f"Failed to create trades DataFrame: {e}")
            return pd.DataFrame()
    
    def _calculate_comprehensive_metrics(
        self, 
            equity_curve: pd.DataFrame, 
            trades: pd.DataFrame, 
            initial_cash: float
    ) -> Dict[str, Any]:
        """Calculate comprehensive backtest metrics with error handling"""
        metrics = {}
        
        try:
            # Basic return metrics
            if not equity_curve.empty and 'equity' in equity_curve.columns:
                metrics.update(self._calculate_return_metrics(equity_curve, initial_cash))
            
            # Risk metrics
            if not equity_curve.empty:
                metrics.update(self._calculate_risk_metrics(equity_curve))
            
            # Trade metrics
            if not trades.empty:
                metrics.update(self._calculate_trade_metrics(trades))
            else:
                # Provide required defaults when no trades present
                metrics.update({'total_trades': 0, 'win_rate': 0.0, 'profit_factor': 0.0})
            
            # Time-based metrics
            if not equity_curve.empty:
                metrics.update(self._calculate_time_metrics(equity_curve))
            
            # Ensure required keys exist for schema compliance
            metrics.setdefault('total_trades', len(trades))
            metrics.setdefault('win_rate', 0.0)
            metrics.setdefault('profit_factor', 0.0)

            logger.debug(f"Calculated {len(metrics)} metrics")
            return metrics
            
        except Exception as e:
            logger.error(f"Metrics calculation failed: {e}")
            return self._get_default_metrics()
    
    def _calculate_return_metrics(self, equity_curve: pd.DataFrame, initial_cash: float) -> Dict[str, Any]:
        """Calculate return-based metrics"""
        try:
            eq_df = equity_curve[['equity']] if 'equity' in equity_curve.columns else equity_curve
            
            # Total return
            total_return_val = total_return(eq_df)
            total_return_pct = total_return_val * 100
            
            # Sharpe ratio
            sharpe = sharpe_ratio(eq_df)
            
            return {
                'total_return': total_return_val,
                'total_return_pct': total_return_pct,
                'sharpe_ratio': sharpe,
                'final_equity': float(eq_df['equity'].iloc[-1]) if 'equity' in eq_df.columns and len(eq_df) > 0 else initial_cash
            }
            
        except Exception as e:
            logger.error(f"Return metrics calculation failed: {e}")
            return {
                'total_return': 0.0,
                'total_return_pct': 0.0,
                'sharpe_ratio': 0.0,
                'final_equity': initial_cash
            }
    
    def _calculate_risk_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, Any]:
        """Calculate risk-based metrics"""
        try:
            eq_df = equity_curve[['equity']] if 'equity' in equity_curve.columns else equity_curve
            
            # Max drawdown
            max_dd = max_drawdown(eq_df)
            max_dd_pct = max_dd * 100
            
            return {
                'max_drawdown': max_dd,
                'max_drawdown_pct': max_dd_pct,
            }
            
        except Exception as e:
            logger.error(f"Risk metrics calculation failed: {e}")
            return {
                'max_drawdown': 0.0,
                'max_drawdown_pct': 0.0,
            }
    
    def _calculate_trade_metrics(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Calculate trade-based metrics"""
        try:
            # Basic trade counts
            total_trades_count = len(trades)
            
            # PnL-based metrics (if PnL column exists)
            pnl_metrics = {}
            if 'pnl' in trades.columns:
                pnl_data = pd.to_numeric(trades['pnl'], errors='coerce').dropna()
                
                if len(pnl_data) > 0:
                    # Win rate
                    win_rate_val = win_rate(pnl_data) * 100
                    
                    # Profit factor
                    profit_factor_val = profit_factor(pnl_data)
                    
                    # Largest trades
                    largest_win = largest_winning_trade(pnl_data)
                    largest_loss = largest_losing_trade(pnl_data)
                    
                    # Consecutive trades
                    max_wins = max_consecutive_wins(pnl_data)
                    max_losses = max_consecutive_losses(pnl_data)
                    
                    pnl_metrics = {
                        'win_rate': win_rate_val,
                        'profit_factor': profit_factor_val,
                        'largest_winning_trade': largest_win,
                        'largest_losing_trade': largest_loss,
                        'max_consecutive_wins': max_wins,
                        'max_consecutive_losses': max_losses,
                    }
            
            # Holding time metrics
            holding_time_metrics = {}
            if 'entry_time' in trades.columns and 'exit_time' in trades.columns:
                try:
                    entry_times = pd.to_datetime(trades['entry_time'], errors='coerce')
                    exit_times = pd.to_datetime(trades['exit_time'], errors='coerce')
                    valid_mask = entry_times.notna() & exit_times.notna()
                    
                    if valid_mask.any():
                        avg_holding = average_holding_time(
                            entry_times[valid_mask], 
                            exit_times[valid_mask]
                        )
                        holding_time_metrics['average_holding_time'] = avg_holding
                except Exception:
                    pass
            
            # Combine all trade metrics
            trade_metrics = {
                'total_trades': total_trades_count,
                **pnl_metrics,
                **holding_time_metrics
            }
            
            return trade_metrics
            
        except Exception as e:
            logger.error(f"Trade metrics calculation failed: {e}")
            return {'total_trades': 0}
    
    def _calculate_time_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, Any]:
        """Calculate time-based metrics"""
        try:
            # Trading sessions based on timestamp column
            trading_days = trading_sessions_days(equity_curve)
            
            return {
                'trading_sessions_days': trading_days,
                'data_points': len(equity_curve)
            }
            
        except Exception as e:
            logger.error(f"Time metrics calculation failed: {e}")
            return {
                'trading_sessions_days': 0,
                'data_points': 0
            }
    
    def _serialize_results(
        self,
        equity_curve: list,
        trades: list,
        metrics: Dict[str, Any],
        raw_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Serialize all results into final format"""
        execution_info = raw_results.get('execution_info', {}) if isinstance(raw_results, dict) else {}
        engine_cfg = execution_info.get('engine_config', {}) if isinstance(execution_info, dict) else {}
        # Sanitize metrics for JSON (no NaN/Inf)
        clean_metrics = {}
        for k, v in (metrics or {}).items():
            try:
                if isinstance(v, float) and (pd.isna(v) or not np.isfinite(v)):
                    clean_metrics[k] = 0.0
                else:
                    clean_metrics[k] = v
            except Exception:
                clean_metrics[k] = v

        return {
            'success': True,
            'equity_curve': equity_curve,
            'trade_log': trades,
            'metrics': clean_metrics,
            'indicators': {},
            'engine_config': engine_cfg,
        }
    
    def save_to_database(self, job_id: int, processed_results: Dict[str, Any]) -> bool:
        """
        Save processed results to database.
        
        Args:
            job_id: Backtest job ID
            processed_results: Processed results from process_backtest_results
            
        Returns:
            bool: True if saved successfully, False otherwise
        """
        try:
            db = self.SessionLocal()
            try:
                # Find the job
                job = db.query(BacktestJob).filter(BacktestJob.id == job_id).first()
                if not job:
                    logger.error(f"Job {job_id} not found")
                    return False
                
                # Update job with results
                job.results = processed_results
                job.status = 'completed'
                job.completed_at = datetime.now(timezone.utc)
                job.progress = 1.0
                job.current_step = 'Completed'
                
                # Extract and save metrics if available
                metrics = processed_results.get('metrics', {})
                if metrics and hasattr(job, 'metrics'):
                    # Update metrics fields if they exist
                    for metric_name, value in metrics.items():
                        if hasattr(job, metric_name):
                            setattr(job, metric_name, value)
                
                db.commit()
                logger.info(f"Results saved to database for job {job_id}")
                return True
                
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"Failed to save results to database for job {job_id}: {e}")
            return False
    
    def _get_default_metrics(self) -> Dict[str, Any]:
        """Get default metrics structure when calculation fails"""
        return {
            'total_return': 0.0,
            'total_return_pct': 0.0,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'max_drawdown_pct': 0.0,
            'win_rate': 0.0,
            'profit_factor': 0.0,
            'total_trades': 0,
            'largest_winning_trade': 0.0,
            'largest_losing_trade': 0.0,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'average_holding_time': 0.0,
            'trading_sessions_days': 0,
            'data_points': 0,
            'final_equity': 0.0
        }
    
    def validate_results(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate processed results structure.
        
        Args:
            results: Results to validate
            
        Returns:
            Dict with validation status and any issues found
        """
        issues = []
        
        # Check required keys
        required_keys = ['success', 'equity_curve', 'trades', 'metrics']
        for key in required_keys:
            if key not in results:
                issues.append(f"Missing required key: {key}")
        
        # Validate data types
        if 'equity_curve' in results and not isinstance(results['equity_curve'], list):
            issues.append("equity_curve should be a list")
        
        if 'trades' in results and not isinstance(results['trades'], list):
            issues.append("trades should be a list")
        
        if 'metrics' in results and not isinstance(results['metrics'], dict):
            issues.append("metrics should be a dict")
        
        # Check data consistency
        if 'processing_info' in results:
            proc_info = results['processing_info']
            actual_trades = len(results.get('trades', []))
            expected_trades = proc_info.get('total_trades', 0)
            
            if actual_trades != expected_trades:
                issues.append(f"Trade count mismatch: {actual_trades} vs {expected_trades}")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues
        }
