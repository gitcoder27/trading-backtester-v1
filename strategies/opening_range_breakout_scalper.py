"""
OpeningRangeBreakoutScalper implements a basic opening range breakout strategy.

Strategy logic:
- For each trading day, compute the high and low of the first `or_period` minutes
  starting at the session open (assumed 9:15).
- After the opening range is formed, go long when price closes above the range high
  and go short when price closes below the range low. Signals are triggered on
  crossovers to avoid repeated entries while price remains outside the range.
- Exits use fixed profit target and stop loss measured in index points.

The strategy relies on the engine's intraday handling and optional daily
profit target to stop trading after a desired amount of points is achieved.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase


class OpeningRangeBreakoutScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.or_period = params.get("or_period", 15) if params else 15
        self.profit_target = params.get("profit_target", 30) if params else 30
        self.stop_loss = params.get("stop_loss", 15) if params else 15
        # complex exit logic -> use traditional engine
        self._use_fast_vectorized = False

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "orb_or_period",
                "param_key": "or_period",
                "type": "number_input",
                "label": "Opening Range (min)",
                "default": 15,
                "min": 1,
                "max": 60,
                "step": 1,
            },
            {
                "name": "orb_profit_target",
                "param_key": "profit_target",
                "type": "number_input",
                "label": "Profit Target (pts)",
                "default": 30,
                "min": 1,
                "max": 200,
                "step": 1,
            },
            {
                "name": "orb_stop_loss",
                "param_key": "stop_loss",
                "type": "number_input",
                "label": "Stop Loss (pts)",
                "default": 15,
                "min": 1,
                "max": 200,
                "step": 1,
            },
        ]

    def indicator_config(self):
        return [
            {
                "column": "or_high",
                "label": "OR High",
                "plot": True,
                "color": "green",
                "type": "dash",
                "panel": 1,
            },
            {
                "column": "or_low",
                "label": "OR Low",
                "plot": True,
                "color": "red",
                "type": "dash",
                "panel": 1,
            },
        ]

    def generate_signals(self, data):
        df = data.copy()
        df["signal"] = 0
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["or_high"] = None
        df["or_low"] = None

        result_frames = []
        for day, day_df in df.groupby("date"):
            day_df = day_df.copy()
            or_window = day_df.iloc[: self.or_period]
            if or_window.empty:
                result_frames.append(day_df)
                continue
            or_high = or_window["high"].max()
            or_low = or_window["low"].min()
            day_df.loc[:, "or_high"] = or_high
            day_df.loc[:, "or_low"] = or_low

            after_window = day_df.iloc[self.or_period :]
            prev_close = after_window["close"].shift(1)
            long_cond = (prev_close <= or_high) & (after_window["close"] > or_high)
            short_cond = (prev_close >= or_low) & (after_window["close"] < or_low)

            day_df.loc[after_window.index[long_cond], "signal"] = 1
            day_df.loc[after_window.index[short_cond], "signal"] = -1
            result_frames.append(day_df)

        return pd.concat(result_frames).sort_index()

    def should_exit(self, position, row, entry_price):
        price = row.close if hasattr(row, "close") else row["close"]
        if position == "long":
            if price >= entry_price + self.profit_target:
                return True, "Target"
            if price <= entry_price - self.stop_loss:
                return True, "Stop Loss"
        elif position == "short":
            if price <= entry_price - self.profit_target:
                return True, "Target"
            if price >= entry_price + self.stop_loss:
                return True, "Stop Loss"
        return False, ""
