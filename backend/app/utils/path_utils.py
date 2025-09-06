"""
Cross-platform path utilities for dataset and CSV file resolution.
Handles Windows vs POSIX separators and WSL path translation.
"""
from __future__ import annotations

import os
from typing import Optional


def normalize_path(path: str) -> str:
    """Normalize path separators for current OS.
    - On POSIX, convert backslashes to slashes
    - On Windows, convert slashes to backslashes
    """
    try:
        if os.name == 'posix' and '\\' in path:
            return path.replace('\\', '/')
        if os.name == 'nt' and '/' in path:
            return path.replace('/', '\\')
    except Exception:
        pass
    return path


def windows_to_wsl(path: str) -> Optional[str]:
    """Convert a Windows-style path to a WSL mount path if applicable.
    Example: C:\\Users\\file.csv -> /mnt/c/Users/file.csv
    Returns None if not convertible or not on POSIX.
    """
    try:
        if os.name != 'posix':
            return None
        if ':' in path and '\\' in path:
            drive = path[0].lower()
            rest = path[2:].replace('\\', '/')
            return f"/mnt/{drive}/{rest}"
    except Exception:
        return None
    return None


def resolve_dataset_path(original_path: Optional[str], filename: Optional[str] = None) -> Optional[str]:
    """Resolve a dataset file path robustly across OS/WSL.
    Tries, in order:
      1) normalized original_path
      2) WSL translated path (for Windows originals)
      3) data/market_data/<basename>
      4) data/<basename>
    Returns a path that exists, or None if not found.
    """
    candidates = []
    if original_path:
        norm = normalize_path(original_path)
        candidates.append(norm)
        wsl = windows_to_wsl(original_path)
        if wsl:
            candidates.append(wsl)
        base = os.path.basename(norm)
    else:
        base = (filename or '').split('/')[-1].split('\\')[-1]

    if base:
        candidates.append(os.path.join('data', 'market_data', base))
        candidates.append(os.path.join('data', base))

    for p in candidates:
        if p and os.path.exists(p):
            return p
    return None

