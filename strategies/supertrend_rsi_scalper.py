from backtester.strategy_base import StrategyBase
import pandas as pd
import numpy as np

class SuperTrendRSIScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.st_period = int(p.get('st_period', 7))
        self.st_multiplier = float(p.get('st_multiplier', 2.0))
        self.rsi_period = int(p.get('rsi_period', 14))
        self.rsi_oversold = float(p.get('rsi_oversold', 45))
        self.rsi_overbought = float(p.get('rsi_overbought', 55))
        self.stop_loss_points = float(p.get('stop_loss_points', 10))

    def _calculate_atr(self, data, period):
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.ewm(alpha=1/period, adjust=False).mean()
        return atr

    def _calculate_supertrend(self, data):
        atr = self._calculate_atr(data, self.st_period)
        hl2 = (data['high'] + data['low']) / 2
        upper_band = hl2 + (self.st_multiplier * atr)
        lower_band = hl2 - (self.st_multiplier * atr)

        supertrend = pd.Series(np.nan, index=data.index)
        trend = pd.Series(np.nan, index=data.index)

        for i in range(1, len(data)):
            if data['close'].iloc[i] > upper_band.iloc[i-1]:
                trend.iloc[i] = 1
            elif data['close'].iloc[i] < lower_band.iloc[i-1]:
                trend.iloc[i] = -1
            else:
                trend.iloc[i] = trend.iloc[i-1]

            if trend.iloc[i] == 1:
                lower_band.iloc[i] = max(lower_band.iloc[i], lower_band.iloc[i-1])
            else:
                upper_band.iloc[i] = min(upper_band.iloc[i], upper_band.iloc[i-1])

        supertrend = np.where(trend == 1, lower_band, upper_band)
        return pd.Series(supertrend, index=data.index), trend

    def _calculate_rsi(self, data, period):
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi

    def generate_signals(self, data):
        df = data.copy()

        df['supertrend'], df['trend'] = self._calculate_supertrend(df)
        df['rsi'] = self._calculate_rsi(df, self.rsi_period)

        df['prev_rsi'] = df['rsi'].shift(1)

        long_entry = (df['trend'] == 1) & (df['rsi'] > self.rsi_oversold) & (df['prev_rsi'] <= self.rsi_oversold)
        short_entry = (df['trend'] == -1) & (df['rsi'] < self.rsi_overbought) & (df['prev_rsi'] >= self.rsi_overbought)

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        supertrend = row.supertrend

        if position == 'long':
            if price < supertrend:
                return True, 'SuperTrend Exit'
            elif price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
        elif position == 'short':
            if price > supertrend:
                return True, 'SuperTrend Exit'
            elif price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'

        return False, ''
