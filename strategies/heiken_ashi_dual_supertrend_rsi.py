from backtester.strategy_base import StrategyBase
import pandas as pd


class HeikenAshiDualSupertrendRSIStrategy(StrategyBase):
    """
    Strategy using Heikin Ashi candles, two Supertrends and RSI.

    Long entry: both Supertrends turn up and RSI < 50.
    Short entry: both Supertrends turn down and RSI > 50.
    Exits use fixed stop loss and take profit.
    """

    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.rsi_period = int(p.get('rsi_period', 70))
        self.stop_loss_points = float(p.get('stop_loss_points', 10))
        self.take_profit_points = float(p.get('take_profit_points', 20))

    def indicator_config(self):
        return [
            {"column": "st1", "label": "Supertrend 0.8", "plot": True, "color": "green"},
            {"column": "st2", "label": "Supertrend 1.6", "plot": True, "color": "red"},
            {
                "column": "rsi",
                "label": f"RSI({self.rsi_period})",
                "plot": True,
                "color": "blue",
                "panel": 2,
            },
        ]

    @staticmethod
    def compute_rsi(series, period):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ma_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    @staticmethod
    def heiken_ashi(df):
        ha = pd.DataFrame(index=df.index)
        ha['ha_close'] = (df['open'] + df['high'] + df['low'] + df['close']) / 4
        ha_open = [(df['open'].iloc[0] + df['close'].iloc[0]) / 2]
        for i in range(1, len(df)):
            ha_open.append((ha_open[i-1] + ha['ha_close'].iloc[i-1]) / 2)
        ha['ha_open'] = ha_open
        ha['ha_high'] = ha[['ha_open', 'ha_close']].join(df['high']).max(axis=1)
        ha['ha_low'] = ha[['ha_open', 'ha_close']].join(df['low']).min(axis=1)
        return ha

    @staticmethod
    def compute_supertrend(ha_df, multiplier):
        hl2 = (ha_df['ha_high'] + ha_df['ha_low']) / 2
        atr = ha_df['ha_high'] - ha_df['ha_low']
        upperband = hl2 + multiplier * atr
        lowerband = hl2 - multiplier * atr
        st = pd.Series(index=ha_df.index, dtype='float64')
        direction = pd.Series(index=ha_df.index, dtype='int64')
        in_uptrend = True
        for i in range(len(ha_df)):
            if i == 0:
                st.iloc[i] = lowerband.iloc[i]
                direction.iloc[i] = 1
                continue
            if ha_df['ha_close'].iloc[i] > upperband.iloc[i-1]:
                in_uptrend = True
            elif ha_df['ha_close'].iloc[i] < lowerband.iloc[i-1]:
                in_uptrend = False
            if in_uptrend:
                if lowerband.iloc[i] < lowerband.iloc[i-1]:
                    lowerband.iloc[i] = lowerband.iloc[i-1]
                st.iloc[i] = lowerband.iloc[i]
                direction.iloc[i] = 1
            else:
                if upperband.iloc[i] > upperband.iloc[i-1]:
                    upperband.iloc[i] = upperband.iloc[i-1]
                st.iloc[i] = upperband.iloc[i]
                direction.iloc[i] = -1
        return st, direction

    def generate_signals(self, data):
        df = data.copy()
        ha = self.heiken_ashi(df)
        df = df.join(ha)
        df['st1'], df['st1_dir'] = self.compute_supertrend(df, 0.8)
        df['st2'], df['st2_dir'] = self.compute_supertrend(df, 1.6)
        df['rsi'] = self.compute_rsi(df['close'], self.rsi_period)
        df['signal'] = 0
        for i in range(1, len(df)):
            long_cond = (
                df['st1_dir'].iloc[i] == 1 and df['st2_dir'].iloc[i] == 1
                and (df['st1_dir'].iloc[i-1] != 1 or df['st2_dir'].iloc[i-1] != 1)
                and df['rsi'].iloc[i] < 50
            )
            short_cond = (
                df['st1_dir'].iloc[i] == -1 and df['st2_dir'].iloc[i] == -1
                and (df['st1_dir'].iloc[i-1] != -1 or df['st2_dir'].iloc[i-1] != -1)
                and df['rsi'].iloc[i] > 50
            )
            if long_cond:
                df.iloc[i, df.columns.get_loc('signal')] = 1
            elif short_cond:
                df.iloc[i, df.columns.get_loc('signal')] = -1
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        if position == 'long':
            if price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
            if price >= entry_price + self.take_profit_points:
                return True, 'Take Profit'
        elif position == 'short':
            if price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'
            if price <= entry_price - self.take_profit_points:
                return True, 'Take Profit'
        return False, ''
