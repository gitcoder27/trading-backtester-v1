"""
strategy_base.py
Base class/interface for trading strategies.
"""

class StrategyBase:
    def __init__(self, params=None):
        self.params = params or {}

    @staticmethod
    def get_params_config():
        """
        Returns a list of parameter configurations for the UI.
        Each element in the list is a dictionary defining a widget.
        """
        return []

    def generate_signals(self, data):
        """
        Given a DataFrame of historical data, return a DataFrame or Series of signals.
        Must be implemented by all strategies.
        """
        raise NotImplementedError("generate_signals must be implemented by the strategy.")

    def should_exit(self, position, row, entry_price):
        """
        Given current position ('long' or 'short'), current row, and entry price,
        return (exit_now: bool, exit_reason: str) for this bar.
        Must be implemented by all strategies.
        """
        raise NotImplementedError("should_exit must be implemented by the strategy.")
