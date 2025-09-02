"""
Risk Calculator
Specialized calculations for risk metrics and analysis
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from .data_formatter import DataFormatter


class RiskCalculator:
    """Calculator for risk-specific metrics and analysis"""
    
    def __init__(self):
        self.formatter = DataFormatter()
    
    def compute_risk_metrics(self, equity_curve: pd.DataFrame) -> Dict[str, Any]:
        """Compute comprehensive risk metrics"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return self._get_empty_risk_metrics()
        
        returns = self.formatter.normalize_returns_data(equity_curve)
        if returns.empty:
            return self._get_empty_risk_metrics()
        
        # Calculate VaR and CVaR
        var_95, var_99 = self._calculate_var(returns)
        cvar_95, cvar_99 = self._calculate_cvar(returns, var_95, var_99)
        
        # Calculate consecutive loss periods
        max_consecutive_losses = self._calculate_max_consecutive_losses(returns)
        
        # Calculate trading session metrics
        trading_days, trading_years = self._calculate_trading_sessions(equity_curve)
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'max_consecutive_losses': max_consecutive_losses,
            'trading_sessions_days': trading_days,
            'trading_sessions_years': trading_years
        }
    
    def _calculate_var(self, returns: pd.Series) -> tuple[float, float]:
        """Calculate Value at Risk at 95% and 99% confidence levels"""
        if len(returns) < 2:
            return 0.0, 0.0
        
        var_95 = float(returns.quantile(0.05))
        var_99 = float(returns.quantile(0.01))
        
        return var_95, var_99
    
    def _calculate_cvar(self, returns: pd.Series, var_95: float, var_99: float) -> tuple[float, float]:
        """Calculate Conditional Value at Risk (Expected Shortfall)"""
        if len(returns) < 2:
            return 0.0, 0.0
        
        # CVaR is the average of returns below the VaR threshold
        returns_below_var95 = returns[returns <= var_95]
        returns_below_var99 = returns[returns <= var_99]
        
        cvar_95 = float(returns_below_var95.mean()) if len(returns_below_var95) > 0 else 0.0
        cvar_99 = float(returns_below_var99.mean()) if len(returns_below_var99) > 0 else 0.0
        
        return cvar_95, cvar_99
    
    def _calculate_max_consecutive_losses(self, returns: pd.Series) -> int:
        """Calculate maximum consecutive loss periods"""
        if len(returns) == 0:
            return 0
        
        try:
            loss_mask = (returns < 0).astype(bool)
            if not loss_mask.any():
                return 0
            
            # Group consecutive losses
            loss_groups = (loss_mask != loss_mask.shift()).cumsum()
            consecutive_losses = loss_mask.groupby(loss_groups).sum()
            
            return int(consecutive_losses.max()) if len(consecutive_losses) > 0 else 0
        except Exception:
            return 0
    
    def _calculate_trading_sessions(self, equity_curve: pd.DataFrame) -> tuple[int, float]:
        """Calculate trading session metrics"""
        trading_days = 0
        trading_years = 0.0
        
        if 'timestamp' in equity_curve.columns:
            try:
                dates = pd.to_datetime(equity_curve['timestamp']).dt.date
                trading_days = int(pd.Series(dates).nunique())
                trading_years = float(trading_days / 252.0)  # 252 trading days per year
            except Exception:
                pass
        
        return trading_days, trading_years
    
    def compute_drawdown_analysis(self, equity_curve: pd.DataFrame) -> Dict[str, Any]:
        """Comprehensive drawdown analysis"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return {
                'max_drawdown': 0.0,
                'max_drawdown_duration': 0,
                'drawdown_periods': [],
                'avg_drawdown': 0.0,
                'drawdown_frequency': 0.0
            }
        
        equity_values = equity_curve['equity'].astype(float)
        
        # Calculate drawdown series
        peak = equity_values.expanding().max()
        drawdown = (equity_values - peak) / peak
        
        # Find drawdown periods
        drawdown_periods = self._identify_drawdown_periods(drawdown, equity_curve)
        
        # Calculate metrics
        max_drawdown = abs(drawdown.min())
        avg_drawdown = abs(drawdown[drawdown < 0].mean()) if (drawdown < 0).any() else 0.0
        max_duration = max([p['duration_days'] for p in drawdown_periods], default=0)
        frequency = len(drawdown_periods) / len(equity_values) if len(equity_values) > 0 else 0.0
        
        return {
            'max_drawdown': float(max_drawdown),
            'max_drawdown_duration': max_duration,
            'drawdown_periods': drawdown_periods,
            'avg_drawdown': float(avg_drawdown),
            'drawdown_frequency': float(frequency)
        }
    
    def _identify_drawdown_periods(self, drawdown: pd.Series, equity_curve: pd.DataFrame) -> list[Dict[str, Any]]:
        """Identify distinct drawdown periods"""
        periods = []
        
        try:
            # Find where drawdown starts and ends
            in_drawdown = drawdown < 0
            drawdown_changes = in_drawdown != in_drawdown.shift()
            
            start_idx = None
            for i, (idx, is_change) in enumerate(drawdown_changes.items()):
                if is_change and in_drawdown.iloc[i]:
                    # Start of drawdown
                    start_idx = i
                elif is_change and not in_drawdown.iloc[i] and start_idx is not None:
                    # End of drawdown
                    end_idx = i - 1
                    
                    # Calculate period metrics
                    period_drawdown = drawdown.iloc[start_idx:end_idx+1]
                    max_dd_in_period = abs(period_drawdown.min())
                    
                    # Calculate duration
                    duration_points = end_idx - start_idx + 1
                    duration_days = self._calculate_duration_days(
                        equity_curve, start_idx, end_idx
                    )
                    
                    periods.append({
                        'start_index': start_idx,
                        'end_index': end_idx,
                        'max_drawdown': float(max_dd_in_period),
                        'duration_points': duration_points,
                        'duration_days': duration_days
                    })
                    
                    start_idx = None
        except Exception:
            # Return empty list if analysis fails
            pass
        
        return periods
    
    def _calculate_duration_days(self, equity_curve: pd.DataFrame, start_idx: int, end_idx: int) -> int:
        """Calculate duration in days for a drawdown period"""
        if 'timestamp' not in equity_curve.columns:
            return end_idx - start_idx + 1  # Fallback to point count
        
        try:
            timestamps = pd.to_datetime(equity_curve['timestamp'])
            start_date = timestamps.iloc[start_idx]
            end_date = timestamps.iloc[end_idx]
            duration = (end_date - start_date).days
            return max(1, duration)  # At least 1 day
        except Exception:
            return end_idx - start_idx + 1
    
    def calculate_correlation_metrics(self, equity_curve: pd.DataFrame, benchmark_returns: pd.Series = None) -> Dict[str, Any]:
        """Calculate correlation and beta metrics"""
        returns = self.formatter.normalize_returns_data(equity_curve)
        
        if returns.empty or benchmark_returns is None or benchmark_returns.empty:
            return {
                'correlation': 0.0,
                'beta': 0.0,
                'alpha': 0.0,
                'tracking_error': 0.0
            }
        
        # Align returns with benchmark
        aligned_data = pd.DataFrame({
            'strategy': returns,
            'benchmark': benchmark_returns
        }).dropna()
        
        if len(aligned_data) < 2:
            return {
                'correlation': 0.0,
                'beta': 0.0,
                'alpha': 0.0,
                'tracking_error': 0.0
            }
        
        strategy_returns = aligned_data['strategy']
        bench_returns = aligned_data['benchmark']
        
        # Calculate metrics
        correlation = float(strategy_returns.corr(bench_returns))
        
        # Beta: covariance(strategy, benchmark) / variance(benchmark)
        beta = float(strategy_returns.cov(bench_returns) / bench_returns.var()) if bench_returns.var() > 0 else 0.0
        
        # Alpha: strategy_return - (risk_free_rate + beta * (benchmark_return - risk_free_rate))
        # Simplified: strategy_return - beta * benchmark_return (assuming risk_free_rate = 0)
        alpha = float(strategy_returns.mean() - beta * bench_returns.mean())
        
        # Tracking error: standard deviation of (strategy_returns - benchmark_returns)
        tracking_error = float((strategy_returns - bench_returns).std())
        
        return {
            'correlation': correlation,
            'beta': beta,
            'alpha': alpha,
            'tracking_error': tracking_error
        }
    
    def _get_empty_risk_metrics(self) -> Dict[str, Any]:
        """Return empty risk metrics structure"""
        return {
            'var_95': 0.0,
            'var_99': 0.0,
            'cvar_95': 0.0,
            'cvar_99': 0.0,
            'max_consecutive_losses': 0,
            'trading_sessions_days': 0,
            'trading_sessions_years': 0.0
        }
