"""
EMA50 & EMA100 Crossover with Stochastic Strategy

This strategy trades the first pullback after a new trend is signalled by a
crossover of the 50-period and 100-period exponential moving averages (EMAs).
It uses a stochastic oscillator to time the entry.

Long Setup:
    * Wait for the 50 EMA to cross above the 100 EMA (uptrend).
    * During the subsequent pullback, wait for the stochastic (%K) to dip
      below 20 and then cross back above 20 while price recovers above the
      short EMA.
    * Enter long when these conditions align.
    * Stop loss is set at the recent swing low and a fixed profit target is
      used for exits.

Short Setup:
    * Mirror of the long setup using a 50 EMA crossing below the 100 EMA and
      a stochastic pullback above 80 that crosses back below 80.

The strategy is designed for quick scalping trades following the first
pullback of a new short-term trend.
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
        self.smooth_period = params.get("smooth_period", 3) if params else 3
        self.profit_target_points = (
            params.get("profit_target_points", 20) if params else 20
        )
        self.swing_lookback = params.get("swing_lookback", 5) if params else 5

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
                "default": 3,
                "min": 1,
                "max": 50,
                "step": 1,
            },
            {
                "name": "swing_lookback",
                "param_key": "swing_lookback",
                "type": "number_input",
                "label": "Swing Lookback",
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

        df["recent_low"] = df["low"].rolling(self.swing_lookback).min().shift(1)
        df["recent_high"] = df["high"].rolling(self.swing_lookback).max().shift(1)

        df["signal"] = 0
        wait_long = False
        wait_short = False

        for i in range(1, len(df)):
            ema_s_prev = df["ema_short"].iloc[i - 1]
            ema_l_prev = df["ema_long"].iloc[i - 1]
            ema_s = df["ema_short"].iloc[i]
            ema_l = df["ema_long"].iloc[i]
            stoch_prev = df["stoch_k"].iloc[i - 1]
            stoch = df["stoch_k"].iloc[i]
            price = df["close"].iloc[i]

            if ema_s_prev <= ema_l_prev and ema_s > ema_l:
                wait_long = True
                wait_short = False
            elif ema_s_prev >= ema_l_prev and ema_s < ema_l:
                wait_short = True
                wait_long = False

            if (
                wait_long
                and stoch_prev < 20
                and stoch >= 20
                and price > ema_s
            ):
                df.iloc[i, df.columns.get_loc("signal")] = 1
                wait_long = False

            if (
                wait_short
                and stoch_prev > 80
                and stoch <= 80
                and price < ema_s
            ):
                df.iloc[i, df.columns.get_loc("signal")] = -1
                wait_short = False

        return df

    def should_exit(self, position, row, entry_price):
        if position == "long":
            stop = row.recent_low if pd.notna(row.recent_low) else None
            if stop is not None and row.low <= stop:
                return True, "stop_loss"
            if row.high >= entry_price + self.profit_target_points:
                return True, "profit_target"
        elif position == "short":
            stop = row.recent_high if pd.notna(row.recent_high) else None
            if stop is not None and row.high >= stop:
                return True, "stop_loss"
            if row.low <= entry_price - self.profit_target_points:
                return True, "profit_target"
        return False, ""
