"""
engine.py
Core backtesting engine for running trading strategies on historical data.
"""

import pandas as pd

class BacktestEngine:
    def __init__(self, data, strategy, initial_cash=100000):
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash

    def run(self):
        """
        Run the backtest using the provided strategy and data.
        Returns: dict with equity_curve, trade_log, indicators
        """
        df = self.strategy.generate_signals(self.data)
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
            ema = row['ema']

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
                # Exit logic for long
                if position == 'long':
                    # Condition 1: EMA exit
                    if price < ema:
                        exit_reason = 'EMA exit'
                        exit_now = True
                    # Condition 2: Point target
                    elif price >= entry_price + 30:
                        exit_reason = 'Target'
                        exit_now = True
                    # Condition 3: Stop loss
                    elif price <= entry_price - 20:
                        exit_reason = 'Stop Loss'
                        exit_now = True
                    else:
                        exit_now = False

                    if exit_now:
                        trade['exit_time'] = row['timestamp']
                        trade['exit_price'] = price
                        trade['pnl'] = price - entry_price
                        trade['exit_reason'] = exit_reason
                        trade_log.append(trade)
                        equity += trade['pnl']
                        position = None
                        entry_price = 0
                        entry_idx = None
                        trade = None

                        # Immediate re-entry if EMA exit and signal flips
                        if exit_reason == 'EMA exit':
                            if price < ema and signal == -1:
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
                # Exit logic for short
                elif position == 'short':
                    # Condition 1: EMA exit
                    if price > ema:
                        exit_reason = 'EMA exit'
                        exit_now = True
                    # Condition 2: Point target
                    elif price <= entry_price - 30:
                        exit_reason = 'Target'
                        exit_now = True
                    # Condition 3: Stop loss
                    elif price >= entry_price + 20:
                        exit_reason = 'Stop Loss'
                        exit_now = True
                    else:
                        exit_now = False

                    if exit_now:
                        trade['exit_time'] = row['timestamp']
                        trade['exit_price'] = price
                        trade['pnl'] = entry_price - price
                        trade['exit_reason'] = exit_reason
                        trade_log.append(trade)
                        equity += trade['pnl']
                        position = None
                        entry_price = 0
                        entry_idx = None
                        trade = None

                        # Immediate re-entry if EMA exit and signal flips
                        if exit_reason == 'EMA exit':
                            if price > ema and signal == 1:
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
            equity_curve.append(equity)

        # If trade is still open at the end, close at last price
        if position is not None and trade is not None:
            last_row = df.iloc[-1]
            trade['exit_time'] = last_row['timestamp']
            trade['exit_price'] = last_row['close']
            if position == 'long':
                trade['pnl'] = last_row['close'] - entry_price
            else:
                trade['pnl'] = entry_price - last_row['close']
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

        return {
            'equity_curve': equity_curve_df,
            'trade_log': trade_log_df,
            'indicators': df[['timestamp', 'ema']]
        }