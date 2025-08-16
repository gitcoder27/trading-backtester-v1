from backtester.strategy_base import StrategyBase
import pandas as pd
import datetime

class RSIMiddayReversionScalper(StrategyBase):
    """RSI-based mean reversion scalping strategy with a midday fallback entry.
    Goes long after oversold RSI recovers above 30 and short after overbought RSI
    drops below 70. Exits when RSI reaches the neutral 50 level or an ATR-based
    stop is hit. Ensures at least one trade per trading day by forcing an entry
    after 13:00 if no signal occurred."""

    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.rsi_period = int(p.get('rsi_period', 14))
        self.atr_period = int(p.get('atr_period', 14))
        self.stop_atr = float(p.get('stop_atr', 5.0))
        self.target_atr = float(p.get('target_atr', 1.0))

    def indicator_config(self):
        return [
            {"column": "rsi", "label": "RSI", "plot": True, "panel": 2, "color": "purple"},
        ]

    def _compute_rsi(self, series, period):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ma_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        return 100 - (100 / (1 + ma_up / ma_down))

    def generate_signals(self, data):
        df = data.copy()
        df['rsi'] = self._compute_rsi(df['close'], self.rsi_period)

        # ATR for stop loss
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()

        df['signal'] = 0
        long_entry = (df['rsi'].shift(1) < 30) & (df['rsi'] >= 30)
        short_entry = (df['rsi'].shift(1) > 70) & (df['rsi'] <= 70)
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        # Ensure at least one trade per day with midday forced entry
        df['date'] = df['timestamp'].dt.date
        for date, group in df.groupby('date'):
            if (group['signal'] != 0).any():
                continue
            midday = group[group['timestamp'].dt.time >= datetime.time(13,0)]
            if not midday.empty:
                idx = midday.index[0]
            else:
                idx = group.index[0]
            df.loc[idx, 'signal'] = 1 if group.loc[idx, 'rsi'] > 50 else -1
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        atr = row.atr
        if position == 'long':
            if row.rsi >= 50 or price >= entry_price + self.target_atr * atr:
                return True, 'Target'
            if price <= entry_price - self.stop_atr * atr:
                return True, 'Stop Loss'
        elif position == 'short':
            if row.rsi <= 50 or price <= entry_price - self.target_atr * atr:
                return True, 'Target'
            if price >= entry_price + self.stop_atr * atr:
                return True, 'Stop Loss'
        return False, ''
