"""
Simple Analytics Service for testing
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
from backend.app.database.models import get_session_factory, Backtest


class SimpleAnalyticsService:
    """Minimal analytics service for testing"""
    
    def __init__(self):
        self.SessionLocal = get_session_factory()
    
    def get_performance_summary(self, backtest_id: int) -> Dict[str, Any]:
        """Get basic performance summary for a backtest"""
        db = self.SessionLocal()
        try:
            backtest = db.query(Backtest).filter(Backtest.id == backtest_id).first()
            
            if not backtest:
                return {'success': False, 'error': 'Backtest not found'}
            
            if not backtest.results:
                return {'success': False, 'error': 'No results available for this backtest'}
            
            # Parse results
            results = backtest.results
            equity_curve = pd.DataFrame(results.get('equity_curve', []))
            trades = pd.DataFrame(results.get('trades', []))
            metrics = results.get('metrics', {})
            
            # Basic analytics
            basic_analytics = self._compute_basic_analytics(equity_curve, trades)
            
            return {
                'success': True,
                'backtest_id': backtest_id,
                'performance': {
                    'basic_metrics': metrics,
                    'advanced_analytics': basic_analytics,
                    'trade_analysis': self._analyze_trades_basic(trades),
                    'risk_metrics': self._compute_risk_metrics_basic(equity_curve),
                    'time_analysis': {}
                }
            }
        except Exception as e:
            return {'success': False, 'error': f'Error processing analytics: {str(e)}'}
        finally:
            db.close()
    
    def _compute_basic_analytics(self, equity_curve: pd.DataFrame, trades: pd.DataFrame) -> Dict[str, Any]:
        """Compute basic analytics"""
        analytics = {}
        
        if not equity_curve.empty and 'equity' in equity_curve.columns:
            try:
                equity_values = equity_curve['equity'].astype(float)
                
                # Simple returns calculation
                returns = equity_values.pct_change().dropna()
                
                analytics.update({
                    'volatility_annualized': float(returns.std() * np.sqrt(252)) if len(returns) > 1 else 0.0,
                    'skewness': float(returns.skew()) if len(returns) > 2 else 0.0,
                    'kurtosis': float(returns.kurtosis()) if len(returns) > 3 else 0.0,
                    'downside_deviation': float(returns[returns < 0].std()) if len(returns[returns < 0]) > 1 else 0.0,
                    'sortino_ratio': self._calculate_sortino_basic(returns),
                    'calmar_ratio': self._calculate_calmar_basic(equity_values),
                })
            except Exception as e:
                analytics = {
                    'volatility_annualized': 0.0,
                    'skewness': 0.0,
                    'kurtosis': 0.0,
                    'downside_deviation': 0.0,
                    'sortino_ratio': 0.0,
                    'calmar_ratio': 0.0,
                    'error': str(e)
                }
        
        return analytics
    
    def _analyze_trades_basic(self, trades: pd.DataFrame) -> Dict[str, Any]:
        """Basic trade analysis"""
        if trades.empty or 'pnl' not in trades.columns:
            return {
                'avg_win': 0.0,
                'avg_loss': 0.0,
                'largest_win': 0.0,
                'largest_loss': 0.0,
                'consecutive_wins': 0,
                'consecutive_losses': 0
            }
        
        pnl = trades['pnl'].astype(float)
        wins = pnl[pnl > 0]
        losses = pnl[pnl <= 0]
        
        return {
            'avg_win': float(wins.mean()) if len(wins) > 0 else 0.0,
            'avg_loss': float(losses.mean()) if len(losses) > 0 else 0.0,
            'largest_win': float(wins.max()) if len(wins) > 0 else 0.0,
            'largest_loss': float(losses.min()) if len(losses) > 0 else 0.0,
            'consecutive_wins': self._max_consecutive(pnl > 0),
            'consecutive_losses': self._max_consecutive(pnl <= 0)
        }
    
    def _compute_risk_metrics_basic(self, equity_curve: pd.DataFrame) -> Dict[str, Any]:
        """Basic risk metrics"""
        if equity_curve.empty or 'equity' not in equity_curve.columns:
            return {
                'var_95': 0.0,
                'var_99': 0.0,
                'cvar_95': 0.0,
                'cvar_99': 0.0,
                'max_consecutive_losses': 0
            }
        
        equity_values = equity_curve['equity'].astype(float)
        returns = equity_values.pct_change().dropna()
        
        if len(returns) < 2:
            return {
                'var_95': 0.0,
                'var_99': 0.0,
                'cvar_95': 0.0,
                'cvar_99': 0.0,
                'max_consecutive_losses': 0
            }
        
        # Simple VaR calculation
        var_95 = float(returns.quantile(0.05))
        var_99 = float(returns.quantile(0.01))
        
        # Simple CVaR (expected shortfall)
        cvar_95 = float(returns[returns <= var_95].mean()) if len(returns[returns <= var_95]) > 0 else 0.0
        cvar_99 = float(returns[returns <= var_99].mean()) if len(returns[returns <= var_99]) > 0 else 0.0
        
        return {
            'var_95': var_95,
            'var_99': var_99,
            'cvar_95': cvar_95,
            'cvar_99': cvar_99,
            'max_consecutive_losses': self._max_consecutive(returns < 0)
        }
    
    def _calculate_sortino_basic(self, returns: pd.Series) -> float:
        """Basic Sortino ratio calculation"""
        if len(returns) < 2:
            return 0.0
        
        downside = returns[returns < 0]
        if len(downside) == 0:
            return float('inf') if returns.mean() > 0 else 0.0
        
        downside_std = downside.std()
        if downside_std == 0:
            return 0.0
        
        return float(returns.mean() / downside_std * np.sqrt(252))
    
    def _calculate_calmar_basic(self, equity_values: pd.Series) -> float:
        """Basic Calmar ratio calculation"""
        if len(equity_values) < 2:
            return 0.0
        
        total_return = (equity_values.iloc[-1] - equity_values.iloc[0]) / equity_values.iloc[0]
        
        # Calculate max drawdown
        peak = equity_values.expanding().max()
        drawdown = (equity_values - peak) / peak
        max_drawdown = abs(drawdown.min())
        
        if max_drawdown == 0:
            return float('inf') if total_return > 0 else 0.0
        
        return float(total_return / max_drawdown)
    
    def _max_consecutive(self, condition_series: pd.Series) -> int:
        """Calculate maximum consecutive True values"""
        if len(condition_series) == 0:
            return 0
        
        groups = (condition_series != condition_series.shift()).cumsum()
        consecutive_counts = condition_series.groupby(groups).sum()
        return int(consecutive_counts.max()) if len(consecutive_counts) > 0 else 0


# Test the service
if __name__ == "__main__":
    service = SimpleAnalyticsService()
    result = service.get_performance_summary(1)
    print(f"Result: {result}")
