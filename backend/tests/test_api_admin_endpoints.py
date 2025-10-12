from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app.api.v1 import admin as admin_module
from backend.app.database import models as db_models
from backend.app.main import app


@pytest.fixture(name="client")
def client_fixture() -> Generator[TestClient, None, None]:
    with TestClient(app) as client:
        yield client


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


def test_clear_datasets_removes_all(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    dataset = db_models.Dataset(
        id=1,
        name="Sample",
        filename="sample.csv",
        file_path="/tmp/sample.csv",
        file_size=100,
    )

    session_factory = _build_session_factory(dataset)
    monkeypatch.setattr(admin_module, "get_session_factory", lambda: session_factory, raising=False)

    response = client.delete("/api/v1/admin/datasets")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_records"] == 1

    with session_factory() as session:
        remaining = session.query(db_models.Dataset).count()
        assert remaining == 0


def test_clear_backtests_removes_associated_data(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    backtest = db_models.Backtest(
        id=11,
        strategy_name="MeanRevert",
        status="completed",
        strategy_params={"window": 5},
        dataset_id=None,
        created_at=datetime(2024, 2, 1, 9, 0, tzinfo=timezone.utc),
        completed_at=datetime(2024, 2, 1, 10, 0, tzinfo=timezone.utc),
        results={},
    )
    metrics = db_models.BacktestMetrics(id=21, backtest_job_id=7, total_return=1.0)
    trade = db_models.Trade(
        id=31,
        backtest_job_id=7,
        entry_time=datetime(2024, 2, 1, 9, 0, tzinfo=timezone.utc),
        entry_price=100.0,
        quantity=1,
        side="long",
    )
    dataset = db_models.Dataset(
        id=41,
        name="Data",
        filename="data.csv",
        file_path="/tmp/data.csv",
        file_size=50,
        backtest_count=3,
    )

    session_factory = _build_session_factory(backtest, metrics, trade, dataset)
    monkeypatch.setattr(admin_module, "get_session_factory", lambda: session_factory, raising=False)

    response = client.delete("/api/v1/admin/backtests")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_backtests"] == 1
    assert data["deleted_trades"] == 1

    with session_factory() as session:
        assert session.query(db_models.Backtest).count() == 0
        assert session.query(db_models.BacktestMetrics).count() == 0
        assert session.query(db_models.Trade).count() == 0
        # Dataset counters reset
        updated_dataset = session.query(db_models.Dataset).filter(db_models.Dataset.id == 41).first()
        assert updated_dataset is not None
        assert updated_dataset.backtest_count == 0


def test_clear_jobs_removes_all(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    job = db_models.BacktestJob(
        id=51,
        status="completed",
        strategy="strategies.alpha.Alpha",
        strategy_params={"window": 10},
        engine_options={"lots": 2},
    )

    session_factory = _build_session_factory(job)
    monkeypatch.setattr(admin_module, "get_session_factory", lambda: session_factory, raising=False)

    response = client.delete("/api/v1/admin/jobs")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["deleted_jobs"] == 1

    with session_factory() as session:
        assert session.query(db_models.BacktestJob).count() == 0
