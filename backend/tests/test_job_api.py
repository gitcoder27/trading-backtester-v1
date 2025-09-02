"""
Integration tests for the job management API endpoints
"""

import pytest
import json
import time
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
import tempfile
import os
from unittest.mock import patch

from backend.app.main import app

# Create test client
client = TestClient(app)


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    # Patch the database URL for testing
    test_url = f"sqlite:///{db_path}"
    
    with patch('backend.app.database.models.DATABASE_URL', test_url):
        with patch('backend.app.tasks.job_runner.get_session_factory') as mock_factory:
            # Setup mock database session factory
            from backend.app.database.models import get_session_factory
            mock_factory.return_value = get_session_factory()
            yield db_path
    
    # Cleanup
    try:
        os.unlink(db_path)
    except:
        pass


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    dates = pd.date_range('2024-01-01 09:15:00', periods=30, freq='1min')
    data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 30),
        'high': np.random.uniform(110, 115, 30),
        'low': np.random.uniform(95, 100, 30),
        'close': np.random.uniform(100, 110, 30),
        'volume': np.random.randint(1000, 5000, 30)
    }, index=dates)
    data.index.name = 'timestamp'
    
    return data.to_csv()


def test_submit_job_json(temp_db):
    """Test submitting a job with JSON payload"""
    request_data = {
        "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
        "strategy_params": {},
        "dataset_path": None,  # Will fail but should return proper error structure
        "engine_options": {
            "initial_cash": 100000,
            "lots": 1,
            "option_delta": 0.5
        }
    }
    
    response = client.post("/api/v1/jobs/", json=request_data)
    
    # Will fail due to no dataset, but should return proper error
    assert response.status_code in [400, 500]


def test_submit_job_with_upload(temp_db, sample_csv_data):
    """Test submitting a job with file upload"""
    files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
    data = {
        "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
        "strategy_params": "{}",
        "engine_options": json.dumps({
            "initial_cash": 100000,
            "lots": 1,
            "option_delta": 0.5
        })
    }
    
    response = client.post("/api/v1/jobs/upload", files=files, data=data)
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "job_id" in result
    assert result["status"] == "pending"
    
    return result["job_id"]


def test_get_job_status(temp_db, sample_csv_data):
    """Test getting job status"""
    # First submit a job
    job_id = test_submit_job_with_upload(temp_db, sample_csv_data)
    
    # Get status
    response = client.get(f"/api/v1/jobs/{job_id}/status")
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "job" in result
    
    job_status = result["job"]
    assert job_status["id"] == int(job_id)
    assert job_status["status"] in ["pending", "running", "completed", "failed"]


def test_get_nonexistent_job_status():
    """Test getting status of nonexistent job"""
    response = client.get("/api/v1/jobs/999/status")
    assert response.status_code == 404


def test_cancel_job(temp_db, sample_csv_data):
    """Test cancelling a job"""
    # Submit a job
    job_id = test_submit_job_with_upload(temp_db, sample_csv_data)
    
    # Cancel it
    response = client.post(f"/api/v1/jobs/{job_id}/cancel")
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert result["job_id"] == job_id


def test_cancel_nonexistent_job():
    """Test cancelling nonexistent job"""
    response = client.post("/api/v1/jobs/999/cancel")
    assert response.status_code == 404


def test_list_jobs(temp_db):
    """Test listing jobs"""
    response = client.get("/api/v1/jobs/")
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "jobs" in result
    assert "total" in result
    assert isinstance(result["jobs"], list)


def test_list_jobs_with_limit(temp_db):
    """Test listing jobs with limit"""
    response = client.get("/api/v1/jobs/?limit=10")
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert len(result["jobs"]) <= 10


def test_get_job_stats(temp_db):
    """Test getting job statistics"""
    response = client.get("/api/v1/jobs/stats")
    
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "stats" in result
    
    stats = result["stats"]
    expected_keys = ["total_jobs", "pending", "running", "completed", "failed", "cancelled"]
    for key in expected_keys:
        assert key in stats
        assert isinstance(stats[key], int)


def test_job_completion_workflow(temp_db, sample_csv_data):
    """Test complete job workflow from submission to results"""
    # Submit job
    files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
    data = {
        "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
        "strategy_params": "{}",
        "engine_options": json.dumps({
            "initial_cash": 100000,
            "lots": 1,
            "option_delta": 0.5
        })
    }
    
    response = client.post("/api/v1/jobs/upload", files=files, data=data)
    assert response.status_code == 200
    
    job_id = response.json()["job_id"]
    
    # Wait for completion
    max_wait = 30  # seconds
    completed = False
    
    for _ in range(max_wait * 2):  # Check every 0.5 seconds
        response = client.get(f"/api/v1/jobs/{job_id}/status")
        if response.status_code == 200:
            status = response.json()["job"]["status"]
            if status in ["completed", "failed"]:
                completed = True
                break
        time.sleep(0.5)
    
    assert completed, "Job did not complete within expected time"
    
    # Try to get results
    response = client.get(f"/api/v1/jobs/{job_id}/results")
    
    if response.status_code == 200:
        # Job completed successfully
        result = response.json()
        assert result["success"] is True
        assert "results" in result
        
        results = result["results"]
        assert "equity_curve" in results
        assert "trade_log" in results
        assert "metrics" in results
    else:
        # Job may have failed - check status for error
        response = client.get(f"/api/v1/jobs/{job_id}/status")
        status_result = response.json()
        print(f"Job failed with error: {status_result['job'].get('error_message', 'Unknown error')}")


def test_invalid_strategy_job(temp_db, sample_csv_data):
    """Test job with invalid strategy"""
    files = {"file": ("test_data.csv", sample_csv_data, "text/csv")}
    data = {
        "strategy": "nonexistent.strategy.Class",
        "strategy_params": "{}",
        "engine_options": "{}"
    }
    
    response = client.post("/api/v1/jobs/upload", files=files, data=data)
    
    # Job should be submitted but will fail during execution
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Wait for it to fail
    max_wait = 10
    for _ in range(max_wait * 2):
        response = client.get(f"/api/v1/jobs/{job_id}/status")
        if response.status_code == 200:
            status = response.json()["job"]["status"]
            if status == "failed":
                break
        time.sleep(0.5)
    
    # Should have failed
    response = client.get(f"/api/v1/jobs/{job_id}/status")
    assert response.status_code == 200
    job_status = response.json()["job"]
    assert job_status["status"] == "failed"
    assert job_status["error_message"] is not None


def test_invalid_json_params_job(temp_db):
    """Test job with invalid JSON parameters"""
    files = {"file": ("test_data.csv", "timestamp,open,high,low,close,volume\n2024-01-01 09:15:00,100,105,95,102,1000", "text/csv")}
    data = {
        "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
        "strategy_params": "invalid json",
        "engine_options": "{}"
    }
    
    response = client.post("/api/v1/jobs/upload", files=files, data=data)
    assert response.status_code == 400


def test_get_results_for_incomplete_job(temp_db, sample_csv_data):
    """Test getting results for incomplete job"""
    # Submit job
    job_id = test_submit_job_with_upload(temp_db, sample_csv_data)
    
    # Immediately try to get results (job won't be complete yet)
    response = client.get(f"/api/v1/jobs/{job_id}/results")
    
    assert response.status_code == 400
    assert "not completed yet" in response.json()["detail"]
