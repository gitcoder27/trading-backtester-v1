"""
This script implements the IntradayEmaTradeStrategy, a strategy based on an EMA crossover,
a confirmation with a red candle, and an entry on the break of the high of that red candle.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase

class IntradayEmaTradeStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = 21
        self.risk_reward_ratio = 1.5
        self.processed_data = None
        self.active_trade_sl = None
        self.active_trade_tp = None

    def generate_signals(self, data):
        """
        Generates trading signals based on the strategy logic.
        """
        df = data.copy()
        df['ema'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        df['signal'] = 0
        df['stop_loss_price'] = pd.NA
        df['take_profit_price'] = pd.NA
        df['is_green'] = df['close'] > df['open']
        df['is_red'] = df['close'] < df['open']

        state = 'LOOKING_FOR_ALERT'
        trade_type = None
        alert_candle_index = -1
        signal_candle_index = -1

        for i in range(1, len(df)):
            current_row = df.iloc[i]

            if state in ['WAITING_FOR_SIGNAL', 'WAITING_FOR_ENTRY']:
                if trade_type == 'long' and current_row['close'] < current_row['ema']:
                    state = 'LOOKING_FOR_ALERT'
                elif trade_type == 'short' and current_row['close'] > current_row['ema']:
                    state = 'LOOKING_FOR_ALERT'

            if state == 'LOOKING_FOR_ALERT':
                is_long_alert = current_row['is_green'] and current_row['open'] < current_row['ema'] and current_row['close'] > current_row['ema']
                is_short_alert = current_row['is_red'] and current_row['open'] > current_row['ema'] and current_row['close'] < current_row['ema']

                if is_long_alert:
                    state, trade_type, alert_candle_index = 'WAITING_FOR_SIGNAL', 'long', i
                elif is_short_alert:
                    state, trade_type, alert_candle_index = 'WAITING_FOR_SIGNAL', 'short', i

            elif state == 'WAITING_FOR_SIGNAL':
                if i > alert_candle_index + 3:
                    state = 'LOOKING_FOR_ALERT'
                    continue

                if trade_type == 'long' and current_row['is_red']:
                    state, signal_candle_index = 'WAITING_FOR_ENTRY', i
                elif trade_type == 'short' and current_row['is_green']:
                    state, signal_candle_index = 'WAITING_FOR_ENTRY', i

            elif state == 'WAITING_FOR_ENTRY':
                if i == signal_candle_index + 1:
                    signal_candle_row = df.iloc[signal_candle_index]

                    if trade_type == 'long' and current_row['close'] > signal_candle_row['high']:
                        df.iloc[i, df.columns.get_loc('signal')] = 1
                        sl_price = signal_candle_row['low']
                        risk = current_row['close'] - sl_price
                        tp_price = current_row['close'] + risk * self.risk_reward_ratio
                        df.iloc[i, df.columns.get_loc('stop_loss_price')] = sl_price
                        df.iloc[i, df.columns.get_loc('take_profit_price')] = tp_price

                    elif trade_type == 'short' and current_row['close'] < signal_candle_row['low']:
                        df.iloc[i, df.columns.get_loc('signal')] = -1
                        sl_price = signal_candle_row['high']
                        risk = sl_price - current_row['close']
                        tp_price = current_row['close'] - risk * self.risk_reward_ratio
                        df.iloc[i, df.columns.get_loc('stop_loss_price')] = sl_price
                        df.iloc[i, df.columns.get_loc('take_profit_price')] = tp_price

                state = 'LOOKING_FOR_ALERT'

        self.processed_data = df
        return df

    def should_exit(self, position, row, entry_price):
        """
        Determines if an open position should be exited based on SL/TP.
        """
        if position is None:
            return False, ''

        # Set SL/TP for the active trade if not already set
        if self.active_trade_sl is None:
            possible_entries = self.processed_data[
                (self.processed_data['close'] == entry_price) &
                (self.processed_data['signal'] != 0) &
                (self.processed_data['timestamp'] <= row.timestamp)
            ]
            if not possible_entries.empty:
                entry_row = possible_entries.iloc[-1]
                self.active_trade_sl = entry_row['stop_loss_price']
                self.active_trade_tp = entry_row['take_profit_price']
            else:
                return False, '' # Should not happen in a live trade

        price = row.close
        if position == 'long':
            if price <= self.active_trade_sl:
                self.active_trade_sl, self.active_trade_tp = None, None
                return True, 'Stop Loss'
            if price >= self.active_trade_tp:
                self.active_trade_sl, self.active_trade_tp = None, None
                return True, 'Take Profit'
        elif position == 'short':
            if price >= self.active_trade_sl:
                self.active_trade_sl, self.active_trade_tp = None, None
                return True, 'Stop Loss'
            if price <= self.active_trade_tp:
                self.active_trade_sl, self.active_trade_tp = None, None
                return True, 'Take Profit'

        return False, ''
