from __future__ import annotations
import json
import os
import datetime as _dt
from typing import Any, Dict

try:
    import numpy as _np  # type: ignore
except Exception:  # pragma: no cover
    _np = None

PREFS_FILE = os.path.join("temp", "user_prefs.json")

__all__ = ["load_prefs", "save_prefs", "get_pref", "set_pref"]


def load_prefs() -> Dict[str, Any]:
    try:
        if os.path.isfile(PREFS_FILE):
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _to_jsonable(obj: Any) -> Any:
    # dict
    if isinstance(obj, dict):
        return {str(k): _to_jsonable(v) for k, v in obj.items()}
    # list/tuple
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(x) for x in obj]
    # datetime/date
    if isinstance(obj, (_dt.datetime, _dt.date)):
        return obj.isoformat()
    # numpy scalars
    if _np is not None and isinstance(obj, _np.generic):  # type: ignore[attr-defined]
        return obj.item()
    # pandas Timestamp (avoid importing pandas here)
    if obj.__class__.__name__ == 'Timestamp' and hasattr(obj, 'isoformat'):
        return obj.isoformat()
    # fallback: let json handle primitives, else str()
    try:
        json.dumps(obj)
        return obj
    except Exception:
        return str(obj)


def save_prefs(prefs: Dict[str, Any]) -> None:
    try:
        os.makedirs(os.path.dirname(PREFS_FILE), exist_ok=True)
        with open(PREFS_FILE, "w", encoding="utf-8") as f:
            json.dump(_to_jsonable(prefs), f, indent=2)
    except Exception:
        # Silently ignore persistence errors
        pass


def get_pref(prefs: Dict[str, Any], key: str, default: Any) -> Any:
    return prefs.get(key, default)


def set_pref(prefs: Dict[str, Any], key: str, value: Any) -> None:
    prefs[key] = value
