from backtester.strategy_base import StrategyBase
import pandas as pd

class MeanReversionConfirmedScalper(StrategyBase):
    """
    A mean reversion scalping strategy that uses Bollinger Bands and a Stochastic Oscillator for confirmation.
    """
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        # Bollinger Bands parameters
        self.bb_length = int(p.get('bb_length', 5))
        self.bb_std = float(p.get('bb_std', 2.0))
        self.band_proximity = float(p.get('band_proximity', 0.0002))

        # Stochastic Oscillator parameters
        self.stoch_k = int(p.get('stoch_k', 3))
        self.stoch_d = int(p.get('stoch_d', 1))
        self.stoch_smooth_k = int(p.get('stoch_smooth_k', 1))
        self.stoch_overbought = int(p.get('stoch_overbought', 80))
        self.stoch_oversold = int(p.get('stoch_oversold', 20))

        # ATR parameters
        self.atr_period = int(p.get('atr_period', 14))
        self.atr_multiplier = float(p.get('atr_multiplier', 1.5))

        # Profit/Loss parameters
        self.daily_profit_target = float(p.get('daily_profit_target', 40))

        # State variables
        self.daily_pnl = 0
        self.last_trade_date = None

    def indicator_config(self):
        return [
            {"column": f"BBL_{self.bb_length}_{self.bb_std}".replace('.', '_'), "label": f"BB-Lower", "plot": True, "color": "red"},
            {"column": f"BBM_{self.bb_length}_{self.bb_std}".replace('.', '_'), "label": f"BB-Mid", "plot": True, "color": "orange"},
            {"column": f"BBU_{self.bb_length}_{self.bb_std}".replace('.', '_'), "label": f"BB-Upper", "plot": True, "color": "green"},
            {"column": "stoch_k", "label": "Stoch %K", "plot": False},
            {"column": "stoch_d", "label": "Stoch %D", "plot": False},
        ]

    def generate_signals(self, data):
        df = data.copy()

        # Bollinger Bands
        close = df['close']
        ma = close.rolling(self.bb_length).mean()
        stdev = close.rolling(self.bb_length).std()
        df[f'BBU_{self.bb_length}_{self.bb_std}'.replace('.', '_')] = ma + self.bb_std * stdev
        df[f'BBM_{self.bb_length}_{self.bb_std}'.replace('.', '_')] = ma
        df[f'BBL_{self.bb_length}_{self.bb_std}'.replace('.', '_')] = ma - self.bb_std * stdev

        # Stochastic Oscillator
        low_min = df['low'].rolling(window=self.stoch_k).min()
        high_max = df['high'].rolling(window=self.stoch_k).max()
        df['stoch_k'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['stoch_d'] = df['stoch_k'].rolling(window=self.stoch_d).mean()
        df['prev_stoch_k'] = df['stoch_k'].shift(1)

        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()

        # Entry conditions
        long_crossover = (df['stoch_k'] > self.stoch_oversold) & (df['prev_stoch_k'] <= self.stoch_oversold)
        short_crossover = (df['stoch_k'] < self.stoch_overbought) & (df['prev_stoch_k'] >= self.stoch_overbought)

        lower_band = df[f'BBL_{self.bb_length}_{self.bb_std}'.replace('.', '_')]
        upper_band = df[f'BBU_{self.bb_length}_{self.bb_std}'.replace('.', '_')]

        near_lower_band = df['close'] <= lower_band * (1 + self.band_proximity)
        near_upper_band = df['close'] >= upper_band * (1 - self.band_proximity)

        long_entry = near_lower_band & long_crossover
        short_entry = near_upper_band & short_crossover

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        trade_date = row.timestamp.date()

        # Reset daily PnL at the start of a new day
        if self.last_trade_date and self.last_trade_date != trade_date:
            self.daily_pnl = 0
        self.last_trade_date = trade_date

        # Check if daily profit target is reached
        if self.daily_pnl >= self.daily_profit_target:
            return True, 'Daily Profit Target Reached'

        # Take Profit
        mid_band = getattr(row, f'BBM_{self.bb_length}_{self.bb_std}'.replace('.', '_'))
        if position == 'long' and price >= mid_band:
            self.daily_pnl += price - entry_price
            return True, 'Take Profit'
        elif position == 'short' and price <= mid_band:
            self.daily_pnl += entry_price - price
            return True, 'Take Profit'

        # Stop Loss
        stop_loss_amount = row.atr * self.atr_multiplier
        if position == 'long' and price <= entry_price - stop_loss_amount:
            self.daily_pnl -= stop_loss_amount
            return True, 'Stop Loss'
        elif position == 'short' and price >= entry_price + stop_loss_amount:
            self.daily_pnl -= stop_loss_amount
            return True, 'Stop Loss'

        return False, ''
