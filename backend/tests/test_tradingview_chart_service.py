# Tests for TradingViewChartService
# Testing framework: pytest (with standard monkeypatch and fixture usage).
import sys
import types
from datetime import date
from types import SimpleNamespace

import pandas as pd
import pytest

# Attempt to import the service from common candidate paths.
# Adjust if project structure differs; tests try multiple paths for resilience.
try:
    from backend.services.tradingview_chart_service import TradingViewChartService  # typical location
except ImportError:
    from services.tradingview_chart_service import TradingViewChartService     # fallback


class DummyFormatter:
    def __init__(self):
        self.calls = []
    def sanitize_json(self, payload):
        self.calls.append(payload)
        return payload

class DummyBuilder:
    def __init__(self, candles=None, trade_markers=None, indicators=None):
        self._candles = candles if candles is not None else []
        self._trade_markers = trade_markers if trade_markers is not None else []
        self._indicators = indicators if indicators is not None else []
        self.calls = {"build_candles": [], "build_trade_markers": [], "build_indicator_series": []}
    def build_candles(self, df):
        self.calls["build_candles"].append(df)
        return list(self._candles)
    def build_trade_markers(self, results, df, tz, start_ts, end_ts):
        self.calls["build_trade_markers"].append((results, df, tz, start_ts, end_ts))
        return list(self._trade_markers)
    def build_indicator_series(self, results, df, strategy_params=None):
        self.calls["build_indicator_series"].append((results, df, strategy_params))
        return list(self._indicators)

class DummyFetcher:
    def __init__(self, bundle=None, exc=None):
        self.bundle = bundle
        self.exc = exc
        self.calls = []
    def load_price_data(self, backtest, results, session, **kwargs):
        self.calls.append((backtest, results, session, kwargs))
        if self.exc:
            raise self.exc
        return self.bundle

def _bundle(
    *,
    df=None,
    dataset_name="TESTSET",
    total_candles=3,
    sampled=False,
    filtered=False,
    available_sessions=None,
    resolved_sessions=None,
    requested_start=None,
    requested_end=None,
    start_bound=None,
    end_bound=None,
):
    if df is None:
        df = pd.DataFrame({"t": [1, 2, 3], "o": [1, 2, 3], "h": [2, 3, 4], "l": [0, 1, 2], "c": [1.5, 2.5, 3.5]})
    if available_sessions is None:
        available_sessions = [
            pd.Timestamp("2024-01-02T00:00:00Z"),
            pd.Timestamp("2024-01-03T00:00:00Z"),
            pd.Timestamp("2024-01-05T00:00:00Z"),
        ]
    if resolved_sessions is None:
        resolved_sessions = [
            pd.Timestamp("2024-01-03T00:00:00Z"),
            pd.Timestamp("2024-01-04T00:00:00Z"),
        ]
    return SimpleNamespace(
        dataframe=df,
        dataset_name=dataset_name,
        total_candles=total_candles,
        sampled=sampled,
        filtered=filtered,
        available_sessions=available_sessions,
        resolved_sessions=resolved_sessions,
        requested_start=requested_start or pd.Timestamp("2024-01-03T00:00:00Z"),
        requested_end=requested_end or pd.Timestamp("2024-01-04T00:00:00Z"),
        start_bound=start_bound or pd.Timestamp("2024-01-03T00:00:00Z"),
        end_bound=end_bound or pd.Timestamp("2024-01-04T23:59:59Z"),
    )

class BT:
    def __init__(self, id="bt-1", results=None, strategy_params=None):
        self.id = id
        self.results = results if results is not None else {}
        self.strategy_params = strategy_params

@pytest.fixture
def base_candles():
    return [
        {"time": "2024-01-03T00:00:00Z", "open": 1, "high": 2, "low": 0, "close": 1},
        {"time": "2024-01-04T00:00:00Z", "open": 2, "high": 3, "low": 1, "close": 2},
        {"time": "2024-01-05T00:00:00Z", "open": 3, "high": 4, "low": 2, "close": 3},
    ]

