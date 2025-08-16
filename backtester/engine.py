"""
engine.py
Core backtesting engine for running trading strategies on historical data.
Optimized for performance with vectorized operations.
"""

import pandas as pd
import numpy as np
from numba import jit
import warnings
warnings.filterwarnings('ignore')

@jit(nopython=True)
def _vectorized_backtest_core(signals, prices, option_delta, option_qty, option_price_per_unit, fee_per_trade, initial_equity):
    """
    Simplified vectorized backtest core using numba JIT compilation.
    Returns only equity curve for performance.
    Fees are deducted at trade close so the equity curve reflects costs.
    """
    n = len(signals)
    equity_curve = np.zeros(n)

    position = 0  # 0=none, 1=long, -1=short
    entry_price = 0.0
    current_equity = initial_equity

    for i in range(n):
        signal = signals[i]
        price = prices[i]

        # Entry logic
        if position == 0:
            if signal == 1:  # Long entry
                position = 1
                entry_price = price
            elif signal == -1:  # Short entry
                position = -1
                entry_price = price
        else:
            # Exit logic - simplified for performance (signal reversal only)
            exit_now = False

            # Check for signal reversal exit
            if (position == 1 and signal == -1) or (position == -1 and signal == 1):
                exit_now = True

            if exit_now:
                # Calculate PnL
                option_move = option_delta * (price - entry_price)
                if position == 1:  # Long
                    pnl = option_move * option_qty * option_price_per_unit
                else:  # Short
                    pnl = -option_move * option_qty * option_price_per_unit

                current_equity += pnl - fee_per_trade

                # Reset position
                position = 0
                entry_price = 0.0

                # Immediate re-entry if signal present
                if signal == 1:
                    position = 1
                    entry_price = price
                elif signal == -1:
                    position = -1
                    entry_price = price

        equity_curve[i] = current_equity

    if position != 0:
        last_price = prices[-1]
        option_move = option_delta * (last_price - entry_price)
        if position == 1:
            pnl = option_move * option_qty * option_price_per_unit
        else:
            pnl = -option_move * option_qty * option_price_per_unit
        current_equity += pnl - fee_per_trade

    equity_curve = np.append(equity_curve, current_equity)

    return equity_curve

