"""Utilities for converting analytics data into TradingView friendly formats."""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

from .data_formatter import DataFormatter

logger = logging.getLogger(__name__)


class TradingViewBuilder:
    """Build charts, markers, and indicator payloads for the frontend."""

    def __init__(self) -> None:
        self.formatter = DataFormatter()
        self._fallback_colors = {
            "sma": "#2196F3",
            "ema": "#FF9800",
            "bb_upper": "#4CAF50",
            "bb_lower": "#4CAF50",
            "bb_middle": "#4CAF50",
            "rsi": "#9C27B0",
            "macd": "#FF5722",
            "support": "#00BCD4",
            "resistance": "#E91E63",
            "bollinger_upper": "#4CAF50",
            "bollinger_lower": "#4CAF50",
            "moving_average": "#FFC107",
        }
        self._css_to_hex = {
            "blue": "#1E90FF",
            "red": "#EF4444",
            "green": "#22C55E",
            "orange": "#F59E0B",
            "purple": "#A855F7",
            "cyan": "#06B6D4",
            "pink": "#EC4899",
            "amber": "#F59E0B",
            "teal": "#14B8A6",
            "indigo": "#6366F1",
            "yellow": "#EAB308",
            "gray": "#6B7280",
        }

    # ------------------------------------------------------------------
    # Candlestick helpers
    # ------------------------------------------------------------------
    def build_candles(self, df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Convert normalized OHLC data into TradingView candle format."""

        candles: List[Dict[str, Any]] = []

        for _, row in df.iterrows():
            try:
                timestamp = row.get("timestamp_utc", row.get("timestamp"))
                epoch = int(pd.Timestamp(timestamp).timestamp())
                candles.append(
                    {
                        "time": epoch,
                        "open": float(row["open"]),
                        "high": float(row["high"]),
                        "low": float(row["low"]),
                        "close": float(row["close"]),
                    }
                )
            except (TypeError, ValueError):
                continue

        return candles

    # ------------------------------------------------------------------
    # Trade helpers
    # ------------------------------------------------------------------
    def build_trade_markers(
        self,
        results: Dict[str, Any],
        price_df: pd.DataFrame,
        *,
        tz: Optional[str] = None,
        start_ts: Optional[pd.Timestamp] = None,
        end_ts: Optional[pd.Timestamp] = None,
    ) -> List[Dict[str, Any]]:
        """Create entry/exit markers compatible with Lightweight Charts."""

        trades = results.get("trades") or results.get("trade_log") or []
        if not trades:
            return []

        markers: List[Dict[str, Any]] = []
        trades_df = pd.DataFrame(trades)
        timezone = tz or "UTC"

        for _, trade in trades_df.iterrows():
            try:
                entry_time_raw = trade.get("entry_time")
                if entry_time_raw:
                    entry_time = pd.to_datetime(entry_time_raw, errors="coerce")
                    if pd.isna(entry_time):
                        continue
                    if entry_time.tzinfo is None:
                        entry_time = entry_time.tz_localize(timezone, nonexistent="shift_forward", ambiguous="infer")
                    entry_time = entry_time.tz_convert("UTC")

                    direction_raw = trade.get("direction", trade.get("side", "unknown"))
                    direction = str(direction_raw).lower() if direction_raw is not None else "unknown"

                    markers.append(
                        {
                            "time": int(entry_time.timestamp()),
                            "position": "belowBar",
                            "color": "#26a69a" if direction == "long" else "#ef5350",
                            "shape": "arrowUp" if direction == "long" else "arrowDown",
                            "text": f"Entry {direction.upper()}",
                            "size": 1,
                        }
                    )

                exit_time_raw = trade.get("exit_time")
                if exit_time_raw and pd.notna(exit_time_raw):
                    exit_time = pd.to_datetime(exit_time_raw, errors="coerce")
                    if pd.isna(exit_time):
                        continue
                    if exit_time.tzinfo is None:
                        exit_time = exit_time.tz_localize(timezone, nonexistent="shift_forward", ambiguous="infer")
                    exit_time = exit_time.tz_convert("UTC")

                    pnl_raw = trade.get("pnl", trade.get("profit_loss", 0))
                    try:
                        pnl_value = float(pnl_raw)
                    except Exception:
                        pnl_value = 0.0

                    markers.append(
                        {
                            "time": int(exit_time.timestamp()),
                            "position": "aboveBar",
                            "color": "#26a69a" if pnl_value > 0 else "#ef5350",
                            "shape": "circle",
                            "text": f"Exit: ${pnl_value:+.0f}",
                            "size": 1,
                        }
                    )
            except Exception:  # pragma: no cover - defensive safety
                continue

        if not markers:
            return []

        if start_ts is not None or end_ts is not None:
            start_epoch = int(pd.Timestamp(start_ts).timestamp()) if start_ts is not None else None
            end_epoch = int(pd.Timestamp(end_ts).timestamp()) if end_ts is not None else None
            filtered_markers = []
            for marker in markers:
                timestamp = marker.get("time")
                if timestamp is None:
                    continue
                if start_epoch is not None and timestamp < start_epoch:
                    continue
                if end_epoch is not None and timestamp > end_epoch:
                    continue
                filtered_markers.append(marker)
            markers = filtered_markers

        return markers

    # ------------------------------------------------------------------
    # Indicator helpers
    # ------------------------------------------------------------------
    def build_indicator_series(
        self,
        results: Dict[str, Any],
        price_df: pd.DataFrame,
        strategy_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Return indicator overlays formatted for Lightweight Charts."""

        indicators_data = (results.get("indicators") or {}) if isinstance(results, dict) else {}

        cfg_list = results.get("indicator_cfg") if isinstance(results, dict) else None
        cfg_list = cfg_list if isinstance(cfg_list, list) else []
        cfg_color_map: Dict[str, str] = {}
        cfg_label_map: Dict[str, str] = {}
        cfg_panel_map: Dict[str, Optional[int]] = {}
        cfg_style_map: Dict[str, Optional[str]] = {}
        cfg_width_map: Dict[str, Optional[float]] = {}
        for cfg in cfg_list:
            try:
                column = str(cfg.get("column", "") or "").strip()
                label = str(cfg.get("label", "") or "").strip()
                color = str(cfg.get("color", "") or "").strip()
                panel = cfg.get("panel")
                style = cfg.get("style") or cfg.get("type")
                width = cfg.get("line_width") or cfg.get("width")
                if column:
                    cfg_color_map[column] = color
                    if label:
                        cfg_label_map[column] = label
                    cfg_panel_map[column] = panel
                    cfg_style_map[column] = style
                    cfg_width_map[column] = width
                if label and color:
                    cfg_color_map[label] = color
                if label:
                    cfg_panel_map[label] = panel
                    cfg_style_map[label] = style
                    cfg_width_map[label] = width
            except Exception:
                continue

        if not indicators_data:
            indicators_data = self._infer_indicators(price_df, strategy_params)

        indicators: List[Dict[str, Any]] = []
        for indicator_name, indicator_values in indicators_data.items():
            try:
                if indicator_values is None:
                    continue

                if isinstance(indicator_values, (list, tuple)) and not indicator_values:
                    continue

                line_data = self._build_indicator_line(price_df, indicator_values)
                if not line_data:
                    continue

                color = self._resolve_indicator_color(indicator_name, cfg_color_map, cfg_label_map)
                label = cfg_label_map.get(indicator_name, indicator_name)
                panel = self._resolve_indicator_panel(indicator_name, cfg_panel_map)
                style = self._resolve_indicator_style(indicator_name, cfg_style_map)
                width = self._resolve_indicator_width(indicator_name, cfg_width_map)

                indicator_payload: Dict[str, Any] = {
                    "name": label,
                    "color": color,
                    "data": line_data,
                    "panel": panel,
                    "style": style,
                    "source": indicator_name,
                }
                if width is not None:
                    indicator_payload["lineWidth"] = width

                indicators.append(indicator_payload)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.debug("Failed to prepare indicator %s: %s", indicator_name, exc)
                continue

        return indicators

    # ------------------------------------------------------------------
    # Indicator internals
    # ------------------------------------------------------------------
    def _infer_indicators(
        self,
        price_df: pd.DataFrame,
        strategy_params: Optional[Dict[str, Any]],
    ) -> Dict[str, Iterable[float]]:
        if price_df.empty or "close" not in price_df.columns:
            return {}

        close = price_df["close"].astype(float)
        params = strategy_params or {}

        def to_int(value: Any, default: Optional[int]) -> Optional[int]:
            try:
                return int(value)
            except Exception:
                return default

        indicators: Dict[str, Iterable[float]] = {}

        ema_fast = params.get("ema_fast") or params.get("ema_short") or params.get("fast_ema") or params.get("ema_period")
        ema_slow = params.get("ema_slow") or params.get("ema_long") or params.get("slow_ema")
        sma_period = params.get("sma_period") or params.get("moving_average_period")
        rsi_period = params.get("rsi_period") or params.get("rsi")
        bb_period = params.get("bb_period") or params.get("bollinger_period")
        bb_std = params.get("bb_std") or params.get("bollinger_std") or 2
        macd_fast = params.get("macd_fast")
        macd_slow = params.get("macd_slow")
        macd_signal = params.get("macd_signal")

        if ema_fast:
            n = to_int(ema_fast, 12) or 12
            indicators["ema_fast"] = close.ewm(span=n, adjust=False).mean()
        if ema_slow:
            n = to_int(ema_slow, 26) or 26
            indicators["ema_slow"] = close.ewm(span=n, adjust=False).mean()
        if sma_period:
            n = to_int(sma_period, 20) or 20
            indicators["sma"] = close.rolling(window=n, min_periods=1).mean()
        if bb_period:
            n = to_int(bb_period, 20) or 20
            k = float(bb_std) if bb_std is not None else 2.0
            ma = close.rolling(window=n, min_periods=1).mean()
            sd = close.rolling(window=n, min_periods=1).std(ddof=0)
            indicators["bb_upper"] = ma + k * sd
            indicators["bb_middle"] = ma
            indicators["bb_lower"] = ma - k * sd
        if rsi_period:
            n = to_int(rsi_period, 14) or 14
            delta = close.diff()
            gain = delta.where(delta > 0, 0.0)
            loss = -delta.where(delta < 0, 0.0)
            avg_gain = gain.rolling(window=n, min_periods=n).mean()
            avg_loss = loss.rolling(window=n, min_periods=n).mean().replace(0, 1e-12)
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            indicators["rsi"] = rsi
        if macd_fast and macd_slow:
            fast_period = to_int(macd_fast, 12) or 12
            slow_period = to_int(macd_slow, 26) or 26
            macd_line = close.ewm(span=fast_period, adjust=False).mean() - close.ewm(span=slow_period, adjust=False).mean()
            indicators["macd"] = macd_line
            if macd_signal:
                signal_period = to_int(macd_signal, 9) or 9
                indicators["macd_signal"] = macd_line.ewm(span=signal_period, adjust=False).mean()

        if not indicators:
            indicators["sma_20"] = close.rolling(window=20, min_periods=1).mean()
            indicators["sma_50"] = close.rolling(window=50, min_periods=1).mean()

        return indicators

    def _build_indicator_line(self, price_df: pd.DataFrame, values: Iterable[Any]) -> List[Dict[str, Any]]:
        data: List[Dict[str, Any]] = []
        for idx, value in enumerate(values):
            if idx >= len(price_df):
                break
            if pd.isna(value):
                continue
            row = price_df.iloc[idx]
            timestamp = row.get("timestamp_utc", row.get("timestamp"))
            try:
                data.append(
                    {
                        "time": int(pd.Timestamp(timestamp).timestamp()),
                        "value": float(value),
                    }
                )
            except (TypeError, ValueError):
                continue
        return data

    def _resolve_indicator_color(
        self,
        indicator_name: str,
        cfg_color_map: Dict[str, str],
        cfg_label_map: Dict[str, str],
    ) -> str:
        explicit = cfg_color_map.get(indicator_name)
        if not explicit:
            label = cfg_label_map.get(indicator_name)
            if label:
                explicit = cfg_color_map.get(label)

        if explicit:
            lowered = explicit.lower()
            if lowered in self._css_to_hex:
                return self._css_to_hex[lowered]
            return explicit

        key = indicator_name.lower()
        if "ema" in key:
            key = "ema"
        elif "sma" in key or "ma" in key:
            key = "sma"

        return self._fallback_colors.get(key, "#666666")

    def _resolve_indicator_panel(
        self,
        indicator_name: str,
        cfg_panel_map: Dict[str, Optional[int]],
    ) -> int:
        panel = cfg_panel_map.get(indicator_name)
        if panel is not None:
            try:
                return int(panel)
            except (TypeError, ValueError):
                pass

        name = indicator_name.lower()
        if any(token in name for token in ("stoch", "rsi", "macd")):
            return 2

        return 1

    def _resolve_indicator_style(
        self,
        indicator_name: str,
        cfg_style_map: Dict[str, Optional[str]],
    ) -> str:
        style = cfg_style_map.get(indicator_name)
        if style:
            return str(style)

        name = indicator_name.lower()
        if "band" in name or "boll" in name:
            return "dashed"

        return "solid"

    def _resolve_indicator_width(
        self,
        indicator_name: str,
        cfg_width_map: Dict[str, Optional[float]],
    ) -> Optional[float]:
        width = cfg_width_map.get(indicator_name)
        if width is None:
            return None
        try:
            return float(width)
        except (TypeError, ValueError):
            return None
