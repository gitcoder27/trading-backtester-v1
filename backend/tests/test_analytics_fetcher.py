"""Tests for analytics data fetching helpers."""

from unittest.mock import MagicMock

import pandas as pd

from backend.app.database.models import Backtest
from backend.app.services.analytics.data_fetcher import AnalyticsDataFetcher


def _make_price(point: str, price: float) -> dict:
    return {
        "timestamp": point,
        "open": price,
        "high": price + 1,
        "low": price - 1,
        "close": price + 0.5,
    }


def test_load_price_data_filters_and_downsamples():
    fetcher = AnalyticsDataFetcher(dataset_service_factory=lambda: MagicMock())
    backtest = Backtest()
    backtest.id = 1
    backtest.dataset_id = None

    records = [
        _make_price("2024-01-01T00:00:00Z", 100),
        _make_price("2024-01-02T00:00:00Z", 101),
        _make_price("2024-01-03T00:00:00Z", 102),
    ]

    bundle = fetcher.load_price_data(
        backtest,
        {"price_data": records},
        session=MagicMock(),
        start="2024-01-02",
        end="2024-01-03",
        max_candles=1,
    )

    assert bundle.filtered is True
    assert bundle.sampled is True
    assert bundle.total_candles == 2  # before downsampling
    assert len(bundle.dataframe) == 1
    assert bundle.start_bound is not None and bundle.end_bound is not None
    assert pd.Timestamp("2024-01-02T00:00:00Z") <= bundle.end_bound
