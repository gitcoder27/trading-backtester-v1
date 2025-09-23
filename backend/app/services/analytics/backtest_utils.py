"""Shared helpers for working with backtest ORM entities."""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from sqlalchemy.orm import Session

from backend.app.database.models import Backtest


def load_backtest(session: Session, backtest_id: int) -> Tuple[Optional[Backtest], Optional[Dict[str, object]]]:
    """Return a backtest instance or a serialized error payload."""

    backtest = session.query(Backtest).filter(Backtest.id == backtest_id).first()

    if backtest is None:
        return None, {'success': False, 'error': 'Backtest not found'}

    if not backtest.results:
        return None, {'success': False, 'error': 'No results available for this backtest'}

    return backtest, None
