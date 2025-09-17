"""Tests for TradingView chart builders."""

import pandas as pd

from backend.app.services.analytics.tradingview_builder import TradingViewBuilder


def _price_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"timestamp": "2024-01-01T00:00:00Z", "open": 100, "high": 101, "low": 99, "close": 100.5},
            {"timestamp": "2024-01-02T00:00:00Z", "open": 101, "high": 102, "low": 100, "close": 101.5},
        ]
    )


def test_build_trade_markers_respects_bounds():
    builder = TradingViewBuilder()
    price_df = _price_frame()
    results = {
        "trades": [
            {
                "entry_time": "2024-01-01T00:00:00Z",
                "exit_time": "2024-01-02T00:00:00Z",
                "direction": "long",
                "pnl": 25,
            }
        ]
    }
    markers = builder.build_trade_markers(
        results,
        price_df,
        start_ts=pd.Timestamp("2024-01-02T00:00:00Z"),
        end_ts=pd.Timestamp("2024-01-02T23:00:00Z"),
    )
    # Only exit marker should remain after filtering
    assert len(markers) == 1
    assert markers[0]["position"] == "aboveBar"


def test_build_indicator_series_resolves_css_colors():
    builder = TradingViewBuilder()
    price_df = _price_frame()
    results = {
        "indicators": {"ema": [100.0, 101.0]},
        "indicator_cfg": [
            {
                "name": "ema",
                "color": "blue",
                "label": "EMA",
                "style": "line",
                "panel": "overlay",
                "width": 2,
            }
        ],
    }
    series = builder.build_indicator_series(results, price_df)
    assert len(series) == 1
    indicator = series[0]
    assert indicator["color"] == "#1E90FF"  # CSS color converted to hex
    assert indicator["lineWidth"] == 2
