from backtester.strategy_base import StrategyBase
import pandas as pd
import numpy as np

class BBandsRSIStochasticStrategy(StrategyBase):
    """Bollinger Bands + RSI + Stochastic Oscillator scalping strategy.

    Long entry when price pierces below the lower Bollinger Band while RSI and
    Stochastic are in oversold territory. Short entry is the mirror setup.
    Trades exit on a close back to the middle Bollinger Band, a profit target
    or a fixed-buffer stop loss from the signal candle.
    """

    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.bb_length = int(p.get("bb_length", 20))
        self.bb_std = float(p.get("bb_std", 2.0))
        self.rsi_period = int(p.get("rsi_period", 14))
        self.stoch_k = int(p.get("stoch_k", 14))
        self.stoch_d = int(p.get("stoch_d", 3))
        self.stoch_smooth = int(p.get("stoch_smooth", 3))
        self.stop_buffer = float(p.get("stop_buffer", 5))
        self.profit_target = float(p.get("profit_target", 20))
        self._entry_stop = None

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "bb_length",
                "param_key": "bb_length",
                "type": "number_input",
                "label": "BB Period",
                "default": 20,
                "min": 5,
                "max": 200,
                "step": 1,
            },
            {
                "name": "bb_std",
                "param_key": "bb_std",
                "type": "number_input",
                "label": "BB StdDev",
                "default": 2.0,
                "min": 0.5,
                "max": 5.0,
                "step": 0.1,
            },
            {
                "name": "rsi_period",
                "param_key": "rsi_period",
                "type": "number_input",
                "label": "RSI Period",
                "default": 14,
                "min": 2,
                "max": 100,
                "step": 1,
            },
            {
                "name": "stoch_k",
                "param_key": "stoch_k",
                "type": "number_input",
                "label": "%K Period",
                "default": 14,
                "min": 1,
                "max": 100,
                "step": 1,
            },
            {
                "name": "stoch_d",
                "param_key": "stoch_d",
                "type": "number_input",
                "label": "%D Period",
                "default": 3,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "name": "stoch_smooth",
                "param_key": "stoch_smooth",
                "type": "number_input",
                "label": "Stoch Smooth",
                "default": 3,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "name": "stop_buffer",
                "param_key": "stop_buffer",
                "type": "number_input",
                "label": "Stop Buffer (pts)",
                "default": 5,
                "min": 1,
                "max": 100,
                "step": 1,
            },
            {
                "name": "profit_target",
                "param_key": "profit_target",
                "type": "number_input",
                "label": "Profit Target (pts)",
                "default": 20,
                "min": 1,
                "max": 400,
                "step": 1,
            },
        ]

    def indicator_config(self):
        return [
            {"column": "mid", "label": f"BB-Mid({self.bb_length})", "plot": True, "color": "orange", "type": "solid"},
            {"column": "upper", "label": f"BB-Upper({self.bb_length},{self.bb_std})", "plot": True, "color": "green", "type": "dash"},
            {"column": "lower", "label": f"BB-Lower({self.bb_length},{self.bb_std})", "plot": True, "color": "red", "type": "dash"},
            {"column": "rsi", "label": f"RSI({self.rsi_period})", "plot": True, "color": "purple", "panel": 2},
            {"column": "stoch_k", "label": "Stoch %K", "plot": True, "color": "blue", "panel": 3},
            {"column": "stoch_d", "label": "Stoch %D", "plot": True, "color": "orange", "panel": 3},
        ]

    def _compute_rsi(self, series: pd.Series) -> pd.Series:
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1 / self.rsi_period, min_periods=self.rsi_period, adjust=False).mean()
        ma_down = down.ewm(alpha=1 / self.rsi_period, min_periods=self.rsi_period, adjust=False).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    def _compute_stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        low_min = df["low"].rolling(self.stoch_k).min()
        high_max = df["high"].rolling(self.stoch_k).max()
        range_ = (high_max - low_min).replace(0, np.nan)
        fast_k = 100 * (df["close"] - low_min) / range_
        stoch_k = fast_k.rolling(self.stoch_smooth).mean()
        stoch_d = stoch_k.rolling(self.stoch_d).mean()
        df["stoch_k"] = stoch_k
        df["stoch_d"] = stoch_d
        return df

    def generate_signals(self, data):
        df = data.copy()
        close = df["close"]
        df["mid"] = close.rolling(self.bb_length).mean()
        df["std"] = close.rolling(self.bb_length).std(ddof=0)
        df["upper"] = df["mid"] + self.bb_std * df["std"]
        df["lower"] = df["mid"] - self.bb_std * df["std"]

        df["rsi"] = self._compute_rsi(close)
        df = self._compute_stochastic(df)

        long_entry = (
            (df["close"] < df["lower"]) &
            (df["rsi"] < 30) &
            (df["stoch_k"] < 20) &
            (df["stoch_d"] < 20)
        )
        short_entry = (
            (df["close"] > df["upper"]) &
            (df["rsi"] > 70) &
            (df["stoch_k"] > 80) &
            (df["stoch_d"] > 80)
        )

        df["signal"] = 0
        df.loc[long_entry, "signal"] = 1
        df.loc[short_entry, "signal"] = -1

        df["long_stop"] = df["low"] - self.stop_buffer
        df["short_stop"] = df["high"] + self.stop_buffer
        df["long_stop_prev"] = df["long_stop"].shift(1)
        df["short_stop_prev"] = df["short_stop"].shift(1)

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        mid = row.mid
        if position == "long":
            if self._entry_stop is None:
                self._entry_stop = row.long_stop_prev if not pd.isna(row.long_stop_prev) else entry_price - self.stop_buffer
            stop = self._entry_stop
            if row.low <= stop:
                self._entry_stop = None
                return True, "stop_loss"
            if price >= entry_price + self.profit_target:
                self._entry_stop = None
                return True, "profit_target"
            if price > mid:
                self._entry_stop = None
                return True, "mid_exit"
        elif position == "short":
            if self._entry_stop is None:
                self._entry_stop = row.short_stop_prev if not pd.isna(row.short_stop_prev) else entry_price + self.stop_buffer
            stop = self._entry_stop
            if row.high >= stop:
                self._entry_stop = None
                return True, "stop_loss"
            if price <= entry_price - self.profit_target:
                self._entry_stop = None
                return True, "profit_target"
            if price < mid:
                self._entry_stop = None
                return True, "mid_exit"
        else:
            self._entry_stop = None
        return False, ""
