"""Utility helpers for optimization workflows."""

from __future__ import annotations

import itertools
from typing import Any, Dict, Iterable, List, Sequence, Union

import numpy as np


class ParameterGridError(ValueError):
    """Raised when parameter grid configuration is invalid."""


ParamRange = Union[List[Any], Dict[str, Any]]


def _range_from_config(config: Dict[str, Any]) -> Sequence[Any]:
    range_type = config.get("type")
    if range_type == "range":
        start = config["start"]
        stop = config["stop"]
        step = config.get("step", 1)
        if not isinstance(step, (int, float)):
            raise ParameterGridError("step must be numeric for range parameters")
        if isinstance(start, int) and isinstance(stop, int) and isinstance(step, int):
            return list(range(start, stop + step, step))
        if isinstance(start, (int, float)) and isinstance(stop, (int, float)):
            return list(np.arange(start, stop + step, step))
        raise ParameterGridError("range parameters must be numeric")
    if range_type == "choice":
        values = config.get("values")
        if not isinstance(values, list) or not values:
            raise ParameterGridError("choice parameters require a non-empty list of values")
        return values
    raise ParameterGridError(f"Unknown parameter type '{range_type}'")


def generate_parameter_grid(param_ranges: Dict[str, ParamRange]) -> List[Dict[str, Any]]:
    """Expand structured parameter ranges into a concrete grid."""

    if not param_ranges:
        return []

    param_lists: Dict[str, Sequence[Any]] = {}
    for name, config in param_ranges.items():
        if isinstance(config, list):
            if not config:
                raise ParameterGridError(f"Parameter '{name}' list cannot be empty")
            param_lists[name] = config
        elif isinstance(config, dict):
            param_lists[name] = _range_from_config(config)
        else:
            raise ParameterGridError(f"Invalid configuration for parameter '{name}'")

    param_names = list(param_lists.keys())
    combinations = [
        dict(zip(param_names, values))
        for values in itertools.product(*(param_lists[name] for name in param_names))
    ]
    return combinations


def validate_metric(metric: str, available_metrics: Iterable[str]) -> str:
    """Ensure the requested optimization metric is available."""

    metric = metric or ""
    if metric not in available_metrics:
        raise ValueError(
            f"Unsupported optimization metric '{metric}'. Available metrics: {sorted(set(available_metrics))}"
        )
    return metric
