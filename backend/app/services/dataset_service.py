"""Dataset management orchestration using modular helpers."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.app.config import get_settings
from backend.app.services.datasets import (
    DatasetAnalysis,
    DatasetAnalyzer,
    DatasetRepository,
    DatasetStorage,
)
from backend.app.utils.path_utils import normalize_path


class DatasetService:
    """High level service coordinating dataset storage and analysis."""

    def __init__(
        self,
        data_dir: Optional[Path | str] = None,
        *,
        storage: Optional[DatasetStorage] = None,
        analyzer: Optional[DatasetAnalyzer] = None,
        repository: Optional[DatasetRepository] = None,
    ) -> None:
        settings = get_settings()
        base_dir = Path(data_dir) if data_dir else Path(settings.data_dir)
        self.storage = storage or DatasetStorage(base_dir)
        self.analyzer = analyzer or DatasetAnalyzer()
        self.repository = repository or DatasetRepository()
        self._project_root = Path.cwd().resolve()

    @property
    def data_dir(self) -> Path:
        return self.storage.data_dir

    def upload_dataset(
        self,
        *,
        file_name: str,
        file_content: bytes,
        name: Optional[str] = None,
        symbol: Optional[str] = None,
        exchange: Optional[str] = None,
        data_source: Optional[str] = None,
    ) -> Dict[str, Any]:
        file_path = self.storage.save(file_name, file_content)
        try:
            analysis = self.analyzer.analyze(file_path)
        except Exception:
            self.storage.delete(file_path)
            raise
        dataset = self.repository.create_dataset(
            file_path=file_path,
            file_name=file_name,
            file_size=len(file_content),
            analysis=analysis,
            name=name,
            symbol=symbol,
            exchange=exchange,
            data_source=data_source,
        )
        return {
            "success": True,
            "dataset_id": dataset.id,
            "dataset": self.repository.to_dict(dataset),
            "analysis": self._serialize_analysis(analysis),
        }

    def get_dataset_quality(self, dataset_id: int) -> Dict[str, Any]:
        dataset = self.repository.get(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        self.repository.touch_last_accessed(dataset)
        analysis_dict: Dict[str, Any]
        if dataset.quality_checks:
            analysis_dict = dataset.quality_checks
        else:
            analysis = self.analyzer.analyze(Path(dataset.file_path))
            dataset = self.repository.update_quality_checks(dataset, analysis)
            analysis_dict = self._serialize_analysis(analysis)
        return {
            "success": True,
            "dataset_id": dataset.id,
            "dataset": self.repository.to_dict(dataset),
            "quality_analysis": analysis_dict,
        }

    def list_datasets(self, limit: int = 50) -> List[Dict[str, Any]]:
        datasets = self.repository.list(limit=limit)
        return [
            self.repository.to_dict(dataset, include_quality=False)
            for dataset in datasets
        ]

    def delete_dataset(self, dataset_id: int) -> Dict[str, Any]:
        dataset = self.repository.delete(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset {dataset_id} not found")
        self.storage.delete(dataset.file_path)
        return {
            "success": True,
            "message": f"Dataset {dataset_id} deleted successfully",
        }

    def get_dataset_data(
        self,
        dataset_id: int,
        *,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> Dict[str, Any]:
        dataset = self.repository.get(dataset_id)
        if not dataset:
            return {"success": False, "error": "Dataset not found"}
        resolved = self.storage.resolve(dataset.file_path)
        if not resolved.exists():
            return {
                "success": False,
                "error": f"Dataset file not found on disk: {dataset.file_path}",
            }
        df = pd.read_csv(resolved)
        timestamp_col = self._detect_timestamp_column(df)
        if timestamp_col:
            df[timestamp_col] = pd.to_datetime(df[timestamp_col])
            if start_date:
                df = df[df[timestamp_col] >= pd.to_datetime(start_date)]
            if end_date:
                df = df[df[timestamp_col] <= pd.to_datetime(end_date)]
            df = df.sort_values(timestamp_col).reset_index(drop=True)
        data_records = df.to_dict("records")
        self.repository.touch_last_accessed(dataset)
        date_range = None
        if timestamp_col and not df.empty:
            date_range = {
                "start": df[timestamp_col].min().isoformat(),
                "end": df[timestamp_col].max().isoformat(),
            }
        return {
            "success": True,
            "dataset_id": dataset_id,
            "data": data_records,
            "rows_count": len(data_records),
            "columns": list(df.columns),
            "date_range": date_range,
            "metadata": self.repository.to_dict(dataset, include_quality=False),
        }

    def preview_dataset(self, dataset_id: int, rows: int = 10) -> Dict[str, Any]:
        dataset = self.repository.get(dataset_id)
        if not dataset:
            raise ValueError("Dataset not found")
        resolved = self.storage.resolve(dataset.file_path)
        if not resolved.exists():
            raise ValueError("Dataset file not found")
        preview_df = self.storage.load_dataframe(dataset.file_path, nrows=rows)
        numeric_columns = preview_df.select_dtypes(include=["number"]).columns
        stats = self._compute_statistics(resolved, list(numeric_columns))
        total_rows = dataset.rows_count or dataset.rows
        if not total_rows:
            total_rows = self._count_rows(resolved)
        self.repository.touch_last_accessed(dataset)
        return {
            "success": True,
            "dataset_id": dataset_id,
            "dataset_info": self.repository.to_dict(dataset),
            "preview": preview_df.to_dict(orient="records"),
            "statistics": stats,
            "total_rows": int(total_rows) if total_rows else 0,
            "columns": list(preview_df.columns),
        }

    def discover_local_datasets(self) -> List[Dict[str, Any]]:
        discovered: List[Dict[str, Any]] = []
        data_dir = self.storage.data_dir
        if not data_dir.exists():
            return discovered
        for path in sorted(data_dir.rglob("*.csv")):
            try:
                resolved = path if path.is_absolute() else (self._project_root / path).resolve()
            except Exception:
                resolved = Path(path)
            if not resolved.exists():
                continue
            storage_path = self._to_storage_path(resolved)
            existing = self.repository.get_by_file_path(storage_path)
            if existing:
                entry = self.repository.to_dict(existing)
                entry["registered"] = True
                entry["dataset_id"] = existing.id
                entry["file_path"] = storage_path
                discovered.append(entry)
                continue
            try:
                analysis = self.analyzer.analyze(resolved)
                display_name = self._derive_dataset_name(resolved)
                entry = {
                    "registered": False,
                    "dataset_id": None,
                    "file_path": storage_path,
                    "name": display_name,
                    "file_size": resolved.stat().st_size,
                    "rows_count": analysis.rows_count,
                    "timeframe": analysis.timeframe,
                    "start_date": analysis.start_date.isoformat() if analysis.start_date else None,
                    "end_date": analysis.end_date.isoformat() if analysis.end_date else None,
                    "quality_score": analysis.quality_score,
                    "analysis": self._serialize_analysis(analysis),
                }
                discovered.append(entry)
            except Exception as exc:
                discovered.append(
                    {
                        "registered": False,
                        "dataset_id": None,
                        "file_path": storage_path,
                        "name": resolved.stem,
                        "error": str(exc),
                    }
                )
        return discovered

    def register_local_datasets(self, file_paths: Optional[List[str]] = None) -> Dict[str, Any]:
        discovered = {item["file_path"]: item for item in self.discover_local_datasets()}
        targets = file_paths or list(discovered.keys())
        registered_ids: List[int] = []
        skipped: List[str] = []
        errors: List[Dict[str, str]] = []
        registered_datasets: List[Dict[str, Any]] = []

        for file_path in targets:
            info = discovered.get(file_path)
            if not info:
                errors.append({"file_path": file_path, "error": "Dataset file not found in data directory"})
                continue
            if info.get("registered"):
                skipped.append(file_path)
                continue
            try:
                resolved = self._resolve_local_path(file_path)
                analysis = self.analyzer.analyze(resolved)
                dataset = self.repository.create_dataset(
                    file_path=self._to_storage_path(resolved),
                    file_name=resolved.name,
                    file_size=resolved.stat().st_size,
                    analysis=analysis,
                    name=info.get("name") or self._derive_dataset_name(resolved),
                )
                registered_ids.append(dataset.id)
                registered_datasets.append(self.repository.to_dict(dataset))
            except Exception as exc:
                errors.append({"file_path": file_path, "error": str(exc)})

        return {
            "success": True,
            "registered": registered_ids,
            "skipped": skipped,
            "errors": errors,
            "datasets": registered_datasets,
        }

    @staticmethod
    def _serialize_analysis(analysis: DatasetAnalysis) -> Dict[str, Any]:
        payload = analysis.to_dict()
        payload["start_date"] = (
            analysis.start_date.isoformat() if analysis.start_date else None
        )
        payload["end_date"] = (
            analysis.end_date.isoformat() if analysis.end_date else None
        )
        return payload

    @staticmethod
    def _detect_timestamp_column(df: pd.DataFrame) -> Optional[str]:
        for candidate in [
            "timestamp",
            "time",
            "datetime",
            "date",
            "Timestamp",
            "DateTime",
            "Date",
        ]:
            if candidate in df.columns:
                return candidate
        return None

    def _compute_statistics(
        self, file_path: Path, numeric_columns: List[str]
    ) -> Dict[str, Dict[str, Optional[float]]]:
        if not numeric_columns:
            return {}
        aggregates: Dict[str, Dict[str, float]] = {
            col: {
                "count": 0.0,
                "sum": 0.0,
                "sumsq": 0.0,
                "min": math.inf,
                "max": -math.inf,
            }
            for col in numeric_columns
        }
        for chunk in self.storage.iter_chunks(file_path, chunk_size=50000, usecols=numeric_columns):
            for col in numeric_columns:
                series = chunk[col].dropna()
                if series.empty:
                    continue
                data = aggregates[col]
                data["count"] += float(series.count())
                data["sum"] += float(series.sum())
                data["sumsq"] += float((series ** 2).sum())
                data["min"] = min(data["min"], float(series.min()))
                data["max"] = max(data["max"], float(series.max()))
        stats: Dict[str, Dict[str, Optional[float]]] = {}
        for col, data in aggregates.items():
            count = int(data["count"])
            if count == 0:
                stats[col] = {
                    "mean": None,
                    "std": None,
                    "min": None,
                    "max": None,
                    "count": 0,
                }
                continue
            mean = data["sum"] / data["count"]
            variance = (
                (data["sumsq"] - (data["sum"] ** 2) / data["count"])
                / (data["count"] - 1)
                if data["count"] > 1
                else 0.0
            )
            std = math.sqrt(max(variance, 0.0))
            stats[col] = {
                "mean": mean,
                "std": std,
                "min": data["min"],
                "max": data["max"],
                "count": count,
            }
        return stats

    def _count_rows(self, file_path: Path) -> int:
        count = 0
        for chunk in self.storage.iter_chunks(file_path, chunk_size=50000):
            count += len(chunk)
        return count

    def _to_storage_path(self, path: Path) -> str:
        try:
            relative = path.relative_to(self._project_root)
            return normalize_path(str(relative))
        except ValueError:
            return normalize_path(str(path))

    def _resolve_local_path(self, file_path: str) -> Path:
        candidate = Path(file_path)
        if candidate.exists():
            return candidate.resolve()
        root_candidate = (self._project_root / file_path).resolve()
        if root_candidate.exists():
            return root_candidate
        resolved = self.storage.resolve(file_path)
        if resolved.exists():
            return resolved
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    @staticmethod
    def _derive_dataset_name(path: Path) -> str:
        filename = path.name
        parts = filename.split("_", 2)
        if len(parts) == 3 and parts[0].isdigit() and len(parts[1]) == 8:
            return parts[2]
        return filename
