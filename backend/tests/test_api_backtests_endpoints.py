from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.v1 import backtests as backtests_module
from backend.app.database import models as db_models
from backend.app.main import app
from backend.app.services import strategy_service as strategy_service_module


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


def _sample_result() -> Dict[str, Any]:
    return {
        "equity_curve": [{"timestamp": "2024-01-01T00:00:00Z", "equity": 101.5}],
        "trade_log": [
            {
                "entry_time": "2024-01-01T09:30:00Z",
                "exit_time": "2024-01-01T10:00:00Z",
                "entry_price": 100.0,
                "exit_price": 101.5,
                "position": "long",
                "pnl": 1.5,
                "duration": 30.0,
            }
        ],
        "metrics": {
            "total_return": 1.5,
            "sharpe_ratio": 1.2,
            "max_drawdown": 0.4,
            "win_rate": 75.0,
            "profit_factor": 1.8,
            "total_trades": 1,
        },
        "indicators": {},
        "engine_config": {"initial_cash": 100000},
    }


def _build_session_factory(*objects: db_models.Base) -> sessionmaker[Any]:
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    db_models.Base.metadata.create_all(bind=engine)
    SessionLocal: sessionmaker[Any] = sessionmaker(bind=engine, autoflush=False, autocommit=False)

    with SessionLocal() as session:
        for obj in objects:
            session.add(obj)
        session.commit()

    return SessionLocal


def test_run_backtest_resolves_dataset_and_strategy(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(backtests_module, "results_store", {}, raising=False)
    monkeypatch.setattr(backtests_module, "next_result_id", 1, raising=False)

    class FakeRegistry:
        def get_strategy_metadata(self, strategy_id: int) -> Dict[str, Any]:
            assert strategy_id == 7
            return {"module_path": "strategies.alpha", "class_name": "AlphaStrategy"}

    monkeypatch.setattr(strategy_service_module, "StrategyRegistry", FakeRegistry)

    dataset_model = db_models.Dataset(id=3, name="Sample Dataset", file_path="/tmp/sample.csv")
    session_factory = _build_session_factory(dataset_model)
    monkeypatch.setattr(backtests_module, "get_session_factory", lambda: session_factory, raising=False)

    class RunCaptor:
        called_with: Dict[str, Any] = {}

        @classmethod
        def run(cls, **kwargs):  # type: ignore[override]
            cls.called_with = kwargs
            return _sample_result()

    monkeypatch.setattr(backtests_module.backtest_service, "run_backtest", RunCaptor.run)

    payload = {
        "strategy": "7",
        "strategy_params": {"window": 10},
        "dataset": "3",
        "engine_options": {"daily_profit_target": 55.0},
    }

    response = client.post("/api/v1/backtests/", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["job_id"] == "1"
    assert backtests_module.results_store["1"]["metrics"]["total_trades"] == 1

    captured = RunCaptor.called_with
    assert captured["strategy"] == "strategies.alpha.AlphaStrategy"
    assert captured["dataset_path"] == "/tmp/sample.csv"
    assert captured["strategy_params"] == {"window": 10}
    assert captured["engine_options"]["daily_target"] == 55.0


def test_run_backtest_dataset_missing_returns_error(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(backtests_module, "results_store", {}, raising=False)
    monkeypatch.setattr(backtests_module, "next_result_id", 1, raising=False)

    session_factory = _build_session_factory()
    monkeypatch.setattr(backtests_module, "get_session_factory", lambda: session_factory, raising=False)

    def not_called(**_kwargs):  # pragma: no cover - safety net
        raise AssertionError("run_backtest should not be called when dataset lookup fails")

    monkeypatch.setattr(backtests_module.backtest_service, "run_backtest", not_called)

    payload = {
        "strategy": "strategies.foo.Bar",
        "strategy_params": {},
        "dataset": "99",
    }

    response = client.post("/api/v1/backtests/", json=payload)

    assert response.status_code == 500
    assert "Dataset with ID 99 not found" in response.json()["detail"]


def test_run_backtest_with_upload_invalid_json(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setattr(backtests_module, "results_store", {}, raising=False)
    monkeypatch.setattr(backtests_module, "next_result_id", 1, raising=False)

    def fail_run_backtest(**_kwargs):  # pragma: no cover - should not be called
        raise AssertionError("run_backtest should not be invoked on invalid input")

    monkeypatch.setattr(backtests_module.backtest_service, "run_backtest", fail_run_backtest)

    files = {"file": ("data.csv", b"timestamp,price\n", "text/csv")}
    data = {
        "strategy": "strategies.foo.Bar",
        "strategy_params": "{invalid",
        "engine_options": "{}",
    }

    response = client.post("/api/v1/backtests/upload", files=files, data=data)

    assert response.status_code == 500
    assert "Invalid JSON in strategy_params" in response.json()["detail"]


def test_get_backtest_detail_enriches_metrics(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    backtest_obj = db_models.Backtest(
        id=5,
        strategy_name="Breakout",
        status="completed",
        dataset_id=8,
        created_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        completed_at=datetime(2024, 1, 1, 12, 0, tzinfo=timezone.utc),
        strategy_params={"lookback": 20},
        results=json.dumps(
            {
                "metrics": {"total_return_pct": 12.0, "max_drawdown_pct": 2.5},
                "trade_log": [{"id": 1}, {"id": 2}],
                "engine_config": {"initial_cash": 50000},
            }
        ),
    )
    dataset_obj = db_models.Dataset(id=8, name="Futures", file_path="/tmp/futures.csv")

    session_factory = _build_session_factory(dataset_obj, backtest_obj)
    monkeypatch.setattr(backtests_module, "get_session_factory", lambda: session_factory, raising=False)

    response = client.get("/api/v1/backtests/5")

    assert response.status_code == 200
    data = response.json()
    assert data["dataset_name"] == "Futures"
    assert data["duration"] == "0m"
    assert data["metrics"]["total_return_percent"] == 12.0
    assert data["metrics"]["max_drawdown_percent"] == 2.5
    assert data["metrics"]["total_trades"] == 2
    assert "results" in data and data["results"]["engine_config"]["initial_cash"] == 50000


def test_list_backtests_compact_coerces_metrics(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    dataset_obj = db_models.Dataset(id=3, name="Equities", file_path="/tmp/equities.csv")
    backtest_obj = db_models.Backtest(
        id=11,
        strategy_name="MeanRevert",
        strategy_params={"window": 5},
        dataset_id=3,
        status="completed",
        created_at=datetime(2024, 2, 1, 9, 0, tzinfo=timezone.utc),
        completed_at=datetime(2024, 2, 1, 16, 0, tzinfo=timezone.utc),
        results=json.dumps(
            {
                "metrics": {
                    "total_return": "1.5",
                    "sharpe_ratio": "0.8",
                    "max_drawdown": "0.2",
                    "win_rate": "55.5",
                    "profit_factor": "1.6",
                    "total_trades": "7",
                    "trading_sessions_days": "3",
                    "trading_days": "3",
                    "total_trading_days": "4",
                    "total_return_pct": "12.5",
                    "max_drawdown_pct": "1.3",
                }
            }
        ),
    )

    session_factory = _build_session_factory(dataset_obj, backtest_obj)
    monkeypatch.setattr(backtests_module, "get_session_factory", lambda: session_factory, raising=False)

    response = client.get("/api/v1/backtests/?compact=true&page=1&size=10")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["page"] == 1
    result_row = data["results"][0]
    metrics = result_row["metrics"]
    assert metrics == {}
