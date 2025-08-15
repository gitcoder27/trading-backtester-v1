"""
optimization_utils.py
Comprehensive optimization utilities for the backtesting system.
"""

import pandas as pd
import numpy as np
from numba import jit
import warnings
warnings.filterwarnings('ignore')

# Set pandas options for better performance
pd.set_option('mode.chained_assignment', None)
pd.set_option('compute.use_bottleneck', True)
pd.set_option('compute.use_numexpr', True)

@jit(nopython=True)
def fast_ema(prices, period):
    """
    Fast EMA calculation using numba.
    """
    alpha = 2.0 / (period + 1.0)
    ema = np.empty_like(prices)
    ema[0] = prices[0]
    
    for i in range(1, len(prices)):
        ema[i] = alpha * prices[i] + (1 - alpha) * ema[i - 1]
    
    return ema

@jit(nopython=True)
def fast_sma(prices, period):
    """
    Fast SMA calculation using numba.
    """
    sma = np.empty_like(prices)
    sma[:period-1] = np.nan
    
    for i in range(period-1, len(prices)):
        sma[i] = np.mean(prices[i-period+1:i+1])
    
    return sma

@jit(nopython=True)
def fast_bollinger_bands(prices, period=20, std_dev=2):
    """
    Fast Bollinger Bands calculation using numba.
    """
    mid = fast_sma(prices, period)
    
    upper = np.empty_like(prices)
    lower = np.empty_like(prices)
    
    for i in range(period-1, len(prices)):
        std = np.std(prices[i-period+1:i+1])
        upper[i] = mid[i] + std_dev * std
        lower[i] = mid[i] - std_dev * std
    
    upper[:period-1] = np.nan
    lower[:period-1] = np.nan
    
    return upper, mid, lower

@jit(nopython=True)
def fast_rsi(prices, period=14):
    """
    Fast RSI calculation using numba.
    """
    deltas = np.diff(prices)
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate initial averages
    avg_gain = np.mean(gains[:period])
    avg_loss = np.mean(losses[:period])
    
    rsi = np.empty(len(prices))
    rsi[:period] = np.nan
    
    if avg_loss == 0:
        rsi[period] = 100
    else:
        rs = avg_gain / avg_loss
        rsi[period] = 100 - (100 / (1 + rs))
    
    # Calculate RSI for remaining periods
    for i in range(period + 1, len(prices)):
        gain = gains[i-1] if i-1 < len(gains) else 0
        loss = losses[i-1] if i-1 < len(losses) else 0
        
        avg_gain = (avg_gain * (period - 1) + gain) / period
        avg_loss = (avg_loss * (period - 1) + loss) / period
        
        if avg_loss == 0:
            rsi[i] = 100
        else:
            rs = avg_gain / avg_loss
            rsi[i] = 100 - (100 / (1 + rs))
    
    return rsi

def optimize_dataframe_memory(df):
    """
    Optimize DataFrame memory usage by downcasting numeric types.
    """
    original_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
    
    for col in df.columns:
        if df[col].dtype == 'float64':
            df[col] = pd.to_numeric(df[col], downcast='float')
        elif df[col].dtype == 'int64':
            df[col] = pd.to_numeric(df[col], downcast='integer')
    
    final_memory = df.memory_usage(deep=True).sum() / 1024 / 1024  # MB
    memory_saved = original_memory - final_memory
    
    return df, memory_saved

def vectorized_signal_generation(df, strategy_type='ema_cross'):
    """
    Generate trading signals using vectorized operations.
    """
    if strategy_type == 'ema_cross':
        # EMA crossover signals
        df['ema_fast'] = df['close'].ewm(span=10).mean()
        df['ema_slow'] = df['close'].ewm(span=20).mean()
        
        # Vectorized signal calculation
        df['signal'] = 0
        df.loc[df['ema_fast'] > df['ema_slow'], 'signal'] = 1
        df.loc[df['ema_fast'] < df['ema_slow'], 'signal'] = -1
        
    elif strategy_type == 'rsi_bounce':
        # RSI oversold/overbought signals
        df['rsi'] = df['close'].rolling(14).apply(lambda x: fast_rsi(x.values))
        
        df['signal'] = 0
        df.loc[df['rsi'] < 30, 'signal'] = 1  # Oversold - buy
        df.loc[df['rsi'] > 70, 'signal'] = -1  # Overbought - sell
    
    return df

class PerformanceOptimizer:
    """
    Class to manage performance optimizations across the backtesting system.
    """
    
    @staticmethod
    def configure_pandas():
        """Configure pandas for optimal performance."""
        pd.set_option('mode.chained_assignment', None)
        pd.set_option('compute.use_bottleneck', True)
        pd.set_option('compute.use_numexpr', True)
    
    @staticmethod
    def estimate_processing_time(data_rows, strategy_complexity=1.0):
        """
        Estimate processing time based on data size and strategy complexity.
        
        Args:
            data_rows: Number of data rows
            strategy_complexity: Multiplier for strategy complexity (1.0 = simple, 2.0 = complex)
        
        Returns:
            Estimated time in seconds
        """
        # Base performance: ~50,000 rows per second for simple strategies
        base_speed = 50000
        adjusted_speed = base_speed / strategy_complexity
        
        estimated_time = data_rows / adjusted_speed
        return max(estimated_time, 0.1)  # Minimum 0.1 seconds
    
    @staticmethod
    def suggest_optimizations(data_rows, strategy_name):
        """
        Suggest optimizations based on data size and strategy type.
        """
        suggestions = []
        
        if data_rows > 100000:
            suggestions.append("Consider using a larger timeframe (5T, 10T) to reduce data points")
            suggestions.append("Use vectorized strategy implementation for better performance")
        
        if data_rows > 500000:
            suggestions.append("Consider data chunking for memory efficiency")
            suggestions.append("Use specialized high-performance indicators")
        
        if 'rsi' in strategy_name.lower():
            suggestions.append("Use fast_rsi implementation for better RSI calculation performance")
        
        if 'ema' in strategy_name.lower():
            suggestions.append("Use fast_ema implementation for better EMA calculation performance")
        
        return suggestions
