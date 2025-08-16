import pandas as pd
import pytest
from backtester.metrics import max_drawdown


def test_max_drawdown_positive():
    eq = pd.DataFrame({'equity': [100, 120, 80, 90]})
    md = max_drawdown(eq)
    assert md == pytest.approx(1/3)
