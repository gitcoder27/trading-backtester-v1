"""EMA Pullback DailyTarget Scalper (EPS-30).

This strategy trades pullbacks to the 9-period EMA in the direction of the
21-period EMA trend. It aims for quick scalps with a 10 point target and an
8 point stop. After each trade a short cooldown is enforced and trading for
the day stops once a daily point target is reached or a maximum number of
trades have been taken.
"""

from __future__ import annotations

import pandas as pd
from backtester.strategy_base import StrategyBase


class EMAPullbackScalperDailyTargetStrategy(StrategyBase):
    """EMA Pullback Scalper with daily goal and trade limits."""

    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.fast_period = p.get("fast_period", 9)
        self.slow_period = p.get("slow_period", 21)
        self.take_profit = p.get("take_profit", 10)
        self.stop_loss = p.get("stop_loss", 8)
        self.cooldown_minutes = p.get("cooldown_minutes", 3)
        self.daily_target = p.get("daily_target", 30)
        self.max_trades_per_day = p.get("max_trades_per_day", 25)
        # Sequential logic required due to cooldown and daily limits
        self._use_fast_vectorized = False

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "eps_fast_period",
                "param_key": "fast_period",
                "type": "number_input",
                "label": "Fast EMA Period",
                "default": 9,
                "min": 1,
                "max": 200,
                "step": 1,
            },
            {
                "name": "eps_slow_period",
                "param_key": "slow_period",
                "type": "number_input",
                "label": "Slow EMA Period",
                "default": 21,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "eps_tp",
                "param_key": "take_profit",
                "type": "number_input",
                "label": "Take Profit (pts)",
                "default": 10,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "eps_sl",
                "param_key": "stop_loss",
                "type": "number_input",
                "label": "Stop Loss (pts)",
                "default": 8,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "eps_cooldown",
                "param_key": "cooldown_minutes",
                "type": "number_input",
                "label": "Cooldown (min)",
                "default": 3,
                "min": 0,
                "max": 60,
                "step": 1,
            },
            {
                "name": "eps_daily_target",
                "param_key": "daily_target",
                "type": "number_input",
                "label": "Daily Target (pts)",
                "default": 30,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "eps_max_trades",
                "param_key": "max_trades_per_day",
                "type": "number_input",
                "label": "Max Trades/Day",
                "default": 25,
                "min": 1,
                "max": 100,
                "step": 1,
            },
        ]

    def indicator_config(self):
        return [
            {
                "column": "ema_fast",
                "label": f"EMA({self.fast_period})",
                "plot": True,
                "color": "green",
                "type": "solid",
                "panel": 1,
            },
            {
                "column": "ema_slow",
                "label": f"EMA({self.slow_period})",
                "plot": True,
                "color": "red",
                "type": "solid",
                "panel": 1,
            },
        ]

    def generate_signals(self, data):
        df = data.copy()
        df["date"] = pd.to_datetime(df["timestamp"]).dt.date
        df["ema_fast"] = df.groupby("date")["close"].transform(
            lambda x: x.ewm(span=self.fast_period, adjust=False).mean()
        )
        df["ema_slow"] = df.groupby("date")["close"].transform(
            lambda x: x.ewm(span=self.slow_period, adjust=False).mean()
        )
        df["signal"] = 0

        for day, day_df in df.groupby("date"):
            position = None
            entry_price = 0.0
            cooldown_end = None
            trades = 0
            day_pnl = 0.0

            for i in range(1, len(day_df)):
                idx = day_df.index[i]
                row = day_df.loc[idx]
                prev_row = day_df.iloc[i - 1]
                ts = row["timestamp"]

                if position is not None:
                    if position == "long":
                        if row["close"] >= entry_price + self.take_profit or row["close"] <= entry_price - self.stop_loss:
                            day_pnl += row["close"] - entry_price
                            trades += 1
                            position = None
                            entry_price = 0.0
                            cooldown_end = ts + pd.Timedelta(minutes=self.cooldown_minutes)
                    else:  # short
                        if row["close"] <= entry_price - self.take_profit or row["close"] >= entry_price + self.stop_loss:
                            day_pnl += entry_price - row["close"]
                            trades += 1
                            position = None
                            entry_price = 0.0
                            cooldown_end = ts + pd.Timedelta(minutes=self.cooldown_minutes)
                    continue

                if trades >= self.max_trades_per_day or day_pnl >= self.daily_target:
                    break

                if cooldown_end and ts < cooldown_end:
                    continue

                long_cond = (
                    row["ema_fast"] > row["ema_slow"]
                    and prev_row["close"] < prev_row["ema_fast"]
                    and row["close"] > row["ema_fast"]
                )
                short_cond = (
                    row["ema_fast"] < row["ema_slow"]
                    and prev_row["close"] > prev_row["ema_fast"]
                    and row["close"] < row["ema_fast"]
                )

                if long_cond:
                    df.loc[idx, "signal"] = 1
                    position = "long"
                    entry_price = row["close"]
                elif short_cond:
                    df.loc[idx, "signal"] = -1
                    position = "short"
                    entry_price = row["close"]

        df.drop(columns=["date"], inplace=True)
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close if hasattr(row, "close") else row["close"]
        if position == "long":
            if price >= entry_price + self.take_profit:
                return True, "Take Profit"
            if price <= entry_price - self.stop_loss:
                return True, "Stop Loss"
        elif position == "short":
            if price <= entry_price - self.take_profit:
                return True, "Take Profit"
            if price >= entry_price + self.stop_loss:
                return True, "Stop Loss"
        return False, ""
