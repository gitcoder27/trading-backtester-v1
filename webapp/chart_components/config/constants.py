"""Chart configuration constants."""
from __future__ import annotations


class ChartConstants:
    """Constants for chart configuration."""

    # Performance limits
    DEFAULT_MAX_POINTS = 2000
    PROGRESSIVE_THRESHOLD = 500
    LARGE_THRESHOLD = 1000
    THROTTLE_DELAY = 100

    # Chart dimensions
    DEFAULT_HEIGHT = "600px"
    DEFAULT_WIDTH = "100%"

    # Animation settings
    ANIMATION_DURATION = 300
    ANIMATION_EASING = "cubicOut"

    # Tooltip settings
    TOOLTIP_HIDE_DELAY = 100
    TOOLTIP_PADDING = [6, 8]
    TOOLTIP_FONT_SIZE = 11

    # Symbol sizes
    TRADE_SYMBOL_SIZE = 12
    TRADE_LINE_WIDTH = 2
    INDICATOR_LINE_WIDTH = 1

    # Candlestick sizing
    CANDLE_MIN_WIDTH = 5
    CANDLE_MAX_WIDTH = 30

    # Z-index layers
    Z_CANDLESTICKS = 1
    Z_INDICATORS = 2
    Z_TRADE_LINES = 2
    Z_TRADE_POINTS = 3
