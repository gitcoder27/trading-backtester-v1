"""Dataset analysis helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd


@dataclass
class DatasetAnalysis:
    """Structured representation of dataset analysis results."""

    rows_count: int
    columns: List[str]
    timeframe: str
    start_date: Optional[datetime]
    end_date: Optional[datetime]
    missing_data_pct: float
    quality_score: float
    has_gaps: bool
    timezone: str
    quality_checks: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "rows_count": self.rows_count,
            "columns": self.columns,
            "timeframe": self.timeframe,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "missing_data_pct": self.missing_data_pct,
            "quality_score": self.quality_score,
            "has_gaps": self.has_gaps,
            "timezone": self.timezone,
            "quality_checks": self.quality_checks,
        }


class DatasetAnalyzer:
    """Perform quality and metadata analysis on CSV datasets."""

    def analyze(self, file_path: Path) -> DatasetAnalysis:
        try:
            df = pd.read_csv(file_path)
        except Exception as exc:  # pragma: no cover - pandas error formatting
            raise ValueError(f"Failed to analyze dataset: {exc}") from exc

        timestamp_col = self._detect_timestamp_column(df)
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None
        timeframe = "unknown"
        timezone_info = "unknown"

        if timestamp_col:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            df = df.sort_values(timestamp_col)
            start_date = df[timestamp_col].min()
            end_date = df[timestamp_col].max()
            timeframe = self._detect_timeframe(df[timestamp_col])
            timezone_info = self._detect_timezone(df[timestamp_col])

        quality_checks = {
            "has_timestamp": timestamp_col is not None,
            "required_columns": self._check_required_columns(df),
            "missing_data": self._check_missing_data(df),
            "data_types": self._check_data_types(df),
            "timestamp_gaps": self._check_timestamp_gaps(df, timestamp_col)
            if timestamp_col
            else {"has_gaps": False, "gap_count": 0},
            "outliers": self._check_outliers(df),
            "duplicates": self._check_duplicates(df, timestamp_col),
        }

        quality_score = self._calculate_quality_score(quality_checks)
        missing_data_pct = (
            df.isnull().sum().sum() / (len(df) * len(df.columns) or 1)
        ) * 100

        if not quality_checks["required_columns"]["has_all_required"]:
            raise ValueError("Dataset missing required OHLC columns")

        serializable_checks = self._make_json_serializable(quality_checks)

        return DatasetAnalysis(
            rows_count=len(df),
            columns=list(df.columns),
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            missing_data_pct=float(missing_data_pct),
            quality_score=quality_score,
            has_gaps=bool(quality_checks["timestamp_gaps"].get("has_gaps", False)),
            timezone=timezone_info,
            quality_checks=serializable_checks,
        )

    @staticmethod
    def _detect_timestamp_column(df: pd.DataFrame) -> Optional[str]:
        candidates = [
            "timestamp",
            "time",
            "date",
            "datetime",
            "Date",
            "Time",
            "DateTime",
        ]
        if pd.api.types.is_datetime64_any_dtype(df.index):
            return df.index.name or "index"
        for col in candidates:
            if col in df.columns:
                try:
                    pd.to_datetime(df[col].head(10))
                    return col
                except Exception:
                    continue
        for col in df.columns:
            if df[col].dtype == "object":
                sample = df[col].dropna().head(10)
                if sample.empty:
                    continue
                try:
                    pd.to_datetime(sample)
                    return col
                except Exception:
                    continue
        return None

    @staticmethod
    def _detect_timeframe(timestamp_series: pd.Series) -> str:
        if len(timestamp_series) < 2:
            return "unknown"
        time_diffs = timestamp_series.diff().dropna()
        if time_diffs.empty:
            return "unknown"
        try:
            diff_seconds = time_diffs.mode().iloc[0].total_seconds()
        except Exception:
            return "unknown"
        mapping = {
            60: "1min",
            300: "5min",
            900: "15min",
            3600: "1h",
            86400: "1d",
        }
        return mapping.get(int(diff_seconds), f"{int(diff_seconds)}s")

    @staticmethod
    def _detect_timezone(timestamp_series: pd.Series) -> str:
        if hasattr(timestamp_series.dtype, "tz") and timestamp_series.dtype.tz:
            return str(timestamp_series.dtype.tz)
        return "naive"

    @staticmethod
    def _check_required_columns(df: pd.DataFrame) -> Dict[str, Any]:
        required_cols = ["open", "high", "low", "close"]
        optional_cols = ["volume"]
        missing_required = [col for col in required_cols if col not in df.columns]
        missing_optional = [col for col in optional_cols if col not in df.columns]
        return {
            "has_all_required": not missing_required,
            "missing_required": missing_required,
            "missing_optional": missing_optional,
            "available_columns": list(df.columns),
        }

    @staticmethod
    def _check_missing_data(df: pd.DataFrame) -> Dict[str, Any]:
        missing_by_column = df.isnull().sum().to_dict()
        total_missing = sum(missing_by_column.values())
        total_cells = len(df) * len(df.columns) or 1
        missing_pct = (total_missing / total_cells) * 100
        return {
            "total_missing": int(total_missing),
            "missing_percentage": float(missing_pct),
            "missing_by_column": missing_by_column,
            "has_missing": total_missing > 0,
        }

    @staticmethod
    def _check_data_types(df: pd.DataFrame) -> Dict[str, Any]:
        numeric_cols = ["open", "high", "low", "close", "volume"]
        type_issues: Dict[str, str] = {}
        for col in numeric_cols:
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                type_issues[col] = str(df[col].dtype)
        return {
            "numeric_columns_correct": not type_issues,
            "type_issues": type_issues,
            "column_types": {col: str(df[col].dtype) for col in df.columns},
        }

    @staticmethod
    def _check_timestamp_gaps(df: pd.DataFrame, timestamp_col: Optional[str]) -> Dict[str, Any]:
        if not timestamp_col or timestamp_col not in df.columns:
            return {"has_gaps": False, "gap_count": 0}
        timestamps = pd.to_datetime(df[timestamp_col]).sort_values()
        if len(timestamps) < 2:
            return {"has_gaps": False, "gap_count": 0}
        time_diffs = timestamps.diff().dropna()
        if time_diffs.empty:
            return {"has_gaps": False, "gap_count": 0}
        expected_freq = time_diffs.mode().iloc[0]
        large_gaps = time_diffs[time_diffs > expected_freq * 1.5]
        return {
            "has_gaps": len(large_gaps) > 0,
            "gap_count": int(len(large_gaps)),
            "largest_gap": large_gaps.max() if not large_gaps.empty else None,
            "expected_frequency": str(expected_freq),
        }

    @staticmethod
    def _check_outliers(df: pd.DataFrame) -> Dict[str, Any]:
        numeric_cols = ["open", "high", "low", "close", "volume"]
        outliers: Dict[str, Dict[str, float]] = {}
        for col in numeric_cols:
            if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
                series = df[col].dropna()
                if series.empty:
                    continue
                q1 = series.quantile(0.25)
                q3 = series.quantile(0.75)
                iqr = q3 - q1
                lower = q1 - 1.5 * iqr
                upper = q3 + 1.5 * iqr
                mask = (series < lower) | (series > upper)
                count = int(mask.sum())
                outliers[col] = {
                    "count": count,
                    "percentage": (count / len(df)) * 100,
                }
        total_outliers = sum(item["count"] for item in outliers.values())
        return {
            "has_outliers": total_outliers > 0,
            "total_outliers": total_outliers,
            "by_column": outliers,
        }

    @staticmethod
    def _check_duplicates(df: pd.DataFrame, timestamp_col: Optional[str]) -> Dict[str, Any]:
        if not timestamp_col or timestamp_col not in df.columns:
            return {"has_duplicates": False, "duplicate_count": 0}
        duplicate_count = int(df[timestamp_col].duplicated().sum())
        return {
            "has_duplicates": duplicate_count > 0,
            "duplicate_count": duplicate_count,
            "unique_timestamps": int(df[timestamp_col].nunique()),
            "total_rows": len(df),
        }

    @staticmethod
    def _calculate_quality_score(quality_checks: Dict[str, Any]) -> float:
        score = 100.0
        if not quality_checks["required_columns"]["has_all_required"]:
            score -= 30
        missing_pct = quality_checks["missing_data"]["missing_percentage"]
        score -= min(missing_pct * 2, 20)
        if not quality_checks["data_types"]["numeric_columns_correct"]:
            score -= 15
        if quality_checks["timestamp_gaps"]["has_gaps"]:
            gap_count = quality_checks["timestamp_gaps"]["gap_count"]
            score -= min(gap_count * 2, 15)
        if quality_checks["outliers"]["has_outliers"]:
            outlier_pct = sum(
                item["percentage"] for item in quality_checks["outliers"]["by_column"].values()
            )
            score -= min(outlier_pct / 10, 10)
        if quality_checks["duplicates"]["has_duplicates"]:
            dup_pct = (
                quality_checks["duplicates"]["duplicate_count"]
                / (quality_checks["duplicates"]["total_rows"] or 1)
            ) * 100
            score -= min(dup_pct, 10)
        return max(0.0, round(score, 1))

    def _make_json_serializable(self, obj: Any) -> Any:
        if isinstance(obj, dict):
            return {key: self._make_json_serializable(value) for key, value in obj.items()}
        if isinstance(obj, list):
            return [self._make_json_serializable(item) for item in obj]
        if isinstance(obj, (np.generic,)):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        if isinstance(obj, pd.Timedelta):
            return str(obj)
        return obj
