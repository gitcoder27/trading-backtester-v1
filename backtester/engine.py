"""
engine_refactored.py
Core backtesting engine using a Numba-accelerated loop for performance.
"""
import pandas as pd
import numpy as np
from numba import njit

class PnLCalculator:
    """Base class for PnL calculators."""
    def calculate_pnl(self, entry_price, exit_price, direction):
        pnl = np.zeros_like(entry_price, dtype=float)
        long_mask = direction == 'long'
        short_mask = direction == 'short'
        pnl[long_mask] = exit_price[long_mask] - entry_price[long_mask]
        pnl[short_mask] = entry_price[short_mask] - exit_price[short_mask]
        return pnl

class OptionsPnLCalculator(PnLCalculator):
    """Calculates PnL for options trades."""
    def __init__(self, option_delta=0.5, lots=2, option_price_per_unit=1):
        self.option_delta = option_delta
        self.lots = lots
        self.option_price_per_unit = option_price_per_unit
        self.option_qty = self.lots * 75

    def calculate_pnl(self, entry_price, exit_price, direction):
        price_change = exit_price - entry_price
        option_move = self.option_delta * price_change

        pnl = np.zeros_like(price_change, dtype=float)
        long_mask = direction == 'long'
        short_mask = direction == 'short'

        pnl[long_mask] = option_move[long_mask] * self.option_qty * self.option_price_per_unit
        pnl[short_mask] = -option_move[short_mask] * self.option_qty * self.option_price_per_unit

        normal_pnl = super().calculate_pnl(entry_price, exit_price, direction)
        return pnl, normal_pnl

@njit
def _numba_core_v2(
    close: np.ndarray,
    signals: np.ndarray,
    ema: np.ndarray,
    timestamps: np.ndarray,
    profit_target: float,
    stop_loss: float
):
    n = len(close)
    trades = []
    position = 0
    entry_price = 0.0
    entry_time = np.int64(0)

    for i in range(n):
        # Check for exit
        if position != 0:
            exit_condition = False
            if position == 1: # Long
                if (close[i] >= entry_price + profit_target or
                    close[i] <= entry_price - stop_loss or
                    close[i] < ema[i]):
                    exit_condition = True
            elif position == -1: # Short
                if (close[i] <= entry_price - profit_target or
                    close[i] >= entry_price + stop_loss or
                    close[i] > ema[i]):
                    exit_condition = True

            if exit_condition:
                trades.append((entry_time, entry_price, timestamps[i], close[i], position))
                position = 0

        # Check for entry
        if position == 0:
            if signals[i] == 1:
                position = 1
                entry_price = close[i]
                entry_time = timestamps[i]
            elif signals[i] == -1:
                position = -1
                entry_price = close[i]
                entry_time = timestamps[i]

    # Handle open position at the end of the data
    if position != 0:
        trades.append((entry_time, entry_price, timestamps[n-1], close[n-1], position))

    return trades


class BacktestEngineRefactored:
    def __init__(self, data, strategy, initial_cash=100000, pnl_calculator=None):
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.pnl_calculator = pnl_calculator or OptionsPnLCalculator()

    def run(self):
        df = self.strategy.generate_signals(self.data.copy())
        params = self.strategy.params
        profit_target = params.get('profit_target', 20)
        stop_loss = params.get('stop_loss', 15)

        # Prepare numpy arrays
        close_np = df['close'].to_numpy(dtype=np.float64)
        signals_np = df['signal'].to_numpy(dtype=np.int64)
        ema_np = df['ema'].to_numpy(dtype=np.float64)
        timestamps_np = df['timestamp'].astype(np.int64).to_numpy()

        trade_list = _numba_core_v2(close_np, signals_np, ema_np, timestamps_np, profit_target, stop_loss)

        if not trade_list:
            return {
                'equity_curve': pd.DataFrame({'timestamp': df['timestamp'], 'equity': self.initial_cash}),
                'trade_log': pd.DataFrame(),
                'indicators': df
            }

        trade_log = pd.DataFrame(
            trade_list,
            columns=['entry_time', 'entry_price', 'exit_time', 'exit_price', 'direction_num']
        )
        trade_log['direction'] = np.where(trade_log['direction_num'] == 1, 'long', 'short')
        trade_log['entry_time'] = pd.to_datetime(trade_log['entry_time'])
        trade_log['exit_time'] = pd.to_datetime(trade_log['exit_time'])

        pnl, normal_pnl = self.pnl_calculator.calculate_pnl(
            trade_log['entry_price'].values,
            trade_log['exit_price'].values,
            trade_log['direction'].values
        )
        trade_log['pnl'] = pnl
        trade_log['normal_pnl'] = normal_pnl

        # Build equity curve
        trade_log = trade_log.sort_values(by='exit_time').reset_index(drop=True)
        pnl_by_time = trade_log.groupby('exit_time')['pnl'].sum()

        # Ensure timezones match before merging
        if df['timestamp'].dt.tz is not None:
            pnl_by_time = pnl_by_time.tz_localize('UTC').tz_convert(df['timestamp'].dt.tz)

        df = df.merge(pnl_by_time.rename('pnl'), left_on='timestamp', right_index=True, how='left')
        df['pnl'].fillna(0, inplace=True)
        df['equity'] = self.initial_cash + df['pnl'].cumsum()

        equity_curve = df[['timestamp', 'equity']].copy()

        return {
            'equity_curve': equity_curve,
            'trade_log': trade_log,
            'indicators': df
        }
