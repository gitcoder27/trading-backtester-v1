from __future__ import annotations

import importlib
import inspect
import pkgutil
from typing import Dict, Type

from backtester.strategy_base import StrategyBase
import strategies

__all__ = ["STRATEGY_MAP"]


def _discover_strategies() -> Dict[str, Type[StrategyBase]]:
    """Dynamically discover strategy classes in the strategies package."""
    strategy_map: Dict[str, Type[StrategyBase]] = {}
    for module_info in pkgutil.iter_modules(strategies.__path__):
        module = importlib.import_module(f"{strategies.__name__}.{module_info.name}")
        for _, obj in inspect.getmembers(module, inspect.isclass):
            if issubclass(obj, StrategyBase) and obj is not StrategyBase:
                key = obj.__name__[:-8] if obj.__name__.endswith("Strategy") else obj.__name__
                strategy_map[key] = obj
    return strategy_map


STRATEGY_MAP = _discover_strategies()
