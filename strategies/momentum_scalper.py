from backtester.strategy_base import StrategyBase
import pandas as pd

class MomentumScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.ema_long_period = int(p.get('ema_long_period', 100))
        self.macd_fast_period = int(p.get('macd_fast_period', 5))
        self.macd_slow_period = int(p.get('macd_slow_period', 13))
        self.macd_signal_period = int(p.get('macd_signal_period', 3))
        self.take_profit_points = float(p.get('take_profit_points', 20))
        self.stop_loss_points = float(p.get('stop_loss_points', 10))

    def _calculate_ema(self, data, period):
        return data['close'].ewm(span=period, adjust=False).mean()

    def _calculate_macd(self, data):
        ema_fast = self._calculate_ema(data, self.macd_fast_period)
        ema_slow = self._calculate_ema(data, self.macd_slow_period)
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.macd_signal_period, adjust=False).mean()
        return macd_line, signal_line

    def generate_signals(self, data):
        df = data.copy()

        df['ema_long'] = self._calculate_ema(df, self.ema_long_period)
        df['macd_line'], df['signal_line'] = self._calculate_macd(df)

        df['prev_macd_line'] = df['macd_line'].shift(1)
        df['prev_signal_line'] = df['signal_line'].shift(1)

        long_entry = (df['close'] > df['ema_long']) & \
                     (df['macd_line'] > df['signal_line']) & \
                     (df['prev_macd_line'] <= df['prev_signal_line'])

        short_entry = (df['close'] < df['ema_long']) & \
                      (df['macd_line'] < df['signal_line']) & \
                      (df['prev_macd_line'] >= df['prev_signal_line'])

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close

        if position == 'long':
            if price >= entry_price + self.take_profit_points:
                return True, 'Take Profit'
            elif price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
        elif position == 'short':
            if price <= entry_price - self.take_profit_points:
                return True, 'Take Profit'
            elif price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'

        return False, ''
