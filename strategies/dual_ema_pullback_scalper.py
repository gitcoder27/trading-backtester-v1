from __future__ import annotations

import datetime as dt
import pandas as pd
from backtester.strategy_base import StrategyBase


class DualEMAPullbackScalperStrategy(StrategyBase):
    """Dual-EMA Pullback Scalper with daily goal and trade limits."""

    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.fast_period = p.get("fast_period", 12)
        self.slow_period = p.get("slow_period", 21)
        self.take_profit = p.get("take_profit", 12)
        self.stop_loss = p.get("stop_loss", 10)
        self.cooldown_minutes = p.get("cooldown_minutes", 3)
        self.daily_target = p.get("daily_target", 30)
        self.daily_loss_cap = p.get("daily_loss_cap", 40)
        self.max_trades_per_day = p.get("max_trades_per_day", 25)
        # cost per round trip in index points
        self.cost = p.get("cost", 0.5)
        # sequential logic required
        self._use_fast_vectorized = False

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "deps_fast_period",
                "param_key": "fast_period",
                "type": "number_input",
                "label": "Fast EMA Period",
                "default": 12,
                "min": 1,
                "max": 200,
                "step": 1,
            },
            {
                "name": "deps_slow_period",
                "param_key": "slow_period",
                "type": "number_input",
                "label": "Slow EMA Period",
                "default": 21,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "deps_tp",
                "param_key": "take_profit",
                "type": "number_input",
                "label": "Take Profit (pts)",
                "default": 12,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "deps_sl",
                "param_key": "stop_loss",
                "type": "number_input",
                "label": "Stop Loss (pts)",
                "default": 10,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "deps_cooldown",
                "param_key": "cooldown_minutes",
                "type": "number_input",
                "label": "Cooldown (min)",
                "default": 3,
                "min": 0,
                "max": 60,
                "step": 1,
            },
            {
                "name": "deps_daily_target",
                "param_key": "daily_target",
                "type": "number_input",
                "label": "Daily Target (pts)",
                "default": 30,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "deps_daily_loss",
                "param_key": "daily_loss_cap",
                "type": "number_input",
                "label": "Daily Loss Cap (pts)",
                "default": 40,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "deps_max_trades",
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

    def _prepare_df(self, data):
        df = data.copy()
        ts = pd.to_datetime(df["timestamp"])
        if ts.dt.tz is None:
            ts = ts.dt.tz_localize("Asia/Kolkata")
        else:
            ts = ts.dt.tz_convert("Asia/Kolkata")
        df["timestamp"] = ts
        df = df.sort_values("timestamp")
        df["time"] = df["timestamp"].dt.time
        session_start = dt.time(9, 15)
        session_end = dt.time(15, 30)
        df = df[(df["time"] >= session_start) & (df["time"] <= session_end)]
        df["date"] = df["timestamp"].dt.date
        # EMAs reset per session
        df["ema_fast"] = df.groupby("date")["close"].transform(
            lambda x: x.ewm(span=self.fast_period, adjust=False).mean()
        )
        df["ema_slow"] = df.groupby("date")["close"].transform(
            lambda x: x.ewm(span=self.slow_period, adjust=False).mean()
        )
        # ATR(14) for diagnostics
        def _atr(g):
            high = g["high"]
            low = g["low"]
            close = g["close"]
            prev_close = close.shift(1)
            tr = pd.concat(
                [
                    high - low,
                    (high - prev_close).abs(),
                    (low - prev_close).abs(),
                ],
                axis=1,
            ).max(axis=1)
            return tr.rolling(window=14).mean()

        df["atr14"] = df.groupby("date").apply(_atr).reset_index(level=0, drop=True)
        return df

    def generate_signals(self, data):
        df = self._prepare_df(data)
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
                if i < 14:
                    continue
                if position is not None:
                    high = row["high"]
                    low = row["low"]
                    if position == "long":
                        tp = entry_price + self.take_profit
                        sl = entry_price - self.stop_loss
                        if low <= sl and high >= tp:
                            exit_price = sl
                        elif high >= tp:
                            exit_price = tp
                        elif low <= sl:
                            exit_price = sl
                        else:
                            continue
                        day_pnl += exit_price - entry_price - self.cost
                    else:
                        tp = entry_price - self.take_profit
                        sl = entry_price + self.stop_loss
                        if high >= sl and low <= tp:
                            exit_price = sl
                        elif low <= tp:
                            exit_price = tp
                        elif high >= sl:
                            exit_price = sl
                        else:
                            continue
                        day_pnl += entry_price - exit_price - self.cost
                    trades += 1
                    position = None
                    entry_price = 0.0
                    cooldown_end = ts + pd.Timedelta(minutes=self.cooldown_minutes)
                    if (
                        trades >= self.max_trades_per_day
                        or day_pnl >= self.daily_target
                        or day_pnl <= -self.daily_loss_cap
                    ):
                        break
                    continue
                if (
                    trades >= self.max_trades_per_day
                    or day_pnl >= self.daily_target
                    or day_pnl <= -self.daily_loss_cap
                ):
                    break
                if cooldown_end and ts < cooldown_end:
                    continue
                long_cond = (
                    row["ema_fast"] > row["ema_slow"]
                    and prev_row["close"] < row["ema_fast"]
                    and row["close"] > row["ema_fast"]
                )
                short_cond = (
                    row["ema_fast"] < row["ema_slow"]
                    and prev_row["close"] > row["ema_fast"]
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
        df = df.drop(columns=["date", "time"])
        return df

    def should_exit(self, position, row, entry_price):
        price_high = row.high if hasattr(row, "high") else row["high"]
        price_low = row.low if hasattr(row, "low") else row["low"]
        if position == "long":
            tp = entry_price + self.take_profit
            sl = entry_price - self.stop_loss
            if price_low <= sl and price_high >= tp:
                return True, "Stop Loss"
            if price_high >= tp:
                return True, "Take Profit"
            if price_low <= sl:
                return True, "Stop Loss"
        elif position == "short":
            tp = entry_price - self.take_profit
            sl = entry_price + self.stop_loss
            if price_high >= sl and price_low <= tp:
                return True, "Stop Loss"
            if price_low <= tp:
                return True, "Take Profit"
            if price_high >= sl:
                return True, "Stop Loss"
        return False, ""
