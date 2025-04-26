"""
reporting.py (refactored)
This module now re-exports reporting utilities from submodules:
- plotting.py: plotting functions
- trade_log.py: trade log saving
- comparison.py: comparison table
- html_report.py: HTML report generation

This keeps backward compatibility for imports from reporting.py.
"""

from .plotting import plot_trades_on_candlestick_plotly, plot_equity_curve, plot_trades_on_price
from .trade_log import save_trade_log
from .comparison import comparison_table
from .html_report import generate_html_report