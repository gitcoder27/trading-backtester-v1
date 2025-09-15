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
def _vectorized_backtest_core(
    signals,
    prices,
    option_delta,
    option_qty,
    option_price_per_unit,
    fee_per_trade=0.0,
    slippage=0.0,
    initial_equity=100000.0,
):
    """Simplified vectorized backtest core using numba JIT compilation.
    Returns only equity curve for performance.

    Parameters
    ----------
    fee_per_trade : float
        Flat transaction cost deducted per round trip.
    slippage : float
        Absolute price slippage applied on both entry and exit.
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
                entry_price = price + slippage
            elif signal == -1:  # Short entry
                position = -1
                entry_price = price - slippage
        else:
            # Exit logic - simplified for performance (signal reversal only)
            exit_now = False

            # Check for signal reversal exit
            if (position == 1 and signal == -1) or (position == -1 and signal == 1):
                exit_now = True

            if exit_now:
                exit_price = price - slippage if position == 1 else price + slippage
                # Calculate PnL
                option_move = option_delta * (exit_price - entry_price)
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
                    entry_price = price + slippage
                elif signal == -1:
                    position = -1
                    entry_price = price - slippage

        equity_curve[i] = current_equity

    if position != 0:
        last_price = prices[-1]
        exit_price = last_price - slippage if position == 1 else last_price + slippage
        option_move = option_delta * (exit_price - entry_price)
        if position == 1:
            pnl = option_move * option_qty * option_price_per_unit
        else:
            pnl = -option_move * option_qty * option_price_per_unit
        current_equity += pnl - fee_per_trade

    equity_curve = np.append(equity_curve, current_equity)

    return equity_curve

class BacktestEngine:
    def __init__(
        self,
        data,
        strategy,
        initial_cash=100000,
        option_delta=0.5,
        lots=2,
        option_price_per_unit=1,
        fee_per_trade=0.0,
        slippage=0.0,
        intraday=False,
        session_close_time="15:15",
        daily_profit_target=None,
    ):
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.option_delta = option_delta
        self.lots = lots
        self.option_price_per_unit = option_price_per_unit
        self.fee_per_trade = fee_per_trade
        self.slippage = slippage
        self.intraday = intraday
        self.session_close_time = (
            pd.to_datetime(session_close_time).time() if session_close_time else None
        )
        self.daily_profit_target = daily_profit_target

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
                self.slippage,
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
            # Also include indicator configuration metadata for downstream consumers (colors, labels, panes)
            result['indicator_cfg'] = indicator_cfg
        trade_log = result['trade_log']
        if trade_log is not None and not trade_log.empty:
            tl = trade_log.copy()
            tl['trade_date'] = pd.to_datetime(tl['entry_time']).dt.date
            daily = tl.groupby('trade_date').agg(pnl=('pnl', 'sum'), trades=('pnl', 'count'))
            if self.daily_profit_target is not None:
                daily['hit_target'] = daily['pnl'] >= self.daily_profit_target
                hit_map = daily['hit_target'].to_dict()
                tl['daily_target_hit'] = tl['trade_date'].map(hit_map)
            result['trade_log'] = tl
            result['daily_summary'] = daily.reset_index().rename(columns={'trade_date': 'date'})
        else:
            result['daily_summary'] = pd.DataFrame(
                columns=['date', 'pnl', 'trades'] + ([] if self.daily_profit_target is None else ['hit_target'])
            )

        return result
    
    def _can_use_fast_vectorized(self, df):
        """Check if we can use the fast vectorized approach."""
        # For now, only use fast approach for simple signal-based strategies
        # More complex exit logic or intraday session handling requires the traditional approach
        return (
            hasattr(self.strategy, '_use_fast_vectorized')
            and self.strategy._use_fast_vectorized
            and not self.intraday
        )
    
    def _generate_trade_log_from_signals(self, df, equity_curve):
        """Generate trade log from signal changes for fast vectorized approach."""
        signals = df['signal'].values
        prices = df['close'].values
        timestamps = df['timestamp'].values
        
        trades = []
        position = 0
        entry_price = 0.0
        entry_time = None

        for i in range(len(signals)):
            signal = signals[i]

            if position == 0 and signal != 0:
                # Entry with slippage
                position = signal
                if signal == 1:
                    entry_price = prices[i] + self.slippage
                else:
                    entry_price = prices[i] - self.slippage
                entry_time = timestamps[i]
            elif position != 0 and (signal == -position or i == len(signals) - 1):
                # Exit with slippage
                if position == 1:
                    exit_price = prices[i] - self.slippage
                else:
                    exit_price = prices[i] + self.slippage
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
                    if signal == 1:
                        entry_price = prices[i] + self.slippage
                    else:
                        entry_price = prices[i] - self.slippage
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
        end_time = self.session_close_time
        current_day = None
        session_closed = False
        trade = None
        daily_points = 0.0

        for idx, row in df.iterrows():
            ts = row['timestamp']
            signal = row['signal']
            price = row['close']
            ref = row.get(exit_col) if exit_col else None

            if self.intraday:
                day = ts.date()
                if day != current_day:
                    current_day = day
                    session_closed = False
                    daily_points = 0.0
                if end_time and ts.time() >= end_time:
                    if position is not None and trade is not None:
                        trade['exit_time'] = ts
                        if position == 'long':
                            trade['exit_price'] = price - self.slippage
                            exit_price = trade['exit_price']
                        else:
                            trade['exit_price'] = price + self.slippage
                            exit_price = trade['exit_price']
                        option_move = self.option_delta * (exit_price - entry_price)
                        if position == 'long':
                            trade['normal_pnl'] = exit_price - entry_price
                            trade['pnl'] = option_move * option_qty * self.option_price_per_unit
                        else:
                            trade['normal_pnl'] = entry_price - exit_price
                            trade['pnl'] = -option_move * option_qty * self.option_price_per_unit
                        trade['pnl'] -= self.fee_per_trade
                        trade['exit_reason'] = 'Session Close'
                        trade_log.append(trade)
                        equity += trade['pnl']
                        position = None
                        entry_price = 0
                        entry_idx = None
                        trade = None
                    equity_curve.append(equity)
                    session_closed = True
                    continue

            # Entry logic
            if position is None:
                if not (self.intraday and session_closed):
                    if signal == 1:
                        position = 'long'
                        entry_price = price + self.slippage
                        entry_idx = idx
                        trade = {
                            'entry_time': ts,
                            'entry_price': entry_price,
                            'direction': 'long',
                            'exit_time': None,
                            'exit_price': None,
                            'pnl': None,
                            'exit_reason': None,
                        }
                    elif signal == -1:
                        position = 'short'
                        entry_price = price - self.slippage
                        entry_idx = idx
                        trade = {
                            'entry_time': ts,
                            'entry_price': entry_price,
                            'direction': 'short',
                            'exit_time': None,
                            'exit_price': None,
                            'pnl': None,
                            'exit_reason': None,
                        }
                    else:
                        trade = None
                else:
                    trade = None
            else:
                # Use strategy-specific exit logic
                exit_now, exit_reason = self.strategy.should_exit(position, row, entry_price)
                if exit_now:
                    trade['exit_time'] = ts
                    if position == 'long':
                        trade['exit_price'] = price - self.slippage
                        exit_price = trade['exit_price']
                    else:
                        trade['exit_price'] = price + self.slippage
                        exit_price = trade['exit_price']
                    # Simulate ATM option price movement: option_delta x index movement
                    option_move = self.option_delta * (exit_price - entry_price)
                    if position == 'long':
                        trade['normal_pnl'] = exit_price - entry_price
                        trade['pnl'] = option_move * option_qty * self.option_price_per_unit
                    else:
                        # For short (PE), reverse the sign
                        trade['normal_pnl'] = entry_price - exit_price
                        trade['pnl'] = -option_move * option_qty * self.option_price_per_unit
                    trade['pnl'] -= self.fee_per_trade
                    trade['exit_reason'] = exit_reason
                    trade_log.append(trade)
                    equity += trade['pnl']
                    daily_points += trade.get('pnl', 0)
                    if (
                        self.daily_profit_target is not None
                        and daily_points >= self.daily_profit_target
                    ):
                        session_closed = True
                    position = None
                    entry_price = 0
                    entry_idx = None
                    trade = None

                    # Immediate re-entry if exit was indicator-based and signal flips
                    if exit_reason.lower().endswith('exit'):
                        if position is None and signal != 0 and not (
                            self.intraday and session_closed
                        ):
                            if signal == 1:
                                position = 'long'
                                entry_price = price + self.slippage
                                entry_idx = idx
                                trade = {
                                    'entry_time': ts,
                                    'entry_price': entry_price,
                                    'direction': 'long',
                                    'exit_time': None,
                                    'exit_price': None,
                                    'pnl': None,
                                    'exit_reason': None,
                                }
                            elif signal == -1:
                                position = 'short'
                                entry_price = price - self.slippage
                                entry_idx = idx
                                trade = {
                                    'entry_time': ts,
                                    'entry_price': entry_price,
                                    'direction': 'short',
                                    'exit_time': None,
                                    'exit_price': None,
                                    'pnl': None,
                                    'exit_reason': None,
                                }

            equity_curve.append(equity)

        # If trade is still open at the end, close at last price
        if position is not None and trade is not None:
            last_row = df.iloc[-1]
            trade['exit_time'] = last_row['timestamp']
            if position == 'long':
                trade['exit_price'] = last_row['close'] - self.slippage
                exit_price = trade['exit_price']
            else:
                trade['exit_price'] = last_row['close'] + self.slippage
                exit_price = trade['exit_price']
            option_move = self.option_delta * (exit_price - entry_price)
            if position == 'long':
                trade['normal_pnl'] = exit_price - entry_price
                trade['pnl'] = option_move * option_qty * self.option_price_per_unit
            else:
                trade['normal_pnl'] = entry_price - exit_price
                trade['pnl'] = -option_move * option_qty * self.option_price_per_unit
            trade['pnl'] -= self.fee_per_trade
            trade['exit_reason'] = 'End of Data'
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
