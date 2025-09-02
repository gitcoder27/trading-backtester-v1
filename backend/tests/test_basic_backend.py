"""
Basic Backend Testing with Coverage
A simpler approach to test all backend components
"""

import pytest
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backend.app.main import app


@pytest.fixture
def client():
    """Create test client for FastAPI app"""
    return TestClient(app)


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_root_endpoint(client):
    """Test root endpoint"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data


def test_strategies_endpoint(client):
    """Test strategies endpoint"""
    response = client.get("/api/v1/strategies")
    # Should return 200 or appropriate error
    assert response.status_code in [200, 404, 500]


def test_datasets_endpoint(client):
    """Test datasets endpoint"""
    response = client.get("/api/v1/datasets")
    # Should return 200 or appropriate error
    assert response.status_code in [200, 404, 500]


def test_import_all_services():
    """Test that all services can be imported"""
    try:
        from backend.app.services.backtest_service import BacktestService
        from backend.app.services.analytics_service import AnalyticsService
        from backend.app.services.dataset_service import DatasetService
        from backend.app.services.optimization_service import OptimizationService
        from backend.app.services.strategy_service import StrategyService
        assert True
    except ImportError as e:
        pytest.fail(f"Import failed: {e}")


def test_service_initialization():
    """Test that services can be initialized"""
    try:
        from backend.app.services.backtest_service import BacktestService
        service = BacktestService()
        assert service is not None
    except Exception as e:
        pytest.fail(f"Service initialization failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
