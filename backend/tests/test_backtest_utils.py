import types
from unittest.mock import MagicMock, call
import pytest

# Testing library/framework note:
# Using pytest with unittest.mock for mocking (preferred per existing repo conventions if present).

# Import target function and model. Adjust module path if needed to match repo structure.
try:
    from backend.app.backtest_utils import load_backtest  # common utils location
except ModuleNotFoundError:
    try:
        from backend.app.backtests.utils import load_backtest  # alternative path
    except ModuleNotFoundError:
        from backend.tests.test_backtest_utils import load_backtest  # fallback for inline snippet during PR review

# Backtest model import for type reference and to pass into session.query assertions.
try:
    from backend.app.database.models import Backtest
except ModuleNotFoundError:
    # Minimal stub for Backtest when running in isolation (type only, not used for behavior)
    class Backtest:  # type: ignore
        id: int
        results: dict | None

class _Obj:
    """Simple namespace builder for stub backtest objects."""
    def __init__(self, **kw):
        for k, v in kw.items():
            setattr(self, k, v)

def _make_session_mock(first_result):
    """
    Build a SQLAlchemy-like session mock:
      session.query(Backtest).filter(Backtest.id == id).first() -> first_result
    """
    session = MagicMock(name="Session")
    query = MagicMock(name="Query")
    # Chain: query().filter().first()
    session.query.return_value = query
    query.filter.return_value = query
    query.first.return_value = first_result
    return session, query

def test_load_backtest_returns_instance_when_found_with_results():
    backtest_obj = _Obj(id=123, results={"metrics": {"sharpe": 1.2}})
    session, query = _make_session_mock(first_result=backtest_obj)

    bt, err = load_backtest(session, backtest_id=123)

    # Returns the object and no error
    assert bt is backtest_obj
    assert err is None

    # Query behavior
    session.query.assert_called_once_with(Backtest)
    assert query.filter.call_count == 1
    query.first.assert_called_once()

def test_load_backtest_returns_not_found_error_when_missing():
    session, query = _make_session_mock(first_result=None)

    bt, err = load_backtest(session, backtest_id=999)

    assert bt is None
    assert err == {'success': False, 'error': 'Backtest not found'}

    session.query.assert_called_once_with(Backtest)
    query.filter.assert_called_once()
    query.first.assert_called_once()

@pytest.mark.parametrize("falsy_results", [None, {}, [], 0, ""])
def test_load_backtest_returns_no_results_error_when_results_falsy(falsy_results):
    backtest_obj = _Obj(id=5, results=falsy_results)
    session, query = _make_session_mock(first_result=backtest_obj)

    bt, err = load_backtest(session, backtest_id=5)

    assert bt is None
    assert err == {'success': False, 'error': 'No results available for this backtest'}

    session.query.assert_called_once_with(Backtest)
    query.filter.assert_called_once()
    query.first.assert_called_once()

def test_load_backtest_uses_filter_on_id_once():
    backtest_obj = _Obj(id=42, results={"ok": True})
    session, query = _make_session_mock(first_result=backtest_obj)

    _bt, _err = load_backtest(session, backtest_id=42)

    # Ensure filter was called exactly once with a SQLAlchemy binary expression-like object.
    # We can't import SQLAlchemy operators reliably here; ensure one positional arg was passed.
    args, kwargs = query.filter.call_args
    assert len(args) == 1
    assert kwargs == {}
    # The expression should reference Backtest.id or similar; do a loose string check
    # to avoid coupling to SQLAlchemy internals.
    expr_repr = repr(args[0])
    assert 'id' in expr_repr or 'Backtest' in expr_repr

def test_error_payloads_are_clean_and_do_not_include_results_or_instance():
    # Missing backtest
    session_missing, _ = _make_session_mock(first_result=None)
    bt, err = load_backtest(session_missing, backtest_id=1)
    assert bt is None
    assert set(err.keys()) == {"success", "error"}
    assert err["success"] is False
    assert isinstance(err["error"], str)

    # No results
    session_no_results, _ = _make_session_mock(first_result=_Obj(id=2, results=None))
    bt2, err2 = load_backtest(session_no_results, backtest_id=2)
    assert bt2 is None
    assert set(err2.keys()) == {"success", "error"}
    assert err2["success"] is False
    assert isinstance(err2["error"], str)