from backtester.strategy_base import StrategyBase
import pandas as pd

class AwesomeScalperStrategy(StrategyBase):
    """
    A scalping strategy that combines Bollinger Bands and RSI for entry signals. test
    """
    
    @classmethod
    def get_params_config(cls):
        """Return parameter configuration for UI generation"""
        return [
            {
                "name": "bb_length",
                "label": "Bollinger Bands Period",
                "type": "number_input",
                "default": 20,
                "min": 5,
                "max": 50,
                "step": 1,
                "param_key": "bb_length",
                "description": "Period for Bollinger Bands calculation"
            },
            {
                "name": "bb_std",
                "label": "Bollinger Bands Std Dev",
                "type": "number_input",
                "default": 2.0,
                "min": 0.5,
                "max": 5.0,
                "step": 0.1,
                "param_key": "bb_std",
                "description": "Standard deviation multiplier for Bollinger Bands"
            },
            {
                "name": "rsi_period",
                "label": "RSI Period",
                "type": "number_input",
                "default": 14,
                "min": 5,
                "max": 30,
                "step": 1,
                "param_key": "rsi_period",
                "description": "Period for RSI calculation"
            },
            {
                "name": "rsi_overbought",
                "label": "RSI Overbought Level",
                "type": "number_input",
                "default": 70,
                "min": 60,
                "max": 90,
                "step": 1,
                "param_key": "rsi_overbought",
                "description": "RSI level considered overbought"
            },
            {
                "name": "rsi_oversold",
                "label": "RSI Oversold Level",
                "type": "number_input",
                "default": 30,
                "min": 10,
                "max": 40,
                "step": 1,
                "param_key": "rsi_oversold",
                "description": "RSI level considered oversold"
            },
            {
                "name": "ema_period",
                "label": "EMA Trend Period",
                "type": "number_input",
                "default": 200,
                "min": 50,
                "max": 500,
                "step": 10,
                "param_key": "ema_period",
                "description": "Period for trend-following EMA"
            },
            {
                "name": "atr_period",
                "label": "ATR Period",
                "type": "number_input",
                "default": 14,
                "min": 5,
                "max": 30,
                "step": 1,
                "param_key": "atr_period",
                "description": "Period for ATR calculation"
            },
            {
                "name": "atr_multiplier",
                "label": "ATR Stop Loss Multiplier",
                "type": "number_input",
                "default": 2.0,
                "min": 0.5,
                "max": 5.0,
                "step": 0.1,
                "param_key": "atr_multiplier",
                "description": "ATR multiplier for stop loss calculation"
            }
        ]
    
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        # Bollinger Bands parameters
        self.bb_length = int(p.get('bb_length', 20))
        self.bb_std = float(p.get('bb_std', 2.0))

        # RSI parameters
        self.rsi_period = int(p.get('rsi_period', 14))
        self.rsi_overbought = int(p.get('rsi_overbought', 70))
        self.rsi_oversold = int(p.get('rsi_oversold', 30))

        # EMA parameters
        self.ema_period = int(p.get('ema_period', 200))

        # ATR parameters
        self.atr_period = int(p.get('atr_period', 14))
        self.atr_multiplier = float(p.get('atr_multiplier', 2.0))

    def indicator_config(self):
        return [
            {"column": "BBL", "label": "BB-Lower", "plot": True, "color": "red"},
            {"column": "BBM", "label": "BB-Mid", "plot": True, "color": "orange"},
            {"column": "BBU", "label": "BB-Upper", "plot": True, "color": "green"},
            {"column": "ema_trend", "label": "EMA Trend", "plot": True, "color": "blue"},
            {"column": "rsi", "label": "RSI", "plot": True, "color": "purple", "panel": 2},
        ]

    def compute_rsi(self, series, period):
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ma_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    def generate_signals(self, data):
        df = data.copy()

        # Bollinger Bands
        close = df['close']
        ma = close.rolling(self.bb_length).mean()
        stdev = close.rolling(self.bb_length).std()
        df['BBU'] = ma + self.bb_std * stdev
        df['BBM'] = ma
        df['BBL'] = ma - self.bb_std * stdev

        # RSI
        df['rsi'] = self.compute_rsi(df['close'], self.rsi_period)

        # EMA Trend Filter
        df['ema_trend'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()

        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.atr_period).mean()

        # EMA Slope
        df['ema_slope'] = df['ema_trend'].diff()

        # Entry conditions
        long_entry = (df['close'] < df['BBL']) & (df['ema_slope'] > 0)
        short_entry = (df['close'] > df['BBU']) & (df['ema_slope'] < 0)

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close

        # Take Profit
        if position == 'long' and price >= row.BBM:
            return True, 'Take Profit'
        elif position == 'short' and price <= row.BBM:
            return True, 'Take Profit'

        # Stop Loss
        stop_loss_amount = row.atr * self.atr_multiplier
        if position == 'long' and price <= entry_price - stop_loss_amount:
            return True, 'Stop Loss'
        elif position == 'short' and price >= entry_price + stop_loss_amount:
            return True, 'Stop Loss'

        return False, ''
