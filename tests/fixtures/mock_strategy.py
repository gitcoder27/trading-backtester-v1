import pandas as pd
from backtester.strategy_base import StrategyBase

class MockStrategy(StrategyBase):
    """
    A simple mock strategy for testing the backtest engine.
    - Buys on the first row.
    - Sells (exits long) if price drops 5% below entry.
    - Shorts on the third row if no position.
    - Covers (exits short) if price rises 5% above entry.
    - Generates an 'indicator' column.
    """
    def __init__(self, params=None):
        super().__init__(params)
        self.sl_pct = self.params.get('sl_pct', 0.05) # Default 5% stop loss

    def generate_signals(self, data):
        """
        Generates signals:
        - Signal 1 (buy) on first data point.
        - Signal -1 (short) on third data point.
        - Also adds a dummy 'indicator1' column.
        """
        signals = pd.Series(0, index=data.index)
        if len(data) > 0:
            signals.iloc[0] = 1  # Buy on the first bar
        if len(data) > 2:
            signals.iloc[2] = -1 # Short on the third bar (if no position)

        # Add a dummy indicator
        indicator_data = data['close'] * 1.01

        return data.assign(signal=signals, indicator1=indicator_data)

    def should_exit(self, position, row, entry_price):
        """
        Exit logic:
        - Long: exit if current close is below entry_price * (1 - sl_pct)
        - Short: exit if current close is above entry_price * (1 + sl_pct)
        """
        if position == 'long':
            if row.close < entry_price * (1 - self.sl_pct):
                return True, f"SL Hit ({self.sl_pct*100}%)"
        elif position == 'short':
            if row.close > entry_price * (1 + self.sl_pct):
                return True, f"SL Hit ({self.sl_pct*100}%)"
        return False, None

    def indicator_config(self):
        """
        Configuration for plotting indicators.
        """
        return [
            {'column': 'indicator1', 'label': 'Mock Indicator', 'color': 'purple', 'type': 'line', 'panel': 1, 'plot': True},
        ]

class NoSignalStrategy(StrategyBase):
    """A strategy that generates no signals."""
    def generate_signals(self, data):
        signals = pd.Series(0, index=data.index) # Always 0
        return data.assign(signal=signals)

    def should_exit(self, position, row, entry_price):
        return False, None # Never exits based on its own logic

class BuyAndHoldStrategy(StrategyBase):
    """A strategy that buys on the first signal and holds."""
    def generate_signals(self, data):
        signals = pd.Series(0, index=data.index)
        if len(data) > 0:
            signals.iloc[0] = 1  # Buy on the first bar
        return data.assign(signal=signals)

    def should_exit(self, position, row, entry_price):
        return False, None # Never exits
