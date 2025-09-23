"""Dataset storage utilities."""

from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

from backend.app.utils.path_utils import resolve_dataset_path


class DatasetStorage:
    """Handle dataset persistence to and from disk."""

    def __init__(self, data_dir: str | Path = "data/market_data") -> None:
        self._data_dir = Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

    @property
    def data_dir(self) -> Path:
        return self._data_dir

    def save(self, file_name: str, content: bytes) -> Path:
        file_hash = hashlib.md5(content).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        safe_name = f"{timestamp}_{file_hash}_{file_name}"
        target_path = self._data_dir / safe_name
        target_path.write_bytes(content)
        return target_path

    def delete(self, file_path: str | Path) -> None:
        path = Path(file_path)
        if path.exists():
            path.unlink()

    def resolve(self, file_path: str | Path) -> Path:
        return Path(resolve_dataset_path(str(file_path)))

    def load_dataframe(
        self,
        file_path: str | Path,
        *,
        nrows: Optional[int] = None,
        usecols: Optional[Iterable[str]] = None,
    ) -> pd.DataFrame:
        resolved = self.resolve(file_path)
        return pd.read_csv(resolved, nrows=nrows, usecols=usecols)

    def iter_chunks(
        self,
        file_path: str | Path,
        *,
        chunk_size: int,
        usecols: Optional[Iterable[str]] = None,
    ) -> Iterable[pd.DataFrame]:
        resolved = self.resolve(file_path)
        return pd.read_csv(resolved, chunksize=chunk_size, usecols=usecols)

    def exists(self, file_path: str | Path) -> bool:
        return self.resolve(file_path).exists()
