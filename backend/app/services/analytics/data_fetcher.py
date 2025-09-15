"""Data loading helpers for analytics services.

This module centralizes all logic related to retrieving and normalizing the
price series used for analytics visualizations.  The legacy analytics service
contained a large, monolithic implementation that mixed data access,
filtering, timezone handling, sampling, and chart shaping.  The
``AnalyticsDataFetcher`` below keeps each concern focused and testable while
exposing a single high-level method used by the analytics services.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import pandas as pd

from backend.app.database.models import Backtest, Dataset

from .data_formatter import DataFormatter

logger = logging.getLogger(__name__)


class PriceDataError(Exception):
    """Raised when price data required for analytics cannot be prepared."""


@dataclass
class PriceDataBundle:
    """Container for normalized price data and associated metadata."""

    dataframe: pd.DataFrame
    dataset_name: str
    total_candles: int
    filtered: bool
    sampled: bool
    start_bound: Optional[pd.Timestamp]
    end_bound: Optional[pd.Timestamp]
    source: str


class AnalyticsDataFetcher:
    """Retrieve and normalize dataset and backtest price data."""

    def __init__(self, dataset_service_factory: Optional[Callable[[], Any]] = None) -> None:
        self._dataset_service_factory = dataset_service_factory

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def load_price_data(
        self,
        backtest: Backtest,
        results: Dict[str, Any],
        session,
        *,
        tz: Optional[str] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        max_candles: Optional[int] = None,
    ) -> PriceDataBundle:
        """Load and normalize price data used for TradingView charts.

        The loader prefers fetching the original dataset rows to preserve the
        true OHLC patterns.  It falls back to serialized price or market data
        in the stored results and, as a last resort, synthesizes candles from
        the equity curve to avoid breaking the UI entirely.
        """

        records, dataset_name, source = self._extract_price_records(backtest, results, session)

        dataframe = pd.DataFrame(records)
        if dataframe.empty:
            raise PriceDataError("Empty price data")

        dataframe = self._normalize_dataframe(dataframe, tz)

        dataframe, filtered, start_bound, end_bound = self._apply_date_filter(
            dataframe, start=start, end=end, tz=tz
        )

        total_candles = int(len(dataframe))

        dataframe, sampled = self._downsample(dataframe, max_candles)

        return PriceDataBundle(
            dataframe=dataframe,
            dataset_name=dataset_name,
            total_candles=total_candles,
            filtered=filtered,
            sampled=sampled,
            start_bound=start_bound,
            end_bound=end_bound,
            source=source,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _extract_price_records(
        self,
        backtest: Backtest,
        results: Dict[str, Any],
        session,
    ) -> Tuple[List[Dict[str, Any]], str, str]:
        """Determine the best available source of price data."""

        dataset_name = "Unknown Dataset"

        if backtest.dataset_id:
            dataset = session.query(Dataset).filter(Dataset.id == backtest.dataset_id).first()
            if dataset:
                dataset_name = dataset.name or dataset_name

            try:
                dataset_service = self._get_dataset_service()
                dataset_payload = dataset_service.get_dataset_data(backtest.dataset_id)
                if dataset_payload and dataset_payload.get("success") and dataset_payload.get("data"):
                    logger.debug(
                        "Loaded %s rows of dataset data for backtest_id=%s", len(dataset_payload["data"]), backtest.id
                    )
                    return dataset_payload["data"], dataset_name, "dataset"
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning(
                    "Failed to load dataset %s for backtest %s: %s",
                    backtest.dataset_id,
                    backtest.id,
                    exc,
                )

        if results.get("price_data"):
            price_data = results.get("price_data")
            logger.debug("Loaded %s price_data rows from backtest results", len(price_data))
            return price_data, dataset_name, "results.price_data"

        if results.get("market_data"):
            market_data = results.get("market_data")
            logger.debug("Loaded %s market_data rows from backtest results", len(market_data))
            return market_data, dataset_name, "results.market_data"

        equity_curve = results.get("equity_curve") or []
        if equity_curve:
            simulated = self._simulate_price_data_from_equity(equity_curve)
            logger.debug(
                "Simulated %s candles from equity curve for backtest_id=%s", len(simulated), backtest.id
            )
            return simulated, "Simulated from Equity Curve", "simulated"

        raise PriceDataError("No price data, market data, or equity curve available for this backtest")

    def _normalize_dataframe(self, df: pd.DataFrame, tz: Optional[str]) -> pd.DataFrame:
        """Normalize naming, ordering, and timezone information."""

        mapping = DataFormatter.get_column_mapping(df.columns.tolist())
        required = ["timestamp", "open", "high", "low", "close"]
        missing = [col for col in required if col not in mapping]
        if missing:
            raise PriceDataError(
                f"Missing required columns: {missing}. Available columns: {list(df.columns)}"
            )

        rename_map = {mapping[key]: key for key in required if key in mapping}
        df = df.rename(columns=rename_map)

        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        df = df.dropna(subset=["timestamp"])
        df = df.sort_values("timestamp").reset_index(drop=True)

        if df.empty:
            raise PriceDataError("No valid data after timestamp processing")

        df["timestamp_utc"] = self._to_utc(df["timestamp"], tz)

        # Ensure the timestamp conversion succeeded; fall back to naive timestamps if needed
        if df["timestamp_utc"].isna().any():
            df["timestamp_utc"] = df["timestamp"].dt.tz_localize("UTC")

        return df

    @staticmethod
    def _to_utc(series: pd.Series, tz: Optional[str]) -> pd.Series:
        """Return a timezone-aware UTC series from arbitrary timestamp input."""

        try:
            if hasattr(series.dt, "tz") and series.dt.tz is not None:
                return series.dt.tz_convert("UTC")
            if tz:
                return series.dt.tz_localize(tz, nonexistent="shift_forward", ambiguous="infer").dt.tz_convert("UTC")
            return series.dt.tz_localize("UTC")
        except Exception:
            # Fallback: treat timestamps as UTC without localization to keep pipeline running
            logger.debug("Falling back to naive UTC localization for price data timestamps")
            return series.dt.tz_localize("UTC", nonexistent="shift_forward", ambiguous="infer")

    def _apply_date_filter(
        self,
        df: pd.DataFrame,
        *,
        start: Optional[str],
        end: Optional[str],
        tz: Optional[str],
    ) -> Tuple[pd.DataFrame, bool, Optional[pd.Timestamp], Optional[pd.Timestamp]]:
        """Apply optional start/end filters and return resulting metadata."""

        if not start and not end:
            return df.reset_index(drop=True), False, None, None

        local_tz = tz or "UTC"
        start_ts = self._parse_bound(start, local_tz, is_start=True)
        end_ts = self._parse_bound(end, local_tz, is_start=False)

        if start_ts is None:
            start_ts = df["timestamp_utc"].min()
        if end_ts is None:
            end_ts = df["timestamp_utc"].max()

        mask = (df["timestamp_utc"] >= start_ts) & (df["timestamp_utc"] <= end_ts)
        filtered_df = df.loc[mask].copy().reset_index(drop=True)

        return filtered_df, True, start_ts, end_ts

    @staticmethod
    def _parse_bound(value: Optional[str], tz: str, *, is_start: bool) -> Optional[pd.Timestamp]:
        if not value:
            return None

        try:
            bound = pd.to_datetime(value)
            if isinstance(value, str) and len(value) == 10:
                if is_start:
                    bound = bound.replace(hour=0, minute=0, second=0, microsecond=0)
                else:
                    bound = bound.replace(hour=23, minute=59, second=59, microsecond=999000)

            if bound.tzinfo is None:
                try:
                    bound = bound.tz_localize(tz)
                except Exception:
                    # Use DatetimeIndex to leverage broader localization options
                    localized = (
                        pd.DatetimeIndex([bound])
                        .tz_localize(tz, nonexistent="shift_forward", ambiguous="infer")
                    )
                    bound = localized[0]

            return bound.tz_convert("UTC")
        except Exception:
            logger.warning("Failed to parse date bound '%s' using tz %s", value, tz)
            return None

    @staticmethod
    def _downsample(df: pd.DataFrame, max_candles: Optional[int]) -> Tuple[pd.DataFrame, bool]:
        if not max_candles or len(df) <= max_candles:
            return df.reset_index(drop=True), False

        step = max(1, len(df) // max_candles)
        return df.iloc[::step].copy().reset_index(drop=True), True

    @staticmethod
    def _simulate_price_data_from_equity(equity_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Simulate an OHLC series from an equity curve as a last resort."""

        simulated: List[Dict[str, Any]] = []
        base_date = datetime(2025, 1, 1, 9, 15)

        for idx, point in enumerate(equity_data):
            try:
                timestamp_raw = point.get("timestamp") or point.get("time") or str(idx)
                timestamp = pd.to_datetime(timestamp_raw, errors="coerce")
                if pd.isna(timestamp):
                    timestamp = base_date + pd.Timedelta(minutes=idx)

                equity_value = float(point.get("equity") or point.get("value") or 100_000)
                base_price = 24_000
                price_change = (equity_value - 100_000) / 1_000
                price = base_price + price_change
                volatility = abs(price) * 0.001

                simulated.append(
                    {
                        "timestamp": timestamp.isoformat(),
                        "open": float(price + (volatility * 0.5)),
                        "high": float(price + volatility),
                        "low": float(price - volatility),
                        "close": float(price),
                    }
                )
            except Exception:
                continue

        return simulated

    def _get_dataset_service(self):
        if self._dataset_service_factory:
            return self._dataset_service_factory()

        from backend.app.services.dataset_service import DatasetService  # Local import to avoid cycles

        return DatasetService()