class BacktestEngine:
    def __init__(self, data, strategy, initial_cash=100000, option_delta=0.5, lots=2, option_price_per_unit=1, fee_per_trade=0.0):
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.option_delta = option_delta
        self.lots = lots
        self.option_price_per_unit = option_price_per_unit
        self.fee_per_trade = fee_per_trade

    def run(self):
        """
        Run the backtest using vectorized operations for better performance.
        Returns: dict with equity_curve, trade_log, indicators
        """
        # Generate signals once
        df = self.strategy.generate_signals(self.data)
        
        # Dynamic indicator support based on strategy metadata
        indicator_cfg = []
        if hasattr(self.strategy, 'indicator_config'):
            indicator_cfg = self.strategy.indicator_config() or []
        indicator_cols = [cfg.get('column') for cfg in indicator_cfg if cfg.get('column')]
        
        # Extract arrays for vectorized processing
        signals = df['signal'].values
        prices = df['close'].values
        timestamps = df['timestamp'].values
        option_qty = self.lots * 75
        
        # Use vectorized backtest if signals are simple (just entry signals)
        if self._can_use_fast_vectorized(df):
            equity_curve_values = _vectorized_backtest_core(
                signals,
                prices,
                self.option_delta,
                option_qty,
                self.option_price_per_unit,
                self.fee_per_trade,
                self.initial_cash,
            )

            # Build results
            if len(equity_curve_values) > len(timestamps):
                ts = np.append(timestamps, timestamps[-1])
            else:
                ts = timestamps
            equity_curve_df = pd.DataFrame({
                'timestamp': ts,
                'equity': equity_curve_values
            })
            
            # Generate trade log from signals for compatibility
            trade_log = self._generate_trade_log_from_signals(df, equity_curve_values)
            
        else:
            # Fall back to original logic for complex strategies
            equity_curve_df, trade_log = self._run_traditional_backtest(df, option_qty, indicator_cols)
        
        result = {
            'equity_curve': equity_curve_df,
            'trade_log': trade_log,
        }
        
        # Include all configured indicators
        if indicator_cols:
            result['indicators'] = df[['timestamp'] + indicator_cols]
        
        return result
    
    def _can_use_fast_vectorized(self, df):
        """Check if we can use the fast vectorized approach."""
        # For now, only use fast approach for simple signal-based strategies
        # More complex exit logic requires the traditional approach
        return hasattr(self.strategy, '_use_fast_vectorized') and self.strategy._use_fast_vectorized
    
    def _generate_trade_log_from_signals(self, df, equity_curve):
        """Generate trade log from signal changes for fast vectorized approach."""
        signals = df['signal'].values
        prices = df['close'].values
        timestamps = df['timestamp'].values
        
        trades = []
        position = 0
        entry_price = 0
        entry_time = None

        for i in range(len(signals)):
            signal = signals[i]
            
            if position == 0 and signal != 0:
                # Entry
                position = signal
                entry_price = prices[i]
                entry_time = timestamps[i]
            elif position != 0 and (signal == -position or i == len(signals) - 1):
                # Exit
                exit_price = prices[i]
                exit_time = timestamps[i]

                # Calculate PnL
                option_move = self.option_delta * (exit_price - entry_price)
                option_qty = self.lots * 75

                if position == 1:  # Long
                    pnl = option_move * option_qty * self.option_price_per_unit
                    direction = 'long'
                else:  # Short
                    pnl = -option_move * option_qty * self.option_price_per_unit
                    direction = 'short'

                pnl -= self.fee_per_trade

                trades.append({
                    'entry_time': entry_time,
                    'entry_price': entry_price,
                    'direction': direction,
                    'exit_time': exit_time,
                    'exit_price': exit_price,
                    'pnl': pnl,
                    'normal_pnl': exit_price - entry_price if position == 1 else entry_price - exit_price,
                    'exit_reason': 'Signal Reversal' if i < len(signals) - 1 else 'End of Data'
                })
                
                position = 0
                if i < len(signals) - 1 and signal != 0:
                    # Immediate re-entry
                    position = signal
                    entry_price = exit_price
                    entry_time = exit_time
        
        return pd.DataFrame(trades)
    
    def _run_traditional_backtest(self, df, option_qty, indicator_cols):
        """Traditional row-by-row backtest for complex strategies."""
        exit_col = indicator_cols[0] if indicator_cols else None
        equity = self.initial_cash
        position = None  # None, 'long', 'short'
        entry_price = 0
        entry_idx = None
        trade_log = []
        equity_curve = []
        last_signal = 0

        for idx, row in df.iterrows():
            signal = row['signal']
            price = row['close']
            ref = row.get(exit_col) if exit_col else None

            # Entry logic
            if position is None:
                if signal == 1:
                    position = 'long'
                    entry_price = price
                    entry_idx = idx
                    trade = {
                        'entry_time': row['timestamp'],
                        'entry_price': price,
                        'direction': 'long',
                        'exit_time': None,
                        'exit_price': None,
                        'pnl': None,
                        'exit_reason': None
                    }
                elif signal == -1:
                    position = 'short'
                    entry_price = price
                    entry_idx = idx
                    trade = {
                        'entry_time': row['timestamp'],
                        'entry_price': price,
                        'direction': 'short',
                        'exit_time': None,
                        'exit_price': None,
                        'pnl': None,
                        'exit_reason': None
                    }
                else:
                    trade = None
            else:
                # Use strategy-specific exit logic
                exit_now, exit_reason = self.strategy.should_exit(position, row, entry_price)
                if exit_now:
                    trade['exit_time'] = row['timestamp']
                    trade['exit_price'] = price
                    # Simulate ATM option price movement: option_delta x index movement
                    option_move = self.option_delta * (price - entry_price)
                    if position == 'long':
                        trade['normal_pnl'] = price - entry_price
                        trade['pnl'] = option_move * option_qty * self.option_price_per_unit
                    else:
                        # For short (PE), reverse the sign
                        trade['normal_pnl'] = entry_price - price
                        trade['pnl'] = -option_move * option_qty * self.option_price_per_unit
                    trade['exit_reason'] = exit_reason
                    trade['pnl'] -= self.fee_per_trade
                    trade_log.append(trade)
                    equity += trade['pnl']
                    position = None
                    entry_price = 0
                    entry_idx = None
                    trade = None

                    # Immediate re-entry if exit was indicator-based and signal flips
                    if exit_reason.lower().endswith('exit'):
                        if position is None and signal != 0:
                            if signal == 1:
                                position = 'long'
                                entry_price = price
                                entry_idx = idx
                                trade = {
                                    'entry_time': row['timestamp'],
                                    'entry_price': price,
                                    'direction': 'long',
                                    'exit_time': None,
                                    'exit_price': None,
                                    'pnl': None,
                                    'exit_reason': None
                                }
                            elif signal == -1:
                                position = 'short'
                                entry_price = price
                                entry_idx = idx
                                trade = {
                                    'entry_time': row['timestamp'],
                                    'entry_price': price,
                                    'direction': 'short',
                                    'exit_time': None,
                                    'exit_price': None,
                                    'pnl': None,
                                    'exit_reason': None
                                }

            equity_curve.append(equity)

        # If trade is still open at the end, close at last price
        if position is not None and trade is not None:
            last_row = df.iloc[-1]
            trade['exit_time'] = last_row['timestamp']
            trade['exit_price'] = last_row['close']
            option_move = self.option_delta * (last_row['close'] - entry_price)
            if position == 'long':
                trade['normal_pnl'] = last_row['close'] - entry_price
                trade['pnl'] = option_move * option_qty * self.option_price_per_unit
            else:
                trade['normal_pnl'] = entry_price - last_row['close']
                trade['pnl'] = -option_move * option_qty * self.option_price_per_unit
            trade['exit_reason'] = 'End of Data'
            trade['pnl'] -= self.fee_per_trade
            trade_log.append(trade)
            equity += trade['pnl']
            equity_curve.append(equity)

        # Build equity curve DataFrame
        equity_curve_df = pd.DataFrame({
            'timestamp': df['timestamp'],
            'equity': equity_curve[:len(df)]
        })

        trade_log_df = pd.DataFrame(trade_log)
        
        return equity_curve_df, trade_log_df
