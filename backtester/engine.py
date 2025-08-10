"""
engine.py
Core backtesting engine for running trading strategies on historical data.
"""

import pandas as pd

class BacktestEngine:
    def __init__(self, data, strategy, initial_cash=100000, option_delta=0.5, lots=2, option_price_per_unit=1):
        self.data = data
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.option_delta = option_delta
        self.lots = lots
        self.option_price_per_unit = option_price_per_unit

    def run(self):
        """
        Run the backtest using the provided strategy and data.
        Returns: dict with equity_curve, trade_log, indicators
        """
        df = self.strategy.generate_signals(self.data)
        # Dynamic indicator support based on strategy metadata
        indicator_cfg = []
        if hasattr(self.strategy, 'indicator_config'):
            indicator_cfg = self.strategy.indicator_config() or []
        indicator_cols = [cfg.get('column') for cfg in indicator_cfg if cfg.get('column')]
        exit_col = indicator_cols[0] if indicator_cols else None
        equity = self.initial_cash
        position = None  # None, 'long', 'short'
        entry_price = 0
        entry_idx = None
        trade_log = []
        equity_curve = []
        last_signal = 0
        option_qty = self.lots * 75

        for row in df.itertuples(index=True):
            idx = row.Index
            signal = row.signal
            price = row.close
            ref = getattr(row, exit_col) if exit_col and hasattr(row, exit_col) else None

            # Entry logic
            if position is None:
                if signal == 1:
                    position = 'long'
                    entry_price = price
                    entry_idx = idx
                    trade = {
                        'entry_time': row.timestamp,
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
                        'entry_time': row.timestamp,
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
                    trade['exit_time'] = row.timestamp
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
                    trade_log.append(trade)
                    equity += trade['pnl']
                    position = None
                    entry_price = 0
                    entry_idx = None
                    trade = None

                    # Immediate re-entry if exit was indicator-based and signal flips
                    # (Optional: can be customized per strategy)
                    if exit_reason.lower().endswith('exit'):
                        if position is None and signal != 0:
                            if signal == 1:
                                position = 'long'
                                entry_price = price
                                entry_idx = idx
                                trade = {
                                    'entry_time': row.timestamp,
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
                                    'entry_time': row.timestamp,
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
            trade['exit_time'] = last_row.timestamp
            trade['exit_price'] = last_row.close
            option_move = self.option_delta * (last_row.close - entry_price)
            if position == 'long':
                trade['normal_pnl'] = last_row.close - entry_price
                trade['pnl'] = option_move * option_qty * self.option_price_per_unit
            else:
                trade['normal_pnl'] = entry_price - last_row.close
                trade['pnl'] = -option_move * option_qty * self.option_price_per_unit
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

        result = {
            'equity_curve': equity_curve_df,
            'trade_log': trade_log_df,
        }
        # Include all configured indicators
        if indicator_cols:
            result['indicators'] = df[['timestamp'] + indicator_cols]
        return result