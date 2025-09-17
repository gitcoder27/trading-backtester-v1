"""Tests for optimization utility helpers."""

import pytest

from backend.app.services.optimization import ParameterGridError, generate_parameter_grid, validate_metric


def test_generate_parameter_grid_mixed_ranges():
    param_ranges = {
        "ema": {"type": "range", "start": 5, "stop": 7, "step": 1},
        "rsi": {"type": "choice", "values": [14, 21]},
    }
    combos = generate_parameter_grid(param_ranges)
    assert len(combos) == 6
    assert {combo["ema"] for combo in combos} == {5, 6, 7}
    assert {combo["rsi"] for combo in combos} == {14, 21}


def test_generate_parameter_grid_invalid_range():
    with pytest.raises(ParameterGridError):
        generate_parameter_grid({"ema": {"type": "range", "start": "a", "stop": 5}})


def test_validate_metric_allows_known_value():
    assert validate_metric("sharpe_ratio", {"sharpe_ratio", "total_return"}) == "sharpe_ratio"


def test_validate_metric_rejects_unknown():
    with pytest.raises(ValueError):
        validate_metric("unknown_metric", {"sharpe_ratio"})
