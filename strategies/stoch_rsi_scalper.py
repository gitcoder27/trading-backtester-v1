from backtester.strategy_base import StrategyBase
import pandas as pd

class StochRSIScalperStrategy(StrategyBase):
    """Mean-reversion scalper using Stochastic RSI with trend filter."""
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.rsi_period = int(p.get('rsi_period', 14))
        self.stoch_period = int(p.get('stoch_period', 14))
        self.k_period = int(p.get('k_period', 3))
        self.d_period = int(p.get('d_period', 3))
        self.ema_trend = int(p.get('ema_trend', 100))
        self.atr_period = int(p.get('atr_period', 14))
        self.tp_mult = float(p.get('tp_mult', 0.6))
        self.sl_mult = float(p.get('sl_mult', 1.0))

    def indicator_config(self):
        return [
            {"column": "%K", "label": "%K", "plot": True, "color": "blue", "panel": 2},
            {"column": "%D", "label": "%D", "plot": True, "color": "orange", "panel": 2},
        ]

    def compute_rsi(self, series, period):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ma_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    def compute_stoch_rsi(self, rsi, period, k_period, d_period):
        min_rsi = rsi.rolling(period).min()
        max_rsi = rsi.rolling(period).max()
        stoch_rsi = (rsi - min_rsi) / (max_rsi - min_rsi)
        k = stoch_rsi.rolling(k_period).mean()
        d = k.rolling(d_period).mean()
        return k, d

    def generate_signals(self, data):
        df = data.copy()
        close = df['close']

        df['ema'] = close.ewm(span=self.ema_trend, adjust=False).mean()
        df['rsi'] = self.compute_rsi(close, self.rsi_period)
        k, d = self.compute_stoch_rsi(df['rsi'], self.stoch_period, self.k_period, self.d_period)
        df['%K'] = k
        df['%D'] = d

        # ATR for exits
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()

        df['signal'] = 0
        k_prev = df['%K'].shift(1)
        d_prev = df['%D'].shift(1)

        long_cond = (
            (k_prev < d_prev) & (df['%K'] > df['%D']) &
            (df['%K'] < 0.2) & (df['rsi'] < 42) & (df['close'] > df['ema'])
        )
        short_cond = (
            (k_prev > d_prev) & (df['%K'] < df['%D']) &
            (df['%K'] > 0.8) & (df['rsi'] > 58) & (df['close'] < df['ema'])
        )
        df.loc[long_cond, 'signal'] = 1
        df.loc[short_cond, 'signal'] = -1

        # Ensure at least one trade per day
        if 'timestamp' in df.columns:
            df['date'] = pd.to_datetime(df['timestamp']).dt.date
            for date, grp in df.groupby('date'):
                if (grp['signal'] != 0).any():
                    continue
                mid_idx = grp.index[len(grp)//2]
                direction = 1 if grp.loc[mid_idx, 'close'] > grp.loc[mid_idx, 'ema'] else -1
                df.at[mid_idx, 'signal'] = direction
            df.drop(columns=['date'], inplace=True)
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        atr = row.atr if not pd.isna(row.atr) else 0
        tp = self.tp_mult * atr
        sl = self.sl_mult * atr
        if position == 'long':
            if price - entry_price >= tp:
                return True, 'Take Profit'
            if entry_price - price >= sl:
                return True, 'Stop Loss'
            if row['%K'] < row['%D']:
                return True, 'Stoch Exit'
        elif position == 'short':
            if entry_price - price >= tp:
                return True, 'Take Profit'
            if price - entry_price >= sl:
                return True, 'Stop Loss'
            if row['%K'] > row['%D']:
                return True, 'Stoch Exit'
        return False, ''
