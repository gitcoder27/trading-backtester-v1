"""
strategy_base.py
Base class/interface for trading strategies.
"""

class StrategyBase:
    def __init__(self, params=None):
        self.params = params or {}

    def generate_signals(self, data):
        """
        Given a DataFrame of historical data, return a DataFrame or Series of signals.
        Must be implemented by all strategies.
        """
        raise NotImplementedError("generate_signals must be implemented by the strategy.")