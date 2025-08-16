"""
EMA50 & EMA100 with Stochastic Crossover Strategy

This strategy trades in the direction of the 50 and 100 period exponential
moving averages (EMAs) and uses a stochastic oscillator to time entries.

Long Setup:
    * 50 EMA is above the 100 EMA (uptrend).
    * Stochastic %K (5) crosses above %D (3) while both are at or below 20.
    * Enter long on the crossover.
    * Stop loss is the low of the entry candle and a fixed 20 point profit
      target is used for exits.

Short Setup:
    * 50 EMA is below the 100 EMA (downtrend).
    * Stochastic %K crosses below %D while both are at or above 80.
    * Stop loss is the high of the entry candle with the same 20 point profit
      target.

The strategy is designed for quick scalp trades in the direction of the
prevailing trend.
"""

from backtester.strategy_base import StrategyBase
import pandas as pd
import numpy as np


class EMA50_100StochasticStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_short = params.get("ema_short", 50) if params else 50
        self.ema_long = params.get("ema_long", 100) if params else 100
        self.k_period = params.get("k_period", 5) if params else 5
        self.d_period = params.get("d_period", 3) if params else 3
        self.smooth_period = params.get("smooth_period", 5) if params else 5
        self.profit_target_points = (
            params.get("profit_target_points", 20) if params else 20
        )

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "ema_short",
                "param_key": "ema_short",
                "type": "number_input",
                "label": "Short EMA Period",
                "default": 50,
                "min": 5,
                "max": 200,
                "step": 1,
            },
            {
                "name": "ema_long",
                "param_key": "ema_long",
                "type": "number_input",
                "label": "Long EMA Period",
                "default": 100,
                "min": 10,
                "max": 400,
                "step": 1,
            },
            {
                "name": "stoch_k",
                "param_key": "k_period",
                "type": "number_input",
                "label": "%K Period",
                "default": 5,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "name": "stoch_d",
                "param_key": "d_period",
                "type": "number_input",
                "label": "%D Period",
                "default": 3,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "name": "stoch_smooth",
                "param_key": "smooth_period",
                "type": "number_input",
                "label": "Stochastic Smooth",
                "default": 5,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "name": "profit_target_points",
                "param_key": "profit_target_points",
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
            {
                "column": "ema_short",
                "label": f"EMA({self.ema_short})",
                "plot": True,
                "color": "blue",
                "type": "solid",
                "panel": 1,
            },
            {
                "column": "ema_long",
                "label": f"EMA({self.ema_long})",
                "plot": True,
                "color": "red",
                "type": "solid",
                "panel": 1,
            },
            {
                "column": "stoch_k",
                "label": f"Stoch %K",
                "plot": True,
                "color": "green",
                "type": "solid",
                "panel": 2,
            },
            {
                "column": "stoch_d",
                "label": f"Stoch %D",
                "plot": True,
                "color": "orange",
                "type": "solid",
                "panel": 2,
            },
        ]

    def _compute_stochastic(self, df: pd.DataFrame) -> pd.DataFrame:
        low_min = df["low"].rolling(self.k_period).min()
        high_max = df["high"].rolling(self.k_period).max()
        range_ = (high_max - low_min).replace(0, np.nan)
        fast_k = 100 * (df["close"] - low_min) / range_
        stoch_k = fast_k.rolling(self.smooth_period).mean()
        stoch_d = stoch_k.rolling(self.d_period).mean()
        df["stoch_k"] = stoch_k
        df["stoch_d"] = stoch_d
        return df

    def generate_signals(self, data):
        df = data.copy()
        df["ema_short"] = df["close"].ewm(span=self.ema_short, adjust=False).mean()
        df["ema_long"] = df["close"].ewm(span=self.ema_long, adjust=False).mean()

        df = self._compute_stochastic(df)

        df["signal"] = 0

        for i in range(1, len(df)):
            ema_s = df["ema_short"].iloc[i]
            ema_l = df["ema_long"].iloc[i]
            k_prev = df["stoch_k"].iloc[i - 1]
            d_prev = df["stoch_d"].iloc[i - 1]
            k = df["stoch_k"].iloc[i]
            d = df["stoch_d"].iloc[i]

            # Long setup
            if (
                ema_s > ema_l
                and k_prev <= d_prev
                and k > d
                and max(k_prev, d_prev, k, d) <= 20
            ):
                df.iloc[i, df.columns.get_loc("signal")] = 1

            # Short setup
            elif (
                ema_s < ema_l
                and k_prev >= d_prev
                and k < d
                and min(k_prev, d_prev, k, d) >= 80
            ):
                df.iloc[i, df.columns.get_loc("signal")] = -1

        # Store entry candle levels for stop loss reference
        df["entry_low"] = np.where(df["signal"] == 1, df["low"], np.nan)
        df["entry_low"] = df["entry_low"].ffill()
        df["entry_high"] = np.where(df["signal"] == -1, df["high"], np.nan)
        df["entry_high"] = df["entry_high"].ffill()

        return df

    def should_exit(self, position, row, entry_price):
        if position == "long":
            stop = row.entry_low if pd.notna(row.entry_low) else None
            if stop is not None and row.low <= stop:
                return True, "stop_loss"
            if row.high >= entry_price + self.profit_target_points:
                return True, "profit_target"
        elif position == "short":
            stop = row.entry_high if pd.notna(row.entry_high) else None
            if stop is not None and row.high >= stop:
                return True, "stop_loss"
            if row.low <= entry_price - self.profit_target_points:
                return True, "profit_target"
        return False, ""
