from backtester.strategy_base import StrategyBase
import pandas as pd

class HybridScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.trend_ema_period = int(p.get('trend_ema_period', 50))
        self.entry_ema_period = int(p.get('entry_ema_period', 10))
        self.adx_period = int(p.get('adx_period', 14))
        self.take_profit_points = float(p.get('take_profit_points', 12))
        self.stop_loss_points = float(p.get('stop_loss_points', 6))

    def indicator_config(self):
        return [
            {"column": "trend_ema", "label": f"EMA({self.trend_ema_period})", "plot": True, "color": "purple"},
            {"column": "entry_ema", "label": f"EMA({self.entry_ema_period})", "plot": True, "color": "blue"},
            {"column": "adx", "label": f"ADX({self.adx_period})", "plot": False},
        ]

    def _calculate_adx(self, df, period):
        df['tr'] = df['high'].combine(df['close'].shift(), max) - df['low'].combine(df['close'].shift(), min)
        df['dmp'] = df['high'].diff()
        df['dmn'] = df['low'].diff()
        df['plus_dm'] = ((df['dmp'] > df['dmn']) & (df['dmp'] > 0)) * df['dmp']
        df['minus_dm'] = ((df['dmn'] > df['dmp']) & (df['dmn'] > 0)) * df['dmn']

        df['atr'] = df['tr'].rolling(window=period).mean()
        df['plus_di'] = 100 * (df['plus_dm'].rolling(window=period).mean() / df['atr'])
        df['minus_di'] = 100 * (df['minus_dm'].rolling(window=period).mean() / df['atr'])

        df['dx'] = 100 * abs(df['plus_di'] - df['minus_di']) / (df['plus_di'] + df['minus_di'])
        df['adx'] = df['dx'].rolling(window=period).mean()
        return df

    def generate_signals(self, data):
        df = data.copy()
        df['trend_ema'] = df['close'].ewm(span=self.trend_ema_period, adjust=False).mean()
        df['entry_ema'] = df['close'].ewm(span=self.entry_ema_period, adjust=False).mean()
        df = self._calculate_adx(df, self.adx_period)

        long_entry = (df['close'] > df['trend_ema']) & (df['adx'] > 20) & (df['low'] <= df['entry_ema'])
        short_entry = (df['close'] < df['trend_ema']) & (df['adx'] > 20) & (df['high'] >= df['entry_ema'])

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