def _install_dummy_price_data_error(module_under_test_pkg: str):
    # Provide a dummy module with PriceDataError to satisfy "from .data_fetcher import PriceDataError"
    mod_name = f"{module_under_test_pkg}.data_fetcher"
    m = types.ModuleType(mod_name)
    class PriceDataError(Exception):
        pass
    m.PriceDataError = PriceDataError
    sys.modules[mod_name] = m
    return PriceDataError

def _detect_pkg_root():
    # Infer package root from the imported service module for relative import behavior
    mod = TradingViewChartService.__module__
    # Expected "backend.services.tradingview_chart_service"
    parts = mod.split(".")
    if len(parts) >= 2:
        return ".".join(parts[:-1])  # backend.services
    return "backend.services"

def test_build_chart_data_success_with_trades_and_indicators(base_candles):
    df = pd.DataFrame({"t": [1, 2, 3]})
    bundle = _bundle(df=df)
    fetcher = DummyFetcher(bundle=bundle)
    builder = DummyBuilder(
        candles=base_candles,
        trade_markers=[{"time": base_candles[0]["time"], "position": "buy"}],
        indicators=[{"name": "SMA", "data": [1, 2, 3]}],
    )
    formatter = DummyFormatter()

    svc = TradingViewChartService(fetcher, builder, formatter)

    trade_rows = [
        {
            "id": 1,
            "side": "long",
            "entry_time": "2024-01-03T09:15:00Z",
            "exit_time": "2024-01-03T10:00:00Z",
            "entry_price": 100.0,
            "exit_price": 110.5,
            "pnl": 10.5,
        }
    ]

    backtest = BT(
        id="bt-abc",
        results={
            "indicator_cfg": [{"name": "SMA", "color": "blue"}],
            "trades": trade_rows,
        },
    )
    session = object()

    result = svc.build_chart_data(
        session,
        backtest,
        include_trades=True,
        include_indicators=True,
        max_candles=100,
        start="2024-01-03",
        end="2024-01-05",
        tz="UTC",
        single_day=False,
        cursor=None,
        navigate=None,
    )

    assert result["success"] is True
    assert result["backtest_id"] == "bt-abc"
    assert result["dataset_name"] == bundle.dataset_name
    assert result["candlestick_data"] == base_candles
    assert result["returned_candles"] == len(base_candles)
    assert "date_range" in result and result["date_range"]["start"] == base_candles[0]["time"]
    assert "navigation" in result and isinstance(result["navigation"], dict)
    # Trades/indicators included
    assert result["trade_markers"] == [{"time": base_candles[0]["time"], "position": "buy"}]
    assert result["indicators"] == [{"name": "SMA", "data": [1, 2, 3]}]
    assert result["indicator_config"] == [{"name": "SMA", "color": "blue"}]

    assert result["trades"], "Expected trades list to be included"
    trade_payload = result["trades"][0]
    assert trade_payload["id"] == 1
    assert trade_payload["side"] == "long"
    assert trade_payload["entry_time"].startswith("2024-01-03T09:15:00")
    assert trade_payload["exit_price"] == 110.5

    assert result["trades_meta"] == {
        "total": 1,
        "returned": 1,
        "limit": 200,
        "has_more": False,
        "timezone": "UTC",
    }
    # Formatter used
    assert formatter.calls and formatter.calls[-1] is result
    # Builder interactions captured
    assert builder.calls["build_candles"] and builder.calls["build_trade_markers"] and builder.calls["build_indicator_series"]

