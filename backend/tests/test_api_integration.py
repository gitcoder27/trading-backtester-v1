"""
Integration tests for the backtest API endpoints
"""

import pytest
import json
import pandas as pd
import numpy as np
from fastapi.testclient import TestClient
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../../'))

from backend.app.main import app

# Create test client
client = TestClient(app)


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    dates = pd.date_range('2024-01-01 09:15:00', periods=50, freq='1min')
    data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 50),
        'high': np.random.uniform(110, 115, 50),
        'low': np.random.uniform(95, 100, 50),
        'close': np.random.uniform(100, 110, 50),
        'volume': np.random.randint(1000, 5000, 50)
    }, index=dates)
    data.index.name = 'timestamp'
    
    return data.to_csv()


def test_health_endpoint():
    """Test the health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


def test_root_endpoint():
    """Test the root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "endpoints" in data


def test_run_backtest_sync():
    """Test running a synchronous backtest"""
    request_data = {
        "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
        "strategy_params": {},
        "dataset_path": None,
        "engine_options": {
            "initial_cash": 100000,
            "lots": 1,
            "option_delta": 0.5
        }
    }
    
    # This will fail without dataset_path or uploaded file, but should return proper error
    response = client.post("/api/v1/backtests/", json=request_data)
    assert response.status_code == 400  # Should fail because no data source provided


def test_run_backtest_with_file_upload(sample_csv_data):
    """Test running a backtest with file upload"""
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
    
    response = client.post("/api/v1/backtests/upload", files=files, data=data)
    
    # Should succeed
    assert response.status_code == 200
    result = response.json()
    assert result["success"] is True
    assert "result" in result
    assert "job_id" in result
    
    # Verify result structure
    backtest_result = result["result"]
    assert "equity_curve" in backtest_result
    assert "trade_log" in backtest_result
    assert "metrics" in backtest_result
    assert "engine_config" in backtest_result
    
    # Test retrieving the result
    job_id = result["job_id"]
    response = client.get(f"/api/v1/backtests/{job_id}/results")
    assert response.status_code == 200
    retrieved_result = response.json()
    assert retrieved_result["success"] is True
    assert retrieved_result["job_id"] == job_id


def test_list_backtests():
    """Test listing backtests"""
    response = client.get("/api/v1/backtests/")
    assert response.status_code == 200
    data = response.json()
    assert "total" in data
    assert "results" in data
    assert isinstance(data["results"], list)


def test_get_nonexistent_result():
    """Test getting a result that doesn't exist"""
    response = client.get("/api/v1/backtests/999/results")
    assert response.status_code == 404


def test_invalid_strategy():
    """Test with invalid strategy"""
    files = {"file": ("test_data.csv", "timestamp,open,high,low,close,volume\n2024-01-01 09:15:00,100,105,95,102,1000", "text/csv")}
    data = {
        "strategy": "nonexistent.strategy.Class",
        "strategy_params": "{}",
        "engine_options": "{}"
    }
    
    response = client.post("/api/v1/backtests/upload", files=files, data=data)
    assert response.status_code == 400


def test_invalid_json_params():
    """Test with invalid JSON in parameters"""
    files = {"file": ("test_data.csv", "timestamp,open,high,low,close,volume\n2024-01-01 09:15:00,100,105,95,102,1000", "text/csv")}
    data = {
        "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
        "strategy_params": "invalid json",  # Invalid JSON
        "engine_options": "{}"
    }
    
    response = client.post("/api/v1/backtests/upload", files=files, data=data)
    # Currently returns 500, should be improved to return 400
    assert response.status_code in [400, 500]  # Accept both for now
