"""
Phase 2 analytics backend tests
 - ETag/Last-Modified conditional requests
 - Downsampling via max_points on charts endpoints
"""

from fastapi.testclient import TestClient
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json

from backend.app.main import app
from backend.app.database.models import get_session_factory, Backtest, init_db


client = TestClient(app)


def _make_backtest(n_points: int = 500) -> int:
    """Insert a simple completed backtest with n_points equity entries."""
    init_db()
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        start = datetime(2024, 1, 1, 9, 15)
        dates = [start + timedelta(minutes=i) for i in range(n_points)]
        equity = 100000.0
        curve = []
        for i, dt in enumerate(dates):
            equity *= (1.0 + np.random.normal(0.0002, 0.002))
            curve.append({
                'timestamp': dt.isoformat(),
                'equity': float(equity)
            })
        trades = [
            {
                'entry_time': dates[0].isoformat(),
                'exit_time': dates[10].isoformat(),
                'entry_price': 100.0,
                'exit_price': 101.0,
                'pnl': 50.0,
                'direction': 'long'
            }
        ]
        metrics = {
            'total_return_pct': 5.0,
            'sharpe_ratio': 1.0,
            'max_drawdown_pct': -2.0,
            'win_rate': 0.6,
            'profit_factor': 1.5,
            'total_trades': len(trades)
        }
        bt = Backtest(
            strategy_name="Phase2Test",
            strategy_params={'p': 1},
            dataset_id=1,
            status='completed',
            results={
                'equity_curve': curve,
                'trades': trades,
                'metrics': metrics,
                'engine_config': {'daily_target': 30.0}
            },
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )
        db.add(bt)
        db.commit()
        db.refresh(bt)
        return bt.id
    finally:
        db.close()


def test_performance_etag_and_304():
    backtest_id = _make_backtest(120)
    # First request
    r1 = client.get(f"/api/v1/analytics/performance/{backtest_id}", params={'sections': ['basic_metrics']})
    assert r1.status_code == 200
    etag = r1.headers.get('etag')
    assert etag
    # Second request with If-None-Match
    r2 = client.get(
        f"/api/v1/analytics/performance/{backtest_id}",
        params={'sections': ['basic_metrics']},
        headers={'If-None-Match': etag},
    )
    assert r2.status_code == 304


def test_equity_chart_downsampling_and_304():
    backtest_id = _make_backtest(600)
    max_points = 75
    r1 = client.get(f"/api/v1/analytics/charts/{backtest_id}/equity", params={'max_points': max_points})
    assert r1.status_code == 200
    etag = r1.headers.get('etag')
    assert etag
    data = r1.json()
    assert data['success'] is True
    chart_json = data['chart']
    assert isinstance(chart_json, str)
    parsed = json.loads(chart_json)
    # First trace length should be <= max_points + small margin due to last point enforcement
    assert 'data' in parsed and len(parsed['data']) >= 1
    x_vals = parsed['data'][0].get('x', [])
    assert len(x_vals) <= max_points + 1

    # Conditional fetch should return 304
    r2 = client.get(
        f"/api/v1/analytics/charts/{backtest_id}/equity",
        params={'max_points': max_points},
        headers={'If-None-Match': etag},
    )
    assert r2.status_code == 304

