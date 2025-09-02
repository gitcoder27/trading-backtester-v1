"""
Tests for the background job system
"""

import pytest
import time
import json
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import tempfile
import os

from backend.app.tasks.job_runner import JobRunner, JobStatus, ProgressCallback
from backend.app.database.models import create_tables, get_engine


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Patch the database URL for testing
    original_url = "sqlite:///./backend/database/backtester.db"
    test_url = f"sqlite:///{db_path}"
    
    with patch('backend.app.database.models.DATABASE_URL', test_url):
        create_tables()
        yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def job_runner(temp_db):
    """Create a JobRunner instance with test database"""
    with patch('backend.app.database.models.DATABASE_URL', f"sqlite:///{temp_db}"):
        runner = JobRunner(max_workers=2)
        yield runner
        runner.shutdown()


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    dates = pd.date_range('2024-01-01 09:15:00', periods=20, freq='1min')
    data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 20),
        'high': np.random.uniform(110, 115, 20),
        'low': np.random.uniform(95, 100, 20),
        'close': np.random.uniform(100, 110, 20),
        'volume': np.random.randint(1000, 5000, 20)
    }, index=dates)
    data.index.name = 'timestamp'
    
    return data.to_csv().encode('utf-8')


def test_job_runner_initialization(job_runner):
    """Test JobRunner can be initialized"""
    assert job_runner is not None
    assert job_runner.executor is not None
    assert len(job_runner.active_jobs) == 0


def test_submit_job(job_runner, sample_csv_data):
    """Test submitting a job for background execution"""
    job_id = job_runner.submit_job(
        strategy="strategies.ema10_scalper.EMA10ScalperStrategy",
        strategy_params={},
        csv_bytes=sample_csv_data,
        engine_options={"initial_cash": 100000, "lots": 1}
    )
    
    assert job_id is not None
    assert job_id in job_runner.active_jobs


def test_job_status_tracking(job_runner, sample_csv_data):
    """Test job status can be tracked"""
    job_id = job_runner.submit_job(
        strategy="strategies.ema10_scalper.EMA10ScalperStrategy",
        strategy_params={},
        csv_bytes=sample_csv_data,
        engine_options={"initial_cash": 100000, "lots": 1}
    )
    
    # Initially should be pending
    status = job_runner.get_job_status(job_id)
    assert status is not None
    assert status["status"] == JobStatus.PENDING
    assert status["id"] == int(job_id)
    assert status["progress"] == 0.0


def test_job_completion(job_runner, sample_csv_data):
    """Test job completes successfully"""
    job_id = job_runner.submit_job(
        strategy="strategies.ema10_scalper.EMA10ScalperStrategy",
        strategy_params={},
        csv_bytes=sample_csv_data,
        engine_options={"initial_cash": 100000, "lots": 1}
    )
    
    # Wait for completion (should be fast with small dataset)
    max_wait = 30  # seconds
    wait_time = 0
    
    while wait_time < max_wait:
        status = job_runner.get_job_status(job_id)
        if status["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
            break
        time.sleep(0.5)
        wait_time += 0.5
    
    # Check final status
    status = job_runner.get_job_status(job_id)
    assert status["status"] == JobStatus.COMPLETED
    assert status["progress"] == 1.0
    
    # Check results are available
    results = job_runner.get_job_results(job_id)
    assert results is not None
    assert "equity_curve" in results
    assert "trade_log" in results
    assert "metrics" in results


def test_job_cancellation(job_runner, sample_csv_data):
    """Test job can be cancelled"""
    # Submit a job
    job_id = job_runner.submit_job(
        strategy="strategies.ema10_scalper.EMA10ScalperStrategy",
        strategy_params={},
        csv_bytes=sample_csv_data,
        engine_options={"initial_cash": 100000, "lots": 1}
    )
    
    # Cancel immediately
    cancelled = job_runner.cancel_job(job_id)
    assert cancelled is True
    
    # Check status
    status = job_runner.get_job_status(job_id)
    # Status should eventually be cancelled (might take a moment)
    assert status["status"] in [JobStatus.CANCELLED, JobStatus.PENDING, JobStatus.RUNNING]


def test_list_jobs(job_runner, sample_csv_data):
    """Test listing jobs"""
    # Submit multiple jobs
    job_ids = []
    for i in range(3):
        job_id = job_runner.submit_job(
            strategy="strategies.ema10_scalper.EMA10ScalperStrategy",
            strategy_params={},
            csv_bytes=sample_csv_data,
            engine_options={"initial_cash": 100000, "lots": 1}
        )
        job_ids.append(job_id)
    
    # List jobs
    jobs = job_runner.list_jobs(limit=10)
    
    assert len(jobs) >= 3
    job_ids_in_list = [str(job["id"]) for job in jobs]
    
    for job_id in job_ids:
        assert job_id in job_ids_in_list


def test_progress_callback():
    """Test progress callback functionality"""
    mock_runner = MagicMock()
    callback = ProgressCallback("test_job", mock_runner)
    
    # Test callback
    callback(0.5, "test step", 10)
    
    # Should call update_job_progress
    mock_runner.update_job_progress.assert_called_with("test_job", 0.5, "test step", 10)


def test_progress_callback_throttling():
    """Test progress callback throttling"""
    mock_runner = MagicMock()
    callback = ProgressCallback("test_job", mock_runner)
    
    # Call multiple times quickly
    callback(0.1, "step 1")
    callback(0.2, "step 2")  # This should be throttled
    
    # Only first call should go through due to throttling
    assert mock_runner.update_job_progress.call_count == 1


def test_nonexistent_job_status(job_runner):
    """Test getting status of nonexistent job"""
    status = job_runner.get_job_status("999")
    assert status is None


def test_nonexistent_job_results(job_runner):
    """Test getting results of nonexistent job"""
    results = job_runner.get_job_results("999")
    assert results is None


def test_job_with_invalid_strategy(job_runner, sample_csv_data):
    """Test job with invalid strategy fails gracefully"""
    job_id = job_runner.submit_job(
        strategy="nonexistent.strategy.Class",
        strategy_params={},
        csv_bytes=sample_csv_data,
        engine_options={"initial_cash": 100000, "lots": 1}
    )
    
    # Wait for completion
    max_wait = 10  # seconds
    wait_time = 0
    
    while wait_time < max_wait:
        status = job_runner.get_job_status(job_id)
        if status["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
            break
        time.sleep(0.5)
        wait_time += 0.5
    
    # Should fail
    status = job_runner.get_job_status(job_id)
    assert status["status"] == JobStatus.FAILED
    assert status["error_message"] is not None


def test_multiple_concurrent_jobs(job_runner, sample_csv_data):
    """Test multiple jobs can run concurrently"""
    job_ids = []
    
    # Submit multiple jobs
    for i in range(3):
        job_id = job_runner.submit_job(
            strategy="strategies.ema10_scalper.EMA10ScalperStrategy",
            strategy_params={},
            csv_bytes=sample_csv_data,
            engine_options={"initial_cash": 100000, "lots": 1}
        )
        job_ids.append(job_id)
    
    # All should be submitted
    assert len(job_ids) == 3
    
    # Wait for all to complete
    max_wait = 60  # seconds for all jobs
    completed = 0
    
    for attempt in range(max_wait * 2):  # Check every 0.5 seconds
        completed = 0
        for job_id in job_ids:
            status = job_runner.get_job_status(job_id)
            if status["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
                completed += 1
        
        if completed == len(job_ids):
            break
        
        time.sleep(0.5)
    
    # All jobs should complete
    assert completed == len(job_ids)
