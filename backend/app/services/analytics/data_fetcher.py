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
from datetime import date, datetime
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

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
    available_sessions: List[pd.Timestamp]
    resolved_sessions: List[pd.Timestamp]
    requested_start: Optional[pd.Timestamp]
    requested_end: Optional[pd.Timestamp]


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
        single_day: Optional[bool] = None,
        cursor: Optional[str] = None,
        navigate: Optional[str] = None,
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

        local_tz = tz or "UTC"

        dataframe = self._normalize_dataframe(dataframe, tz)
        session_bounds, available_sessions = self._build_session_metadata(dataframe, local_tz)

        (
            start_override,
            end_override,
            target_sessions,
            anchor_utc,
        ) = self._resolve_navigation_bounds(
            session_bounds=session_bounds,
            available_sessions=available_sessions,
            local_tz=local_tz,
            start=start,
            end=end,
            cursor=cursor,
            navigate=navigate,
            single_day=single_day,
        )

        navigation_requested = (navigate or "").strip().lower() in {"next", "previous", "current"}

        filter_start = start_override if start_override is not None else start
        filter_end = end_override if end_override is not None else end

        (
            dataframe,
            filtered,
            start_bound,
            end_bound,
            requested_start,
            requested_end,
        ) = self._apply_date_filter(
            dataframe,
            start=filter_start,
            end=filter_end,
            tz=tz,
        )

        if navigation_requested and not target_sessions:
            dataframe = dataframe.iloc[0:0].copy()
            filtered = True
            start_bound = None
            end_bound = None
            if anchor_utc is not None:
                requested_start = requested_start or anchor_utc
                if requested_end is None:
                    requested_end = anchor_utc

        resolved_sessions = (
            target_sessions if target_sessions else self._extract_sessions(dataframe, local_tz)
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
            available_sessions=available_sessions,
            resolved_sessions=resolved_sessions,
            requested_start=requested_start,
            requested_end=requested_end,
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
        # Preserve the original sequential position so indicators can be aligned after filtering
        df["_source_index"] = df.index

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

    def _build_session_metadata(
        self,
        df: pd.DataFrame,
        local_tz: str,
    ) -> Tuple[Dict[pd.Timestamp, Tuple[pd.Timestamp, pd.Timestamp]], List[pd.Timestamp]]:
        """Return per-session UTC bounds and sorted session list in local timezone."""

        if df.empty or "timestamp_utc" not in df.columns:
            return {}, []

        df = df.copy()
        df["_session_local"] = df["timestamp_utc"].dt.tz_convert(local_tz).dt.normalize()

        session_bounds: Dict[pd.Timestamp, Tuple[pd.Timestamp, pd.Timestamp]] = {}
        for session_key, group in df.groupby("_session_local", sort=True):
            if group.empty:
                continue
            try:
                session_ts = pd.Timestamp(session_key)
                if session_ts.tzinfo is None:
                    session_ts = session_ts.tz_localize(local_tz)
                else:
                    session_ts = session_ts.tz_convert(local_tz)

                start_ts = pd.Timestamp(group["timestamp_utc"].min())
                end_ts = pd.Timestamp(group["timestamp_utc"].max())
                session_bounds[session_ts] = (start_ts, end_ts)
            except Exception:
                continue

        sessions = sorted(session_bounds.keys())
        return session_bounds, sessions

    def _resolve_navigation_bounds(
        self,
        *,
        session_bounds: Dict[pd.Timestamp, Tuple[pd.Timestamp, pd.Timestamp]],
        available_sessions: List[pd.Timestamp],
        local_tz: str,
        start: Optional[str],
        end: Optional[str],
        cursor: Optional[str],
        navigate: Optional[str],
        single_day: Optional[bool],
    ) -> Tuple[
        Optional[pd.Timestamp],
        Optional[pd.Timestamp],
        List[pd.Timestamp],
        Optional[pd.Timestamp],
    ]:
        """Determine overrides for navigation-based requests."""

        if not available_sessions:
            return None, None, [], None

        navigation = (navigate or "").strip().lower()
        navigation_requested = navigation in {"next", "previous", "current"}
        single_day_flag = bool(single_day)

        available_dates = [self._session_to_date(session, local_tz) for session in available_sessions]

        anchor_date = self._determine_anchor_date(
            cursor=cursor,
            start=start,
            end=end,
            available_dates=available_dates,
            local_tz=local_tz,
        )
        anchor_utc = self._normalize_bound(cursor or start, local_tz, is_start=True)

        target_session: Optional[pd.Timestamp] = None

        if navigation_requested:
            if anchor_date is None and available_dates:
                anchor_date = available_dates[0]

            target_date: Optional[date] = None
            if navigation == "next":
                target_date = self._next_date(available_dates, anchor_date)
            elif navigation == "previous":
                target_date = self._previous_date(available_dates, anchor_date)
            else:  # current
                if anchor_date in available_dates:
                    target_date = anchor_date
                else:
                    target_date = self._next_date(available_dates, anchor_date)
                    if target_date is None:
                        target_date = self._previous_date(available_dates, anchor_date)

            if target_date is not None:
                target_session = self._session_by_date(available_sessions, target_date, local_tz)
        elif single_day_flag:
            candidate_date = self._parse_date(cursor or start, local_tz)
            if candidate_date and candidate_date in available_dates:
                target_session = self._session_by_date(available_sessions, candidate_date, local_tz)

        if target_session is None:
            return None, None, [], anchor_utc

        start_end = session_bounds.get(target_session)
        if not start_end:
            return None, None, [], anchor_utc

        start_override, end_override = start_end
        return start_override, end_override, [target_session], start_override

    def _determine_anchor_date(
        self,
        *,
        cursor: Optional[str],
        start: Optional[str],
        end: Optional[str],
        available_dates: List[date],
        local_tz: str,
    ) -> Optional[date]:
        candidates = [cursor, start, end]
        for candidate in candidates:
            parsed = self._parse_date(candidate, local_tz)
            if parsed is not None:
                return parsed
        return available_dates[0] if available_dates else None

    def _parse_date(self, value: Optional[str], local_tz: str) -> Optional[date]:
        if not value:
            return None
        try:
            timestamp = pd.to_datetime(value)
            if isinstance(value, str) and len(value) == 10:
                timestamp = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)

            if timestamp.tzinfo is None:
                timestamp = timestamp.tz_localize(local_tz)
            else:
                timestamp = timestamp.tz_convert(local_tz)

            return timestamp.date()
        except Exception:
            return None

    def _session_to_date(self, session: pd.Timestamp, local_tz: str) -> date:
        try:
            ts = pd.Timestamp(session)
            if ts.tzinfo is None:
                ts = ts.tz_localize(local_tz)
            else:
                ts = ts.tz_convert(local_tz)
            return ts.date()
        except Exception:
            return pd.Timestamp(session).date()

    def _session_by_date(
        self,
        sessions: List[pd.Timestamp],
        target_date: date,
        local_tz: str,
    ) -> Optional[pd.Timestamp]:
        for session in sessions:
            if self._session_to_date(session, local_tz) == target_date:
                return session
        return None

    @staticmethod
    def _next_date(available_dates: List[date], anchor: Optional[date]) -> Optional[date]:
        if not available_dates:
            return None
        if anchor is None:
            return available_dates[0]

        idx = pd.Index(available_dates).searchsorted(anchor, side="right")
        if idx >= len(available_dates):
            return None
        return available_dates[idx]

    @staticmethod
    def _previous_date(available_dates: List[date], anchor: Optional[date]) -> Optional[date]:
        if not available_dates or anchor is None:
            return None

        idx = pd.Index(available_dates).searchsorted(anchor, side="left")
        if idx <= 0:
            return None
        return available_dates[idx - 1]

    def _normalize_bound(
        self,
        value: Optional[Union[str, pd.Timestamp]],
        tz: str,
        *,
        is_start: bool,
    ) -> Optional[pd.Timestamp]:
        if value is None:
            return None

        if isinstance(value, pd.Timestamp):
            bound = pd.Timestamp(value)
            if bound.tzinfo is None:
                bound = bound.tz_localize("UTC")
            return bound.tz_convert("UTC")

        return self._parse_bound(value, tz, is_start=is_start)

    def _apply_date_filter(
        self,
        df: pd.DataFrame,
        *,
        start: Optional[Union[str, pd.Timestamp]],
        end: Optional[Union[str, pd.Timestamp]],
        tz: Optional[str],
    ) -> Tuple[
        pd.DataFrame,
        bool,
        Optional[pd.Timestamp],
        Optional[pd.Timestamp],
        Optional[pd.Timestamp],
        Optional[pd.Timestamp],
    ]:
        """Apply optional start/end filters and return resulting metadata."""

        if start is None and end is None:
            return df.reset_index(drop=True), False, None, None, None, None

        local_tz = tz or "UTC"
        requested_start = self._normalize_bound(start, local_tz, is_start=True)
        requested_end = self._normalize_bound(end, local_tz, is_start=False)

        start_ts = requested_start if requested_start is not None else df["timestamp_utc"].min()
        end_ts = requested_end if requested_end is not None else df["timestamp_utc"].max()

        if start_ts is None:
            start_ts = df["timestamp_utc"].min()
        if end_ts is None:
            end_ts = df["timestamp_utc"].max()

        mask = (df["timestamp_utc"] >= start_ts) & (df["timestamp_utc"] <= end_ts)
        filtered_df = df.loc[mask].copy().reset_index(drop=True)

        return filtered_df, True, start_ts, end_ts, requested_start, requested_end

    def _extract_sessions(self, df: pd.DataFrame, local_tz: str) -> List[pd.Timestamp]:
        if df is None or df.empty:
            return []

        if "_session_local" in df.columns:
            normalized = df["_session_local"].dropna().unique()
        elif "timestamp_utc" in df.columns:
            normalized = df["timestamp_utc"].dt.tz_convert(local_tz).dt.normalize().dropna().unique()
        else:
            return []

        sessions: List[pd.Timestamp] = []
        for value in normalized:
            ts = pd.Timestamp(value)
            if ts.tzinfo is None:
                ts = ts.tz_localize(local_tz)
            else:
                ts = ts.tz_convert(local_tz)
            sessions.append(ts)

        sessions.sort()
        return sessions

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
