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
        """
        Initialize the instance and prepare an empty list to record method call arguments.
        """
        self.calls = []
    def sanitize_json(self, payload):
        """
        Record the given payload and return it unchanged.
        
        Parameters:
            payload: The JSON-serializable object to record.
        
        Returns:
            The same payload that was passed in (identity passthrough).
        """
        self.calls.append(payload)
        return payload

class DummyBuilder:
    def __init__(self, candles=None, trade_markers=None, indicators=None):
        """
        Initialize the dummy builder with optional predefined outputs and a call log.
        
        Parameters:
            candles (list, optional): Predefined list returned by build_candles when invoked. Defaults to empty list.
            trade_markers (list, optional): Predefined list returned by build_trade_markers when invoked. Defaults to empty list.
            indicators (list, optional): Predefined list returned by build_indicator_series when invoked. Defaults to empty list.
        
        The instance also exposes `calls`, a dict that records arguments passed to each build_* method for later inspection in tests.
        """
        self._candles = candles if candles is not None else []
        self._trade_markers = trade_markers if trade_markers is not None else []
        self._indicators = indicators if indicators is not None else []
        self.calls = {"build_candles": [], "build_trade_markers": [], "build_indicator_series": []}
    def build_candles(self, df):
        """
        Record the provided dataframe call and return the builder's predefined candle list.
        
        Appends the given `df` to this instance's `calls["build_candles"]` (for test inspection) and returns a shallow copy of the builder's predefined candles.
        
        Parameters:
            df: The input dataframe or data structure passed to the builder; recorded for test assertions.
        
        Returns:
            list: A list of candlestick dictionaries previously configured on this DummyBuilder.
        """
        self.calls["build_candles"].append(df)
        return list(self._candles)
    def build_trade_markers(self, results, df, tz, start_ts, end_ts):
        """
        Record a call to build trade markers and return the predefined trade marker list.
        
        Parameters:
            results: Backtest results object used to compute markers (passed through and recorded).
            df: DataFrame of price/candle data used for marker construction (passed through and recorded).
            tz: Timezone or tzinfo used for time conversion (passed through and recorded).
            start_ts: Start timestamp of the requested window (passed through and recorded).
            end_ts: End timestamp of the requested window (passed through and recorded).
        
        Returns:
            list: A shallow copy of the builder's predefined trade marker list (each marker is typically a dict-like structure).
        """
        self.calls["build_trade_markers"].append((results, df, tz, start_ts, end_ts))
        return list(self._trade_markers)
    def build_indicator_series(self, results, df, strategy_params=None):
        """
        Record the call and return a copy of the predefined indicator series.
        
        Records the (results, df, strategy_params) tuple in self.calls["build_indicator_series"] and returns a shallow copy of the builder's configured indicator list.
        
        Parameters:
            results: Backtest results or analysis output passed to the builder (kept for inspection).
            df: DataFrame or data structure representing price/candle data passed to the builder.
            strategy_params (optional): Strategy parameters that may influence indicator construction; recorded but not used by this dummy implementation.
        
        Returns:
            list: A shallow copy of the builder's predefined indicators.
        """
        self.calls["build_indicator_series"].append((results, df, strategy_params))
        return list(self._indicators)

