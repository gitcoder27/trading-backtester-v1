"""
EMA10 Scalper Strategy - Main implementation
This is a wrapper that imports the primary EMA10 scalper strategy
"""

from strategies.ema10_scalper_1 import EMA10ScalperStrategyV1 as EMA10ScalperStrategy

# Export the strategy for easy import
__all__ = ['EMA10ScalperStrategy']