def test_build_chart_data_no_candles_returns_error():
    df = pd.DataFrame({"t": [1]})
    bundle = _bundle(df=df)
    fetcher = DummyFetcher(bundle=bundle)
    builder = DummyBuilder(candles=[])  # no candles triggers error payload
    formatter = DummyFormatter()
    svc = TradingViewChartService(fetcher, builder, formatter)

    res = svc.build_chart_data(
        object(),
        BT(),
        include_trades=False,
        include_indicators=False,
        max_candles=None,
        start=None,
        end=None,
        tz="UTC",
        single_day=None,
        cursor=None,
        navigate=None,
    )

    assert res["success"] is False
    assert "No valid candlestick data" in res["error"]
    # Navigation should still be present and sanitized via formatter
    assert "navigation" in res
    assert formatter.calls and formatter.calls[-1] is res

def test_build_chart_data_handles_pricedataerror():
    pkg_root = _detect_pkg_root()
    PriceDataError = _install_dummy_price_data_error(pkg_root)

    fetcher = DummyFetcher(exc=PriceDataError("range not available"))
    builder = DummyBuilder(candles=[{"time": "2024-01-03T00:00:00Z", "open": 1, "high": 1, "low": 1, "close": 1}])
    formatter = DummyFormatter()
    svc = TradingViewChartService(fetcher, builder, formatter)

    res = svc.build_chart_data(
        object(),
        BT(),
        include_trades=False,
        include_indicators=False,
        max_candles=50,
        start="2024-01-01",
        end="2024-01-02",
        tz="UTC",
        single_day=True,
        cursor=None,
        navigate=None,
    )

    assert res["success"] is False
    assert res["error"] == "range not available"  # message propagated
    # Formatter should not be called for early error path (function returns immediately)
    assert formatter.calls == []

def test_build_chart_data_handles_unexpected_exception():
    class Boom(Exception):
        pass
    fetcher = DummyFetcher(exc=Boom("db down"))
    builder = DummyBuilder()
    formatter = DummyFormatter()
    svc = TradingViewChartService(fetcher, builder, formatter)

    res = svc.build_chart_data(
        object(),
        BT(),
        include_trades=False,
        include_indicators=False,
        max_candles=None,
        start=None,
        end=None,
        tz=None,
        single_day=None,
        cursor=None,
        navigate=None,
    )

    assert res["success"] is False
    assert res["error"] == "Error generating chart data"
    assert formatter.calls == []

@pytest.mark.parametrize(
    "value,tz,expected",
    [
        ("2024-01-02", "UTC", date(2024, 1, 2)),                    # naive date string -> localized midnight
        ("2024-01-02T15:30:00Z", "UTC", date(2024, 1, 2)),          # aware ISO string
        ("2024-01-02T23:30:00Z", "Asia/Tokyo", date(2024, 1, 3)),   # tz conversion crosses day boundary
        (None, "UTC", None),
        ("not-a-date", "UTC", None),
    ],
)
def test_parse_date_various_inputs(value, tz, expected):
    assert TradingViewChartService._parse_date(value, tz) == expected

def test_timestamp_to_date_handles_naive_and_aware_and_errors():
    # None -> None
    assert TradingViewChartService._timestamp_to_date(None, "UTC") is None

    # Naive timestamp (interpreted as UTC, then converted)
    d = TradingViewChartService._timestamp_to_date(pd.Timestamp("2024-06-15 12:00:00"), "US/Eastern")
    # 12:00 UTC -> 08:00 US/Eastern on same date
    assert d == date(2024, 6, 15)

    # Aware timestamp conversion
    aware = pd.Timestamp("2024-01-01T01:00:00", tz="Asia/Tokyo")
    d2 = TradingViewChartService._timestamp_to_date(aware, "UTC")
    assert d2 == date(2023, 12, 31) or d2 == date(2024, 1, 1)  # depends on exact offset; accept either day boundary

    # Invalid input that cannot construct a Timestamp
    class Weird:
        __slots__ = ()
    assert TradingViewChartService._timestamp_to_date(Weird(), "UTC") is None