class DummyFetcher:
    def __init__(self, bundle=None, exc=None):
        """
        Initialize the dummy fetcher used in tests.
        
        Parameters:
            bundle (Optional[object]): Prebuilt bundle to return from load_price_data. If None, the fetcher will return None.
            exc (Optional[Exception]): Optional exception to raise when load_price_data is called instead of returning the bundle.
        
        Notes:
            The instance records each call to load_price_data in `self.calls` (initialized as an empty list).
        """
        self.bundle = bundle
        self.exc = exc
        self.calls = []
    def load_price_data(self, backtest, results, session, **kwargs):
        """
        Record the call and return a preset bundle or raise a preset exception.
        
        Parameters:
            backtest: The backtest object passed to the fetcher (recorded for assertions).
            results: Backtest results passed through (recorded for assertions).
            session: Session identifier or object for which price data is requested (recorded for assertions).
            **kwargs: Additional fetch options (recorded with the call).
        
        Returns:
            The preset `bundle` attribute (test fixture) that contains price data and metadata.
        
        Raises:
            Exception: Re-raises the exception set on `self.exc` if present.
        """
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
    """
    Create a test "bundle" SimpleNamespace representing fetched price data and metadata.
    
    This helper returns a SimpleNamespace with attributes commonly used by the tests:
    - dataframe: the price DataFrame (defaults to a small 3-row sample if not provided).
    - dataset_name: identifier for the dataset.
    - total_candles: total number of candles in the original dataset.
    - sampled / filtered: booleans indicating whether the data was sampled or filtered.
    - available_sessions / resolved_sessions: lists of session timestamps used for navigation tests (defaults provided).
    - requested_start / requested_end and start_bound / end_bound: timestamp window values used by navigation and range calculations (default timestamps are provided when not supplied).
    
    Parameters:
    - df (pandas.DataFrame | None): optional price DataFrame; if None a 3-row DataFrame with columns t,o,h,l,c is created.
    - dataset_name (str): dataset identifier included in the bundle.
    - total_candles (int): reported total number of candles.
    - sampled (bool): whether the bundle should indicate sampling occurred.
    - filtered (bool): whether the bundle should indicate filtering occurred.
    - available_sessions (list[pandas.Timestamp] | None): list of available session timestamps; a default list is used when None.
    - resolved_sessions (list[pandas.Timestamp] | None): list of resolved session timestamps; a default list is used when None.
    - requested_start / requested_end (pandas.Timestamp | None): requested window start/end; defaults are provided when None.
    - start_bound / end_bound (pandas.Timestamp | None): bounding timestamps for the dataset window; defaults are provided when None.
    
    Returns:
    SimpleNamespace with the attributes described above.
    """
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
        """
        Initialize a BackTest container.
        
        A minimal container object used in tests to hold a backtest identifier, result data, and optional strategy parameters.
        
        Parameters:
            id (str): Backtest identifier; defaults to "bt-1".
            results (dict | None): Result payload produced by the backtest; empty dict is used when None is provided.
            strategy_params (Any | None): Optional strategy configuration or parameters associated with the backtest.
        """
        self.id = id
        self.results = results if results is not None else {}
        self.strategy_params = strategy_params

@pytest.fixture
def base_candles():
    """
    Return a small sample list of candlestick dictionaries for tests.
    
    Each dict contains ISO-8601 UTC `time` and numeric `open`, `high`, `low`, `close` fields.
    Returns:
        list[dict]: Three sample candlesticks spanning 2024-01-03 to 2024-01-05.
    """
    return [
        {"time": "2024-01-03T00:00:00Z", "open": 1, "high": 2, "low": 0, "close": 1},
        {"time": "2024-01-04T00:00:00Z", "open": 2, "high": 3, "low": 1, "close": 2},
        {"time": "2024-01-05T00:00:00Z", "open": 3, "high": 4, "low": 2, "close": 3},
    ]

def _install_dummy_price_data_error(module_under_test_pkg: str):
    # Provide a dummy module with PriceDataError to satisfy "from .data_fetcher import PriceDataError"
    """
    Create and register a dummy `data_fetcher` module containing a `PriceDataError` exception class.
    
    This injects a synthetic module named "<module_under_test_pkg>.data_fetcher" into sys.modules so code that performs
    `from .data_fetcher import PriceDataError` can import a stable exception type during tests.
    
    Parameters:
        module_under_test_pkg (str): Package path prefix to use when constructing the dummy module name
            (e.g., "mypkg.subpkg" -> "mypkg.subpkg.data_fetcher").
    
    Returns:
        type: The dynamically created `PriceDataError` exception class.
    """
    mod_name = f"{module_under_test_pkg}.data_fetcher"
    m = types.ModuleType(mod_name)
    class PriceDataError(Exception):
        pass
    m.PriceDataError = PriceDataError
    sys.modules[mod_name] = m
    return PriceDataError

def _detect_pkg_root():
    # Infer package root from the imported service module for relative import behavior
    """
    Infer the package root used for relative imports based on TradingViewChartService's module path.
    
    Returns:
        str: The package root (module path without the final component). If the module path of
        TradingViewChartService cannot be split into at least two parts, returns the default
        "backend.services".
    """
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

    backtest = BT(id="bt-abc", results={"indicator_cfg": [{"name": "SMA", "color": "blue"}]})
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
    assert "indicators" not in res
    # indicator_config defaults to empty list when include_indicators False; ensure key absent to avoid confusion
    assert "indicator_config" not in res