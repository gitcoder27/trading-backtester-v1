"""
Performance Calculator
Handles all performance metric calculations for backtest results
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
from .data_formatter import DataFormatter


class PerformanceCalculator:
    """Calculator for performance metrics and advanced analytics"""
    
    def __init__(self):
        self.formatter = DataFormatter()
    
    def compute_basic_analytics(self, equity_curve: pd.DataFrame, trades: pd.DataFrame) -> Dict[str, Any]:
        """Compute comprehensive analytics from equity curve and trades"""
        if equity_curve.empty:
            return self._get_empty_analytics()
        
        # Extract returns
        returns = self.formatter.normalize_returns_data(equity_curve)
        if returns.empty:
            return self._get_empty_analytics()
        
        # Calculate basic metrics
        analytics = {
            'volatility_annualized': self._calculate_volatility(returns),
            'skewness': self._calculate_skewness(returns),
            'kurtosis': self._calculate_kurtosis(returns),
            'downside_deviation': self._calculate_downside_deviation(returns),
            'sortino_ratio': self._calculate_sortino_ratio(returns),
            'calmar_ratio': self._calculate_calmar_ratio(equity_curve),
        }
        
        # Add trade analysis if available
        if not trades.empty:
            trade_metrics = self._analyze_trades_basic(trades)
            analytics.update(trade_metrics)
        
        return analytics
    
    def _calculate_volatility(self, returns: pd.Series, annualize: bool = True) -> float:
        """Calculate volatility (standard deviation of returns)"""
        if len(returns) < 2:
            return 0.0
        
        vol = float(returns.std())
        
        if annualize:
            # Annualize based on data frequency (assuming minute data)
            annualization_factor = self.formatter.calculate_annualization_factor('minute')
            vol *= np.sqrt(annualization_factor)
        
        return vol
    
    def _calculate_skewness(self, returns: pd.Series) -> float:
        """Calculate skewness of returns distribution"""
        if len(returns) < 3:
            return 0.0
        return float(returns.skew())
    
    def _calculate_kurtosis(self, returns: pd.Series) -> float:
        """Calculate kurtosis of returns distribution"""
        if len(returns) < 4:
            return 0.0
        return float(returns.kurtosis())
    
    def _calculate_downside_deviation(self, returns: pd.Series) -> float:
        """Calculate downside deviation (standard deviation of negative returns)"""
        negative_returns = returns[returns < 0]
        if len(negative_returns) < 2:
            return 0.0
        return float(negative_returns.std())
    
    def _calculate_sortino_ratio(self, returns: pd.Series) -> float:
        """Calculate Sortino ratio (return vs downside risk)"""
        if len(returns) < 2:
            return 0.0
        
        downside_returns = returns[returns < 0]
        if len(downside_returns) == 0:
            return float('inf') if returns.mean() > 0 else 0.0
        
        downside_std = downside_returns.std()
        if downside_std == 0:
            return 0.0
        
        # Annualize the ratio
        annualization_factor = self.formatter.calculate_annualization_factor('minute')
        return float(returns.mean() / downside_std * np.sqrt(annualization_factor))
    
    def _calculate_calmar_ratio(self, equity_curve: pd.DataFrame) -> float:
        """Calculate Calmar ratio (annual return / max drawdown)"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return 0.0
        
        equity_values = equity_curve['equity'].astype(float)
        if len(equity_values) < 2:
            return 0.0
        
        # Calculate total return
        total_return = (equity_values.iloc[-1] - equity_values.iloc[0]) / equity_values.iloc[0]
        
        # Calculate max drawdown
        peak = equity_values.expanding().max()
        drawdown = (equity_values - peak) / peak
        max_drawdown = abs(drawdown.min())
        
        if max_drawdown == 0:
            return float('inf') if total_return > 0 else 0.0
        
        return float(total_return / max_drawdown)
    
    def _analyze_trades_basic(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Basic trade analysis with safe error handling"""
        if trades.empty or 'pnl' not in trades.columns:
            return {
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'consecutive_wins': 0,
                'consecutive_losses': 0,
                'avg_holding_time': 0.0,
                'total_long_trades': 0,
                'total_short_trades': 0,
                'winning_long_trades': 0,
                'winning_short_trades': 0,
            }
        
        # Convert PnL to numeric safely
        try:
            pnl = pd.to_numeric(trades['pnl'], errors='coerce').fillna(0)
            wins = pnl[pnl > 0]
            losses = pnl[pnl <= 0]
        except Exception:
            return self._get_empty_trade_metrics()
        
        # Calculate holding time
        avg_holding_time = self._calculate_avg_holding_time(trades)
        
        # Calculate consecutive wins/losses
        consecutive_wins = self._calculate_consecutive_trades(pnl, positive=True)
        consecutive_losses = self._calculate_consecutive_trades(pnl, positive=False)
        
        return {
            'avg_win': float(wins.mean()) if len(wins) > 0 else 0.0,
            'avg_loss': float(losses.mean()) if len(losses) > 0 else 0.0,
            'largest_win': float(wins.max()) if len(wins) > 0 else 0.0,
            'largest_loss': float(losses.min()) if len(losses) > 0 else 0.0,
            'consecutive_wins': consecutive_wins,
            'consecutive_losses': consecutive_losses,
            'avg_holding_time': avg_holding_time,
            'total_long_trades': self._count_direction_trades(trades, 'long'),
            'total_short_trades': self._count_direction_trades(trades, 'short'),
            'winning_long_trades': self._count_winning_direction_trades(trades, 'long'),
            'winning_short_trades': self._count_winning_direction_trades(trades, 'short'),
        }
    
    def _calculate_avg_holding_time(self, trades: pd.DataFrame) -> float:
        """Calculate average holding time in minutes"""
        if 'entry_time' not in trades.columns or 'exit_time' not in trades.columns:
            return 0.0
        
        try:
            entry_times = pd.to_datetime(trades['entry_time'], errors='coerce')
            exit_times = pd.to_datetime(trades['exit_time'], errors='coerce')
            valid_mask = entry_times.notna() & exit_times.notna()
            
            if not valid_mask.any():
                return 0.0
            
            holding_times = (exit_times[valid_mask] - entry_times[valid_mask]).dt.total_seconds() / 60
            return float(holding_times.mean())
        except Exception:
            return 0.0
    
    def _calculate_consecutive_trades(self, pnl: pd.Series, positive: bool = True) -> int:
        """Calculate maximum consecutive winning or losing trades"""
        try:
            if len(pnl) == 0:
                return 0
            
            if positive:
                condition = pnl > 0
            else:
                condition = pnl <= 0
            
            # Convert to boolean and count consecutive
            bool_series = condition.astype(bool)
            if not bool_series.any():
                return 0
            
            groups = (bool_series != bool_series.shift()).cumsum()
            consecutive_counts = bool_series.groupby(groups).sum()
            return int(consecutive_counts.max()) if len(consecutive_counts) > 0 else 0
        except Exception:
            return 0
    
    def _count_direction_trades(self, trades: pd.DataFrame, direction: str) -> int:
        """Count trades by direction (long/short)"""
        if 'direction' not in trades.columns and 'side' not in trades.columns:
            return len(trades) if direction == 'long' else 0  # Default assumption
        
        direction_col = 'direction' if 'direction' in trades.columns else 'side'
        trades_copy = trades.copy()
        try:
            trades_copy[direction_col] = trades_copy[direction_col].astype(str).str.lower()
        except Exception:
            return len(trades_copy) if direction.lower() == 'long' else 0
        direction_trades = trades_copy[trades_copy[direction_col] == direction.lower()]
        return len(direction_trades)
    
    def _count_winning_direction_trades(self, trades: pd.DataFrame, direction: str) -> int:
        """Count winning trades by direction"""
        if 'pnl' not in trades.columns:
            return 0
        
        direction_col = 'direction' if 'direction' in trades.columns else 'side'
        if direction_col not in trades.columns:
            # If no direction info, assume all long and count winning trades
            pnl_series = pd.to_numeric(trades['pnl'], errors='coerce').fillna(0)
            if direction.lower() == 'long':
                return int((pnl_series > 0).sum())
            return 0
        
        trades_copy = trades.copy()
        try:
            trades_copy[direction_col] = trades_copy[direction_col].astype(str).str.lower()
        except Exception:
            return 0
        pnl_series = pd.to_numeric(trades_copy['pnl'], errors='coerce').fillna(0)
        direction_mask = trades_copy[direction_col] == direction.lower()
        winning_mask = pnl_series > 0
        return int((direction_mask & winning_mask).sum())
    
    def compute_rolling_metrics(self, equity_curve: pd.DataFrame, window: int = 50) -> pd.DataFrame:
        """Compute rolling performance metrics"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return pd.DataFrame()
        
        returns = self.formatter.normalize_returns_data(equity_curve)
        if len(returns) < window:
            return pd.DataFrame()
        
        # Calculate rolling metrics
        rolling_data = {
            'timestamp': returns.index,
            'rolling_sharpe': self._calculate_rolling_sharpe(returns, window),
            'rolling_volatility': returns.rolling(window).std(),
            'rolling_return': returns.rolling(window).mean()
        }
        
        return pd.DataFrame(rolling_data).dropna()
    
    def _calculate_rolling_sharpe(self, returns: pd.Series, window: int) -> pd.Series:
        """Calculate rolling Sharpe ratio"""
        annualization_factor = np.sqrt(self.formatter.calculate_annualization_factor('minute'))
        
        def sharpe_calc(x):
            if len(x) < 2 or x.std() == 0:
                return 0.0
            return (x.mean() / x.std()) * annualization_factor
        
        return returns.rolling(window).apply(sharpe_calc, raw=False)
    
    def _get_empty_analytics(self) -> Dict[str, Any]:
        """Return empty analytics structure"""
        return {
            'volatility_annualized': 0.0,
            'skewness': 0.0,
            'kurtosis': 0.0,
            'downside_deviation': 0.0,
            'sortino_ratio': 0.0,
            'calmar_ratio': 0.0,
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'avg_holding_time': 0.0,
            'total_long_trades': 0,
            'total_short_trades': 0,
            'winning_long_trades': 0,
            'winning_short_trades': 0,
        }
    
    def _get_empty_trade_metrics(self) -> Dict[str, Any]:
        """Return empty trade metrics structure"""
        return {
            'avg_win': 0.0,
            'avg_loss': 0.0,
            'largest_win': 0.0,
            'largest_loss': 0.0,
            'consecutive_wins': 0,
            'consecutive_losses': 0,
            'avg_holding_time': 0.0,
            'total_long_trades': 0,
            'total_short_trades': 0,
            'winning_long_trades': 0,
            'winning_short_trades': 0,
        }