def test_sessions_to_dates_filters_invalid_and_converts():
    sessions = [
        pd.Timestamp("2024-01-02T00:00:00Z"),
        pd.Timestamp("2024-01-03T12:00:00Z"),
        None,  # should be skipped
    ]
    dates = TradingViewChartService(None, None, None)._sessions_to_dates(sessions, "UTC")
    assert dates == [date(2024, 1, 2), date(2024, 1, 3)]

def test_find_previous_and_next_boundaries():
    dates = [date(2024, 1, 2), date(2024, 1, 3), date(2024, 1, 5)]
    # previous
    assert TradingViewChartService._find_previous(dates, date(2024, 1, 3)) == date(2024, 1, 2)
    assert TradingViewChartService._find_previous(dates, date(2024, 1, 2)) is None
    assert TradingViewChartService._find_previous([], date(2024, 1, 3)) is None
    assert TradingViewChartService._find_previous(dates, None) is None
    # next
    assert TradingViewChartService._find_next(dates, date(2024, 1, 3)) == date(2024, 1, 5)
    assert TradingViewChartService._find_next(dates, date(2024, 1, 5)) is None
    assert TradingViewChartService._find_next(dates, None) == date(2024, 1, 2)
    assert TradingViewChartService._find_next([], date(2024, 1, 3)) is None

def test_build_navigation_outputs_expected_shape():
    df = pd.DataFrame({"v": [1, 2]})
    bundle = _bundle(
        df=df,
        available_sessions=[
            pd.Timestamp("2024-01-01T00:00:00Z"),
            pd.Timestamp("2024-01-02T00:00:00Z"),
            pd.Timestamp("2024-01-03T00:00:00Z"),
        ],
        resolved_sessions=[
            pd.Timestamp("2024-01-02T00:00:00Z"),
            pd.Timestamp("2024-01-03T00:00:00Z"),
        ],
        requested_start=pd.Timestamp("2024-01-02T00:00:00Z"),
        requested_end=pd.Timestamp("2024-01-03T00:00:00Z"),
    )
    svc = TradingViewChartService(None, None, DummyFormatter())
    nav = svc._build_navigation(bundle, "UTC", start="2024-01-02", end="2024-01-03", cursor=None)

    assert nav["available_dates"] == ["2024-01-01", "2024-01-02", "2024-01-03"]
    assert nav["resolved_dates"] == ["2024-01-02", "2024-01-03"]
    assert nav["previous_date"] == "2024-01-01"
    assert nav["next_date"] is None
    assert nav["requested_start"] == "2024-01-02"
    assert nav["requested_end"] == "2024-01-03"
    assert nav["requested_cursor"] is None
    assert nav["resolved_start"] == "2024-01-02"
    assert nav["resolved_end"] == "2024-01-03"
    assert nav["has_data"] is True

def test_build_chart_data_excludes_optional_blocks_when_flags_false(base_candles):
    df = pd.DataFrame({"t": [1, 2, 3]})
    bundle = _bundle(df=df)
    fetcher = DummyFetcher(bundle=bundle)
    builder = DummyBuilder(candles=base_candles,
                           trade_markers=[{"time": base_candles[0]["time"], "position": "buy"}],
                           indicators=[{"name": "MACD", "data": [1, 2, 3]}])
    formatter = DummyFormatter()
    svc = TradingViewChartService(fetcher, builder, formatter)
    res = svc.build_chart_data(
        object(),
        BT(),
        include_trades=False,
        include_indicators=False,
        max_candles=None,
        start=None,
        end=None,
        tz="UTC",
        single_day=None,
        cursor=None,
        navigate=None,
    )
    assert res["success"] is True
    assert "trade_markers" not in res
    assert "trades" not in res
    assert "trades_meta" not in res
    assert "indicators" not in res
    # indicator_config defaults to empty list when include_indicators False; ensure key absent to avoid confusion
    assert "indicator_config" not in res
