from __future__ import annotations
from strategies.ema10_scalper import EMA10ScalperStrategy
from strategies.ema44_scalper import EMA44ScalperStrategy
from strategies.ema50_scalper import EMA50ScalperStrategy
from strategies.bbands_scalper import BBandsScalperStrategy
from strategies.first_candle_breakout import FirstCandleBreakoutStrategy
from strategies.rsi_cross_strategy import RSICrossStrategy
from strategies.mean_reversion_scalper import MeanReversionScalper

__all__ = ['STRATEGY_MAP']

STRATEGY_MAP = {
    "EMA10Scalper": EMA10ScalperStrategy,
    "EMA44Scalper": EMA44ScalperStrategy,
    "EMA50Scalper": EMA50ScalperStrategy,
    "BBandsScalper": BBandsScalperStrategy,
    "FirstCandleBreakout": FirstCandleBreakoutStrategy,
    "RSICross": RSICrossStrategy,
    "MeanReversionScalper": MeanReversionScalper,
}
