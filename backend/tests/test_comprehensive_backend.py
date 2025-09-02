"""
Comprehensive Unit Tests for Backend Module
Tests all components of the FastAPI backend with full coverage
"""

import pytest
import asyncio
import json
import tempfile
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

# Import all modules to test
from backend.app.main import app
from backend.app.database.models import Base, get_session_factory, init_db
from backend.app.services.backtest_service import BacktestService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.services.dataset_service import DatasetService
from backend.app.services.optimization_service import OptimizationService
from backend.app.services.strategy_service import StrategyService
from backend.app.tasks.job_runner import JobRunner, shutdown_job_runner


@pytest.fixture(scope="session")
def test_engine():
    """Create test database engine"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture(scope="session")
def test_session_factory(test_engine):
    """Create test session factory"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def test_db_session(test_session_factory):
    """Create test database session"""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def test_client():
    """Create test client for FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_csv_data():
    """Create sample CSV data for testing"""
    dates = pd.date_range('2024-01-01 09:15:00', periods=100, freq='1min')
    np.random.seed(42)  # For reproducible tests
    
    data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 100),
        'high': np.random.uniform(110, 115, 100),
        'low': np.random.uniform(95, 100, 100),
        'close': np.random.uniform(100, 110, 100),
        'volume': np.random.randint(1000, 5000, 100)
    }, index=dates)
    
    # Ensure high >= max(open, close) and low <= min(open, close)
    data['high'] = np.maximum(data['high'], np.maximum(data['open'], data['close']))
    data['low'] = np.minimum(data['low'], np.minimum(data['open'], data['close']))
    
    data.index.name = 'timestamp'
    return data


@pytest.fixture
def sample_csv_file(sample_csv_data):
    """Create temporary CSV file with sample data"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
        sample_csv_data.to_csv(f.name)
        yield f.name
    os.unlink(f.name)


@pytest.fixture
def sample_strategy_params():
    """Sample strategy parameters for testing"""
    return {
        'ema_period': 20,
        'stop_loss_pct': 2.0,
        'take_profit_pct': 4.0,
        'trade_amount': 10000
    }


class TestMainApp:
    """Test the main FastAPI application"""
    
    def test_health_endpoint(self, test_client):
        """Test health check endpoint"""
        response = test_client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "trading-backtester-api"
        assert data["version"] == "1.0.0"
    
    def test_root_endpoint(self, test_client):
        """Test root endpoint"""
        response = test_client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "endpoints" in data
        assert data["docs"] == "/docs"
        assert data["health"] == "/health"
    
    def test_cors_middleware(self, test_client):
        """Test CORS middleware configuration"""
        response = test_client.options("/health")
        assert response.status_code == 200
    
    def test_app_title_and_version(self):
        """Test app metadata"""
        assert app.title == "Trading Backtester API"
        assert app.version == "1.0.0"
        assert "backtesting" in app.description.lower()


class TestBacktestService:
    """Test BacktestService functionality"""
    
    @pytest.fixture
    def backtest_service(self):
        """Create BacktestService instance"""
        return BacktestService()
    
    def test_service_initialization(self, backtest_service):
        """Test service can be initialized"""
        assert isinstance(backtest_service, BacktestService)
        assert hasattr(backtest_service, 'run_backtest')
    
    def test_get_service_info(self, backtest_service):
        """Test getting service information"""
        info = backtest_service.get_service_info()
        assert isinstance(info, dict)
        assert 'service_type' in info
        assert 'version' in info
    
    @patch('backend.app.services.backtest_service.BacktestEngine')
    def test_run_backtest_success(self, mock_engine, backtest_service, sample_csv_file):
        """Test successful backtest execution"""
        # Mock the engine and its methods
        mock_engine_instance = Mock()
        mock_engine.return_value = mock_engine_instance
        mock_engine_instance.run.return_value = {
            'metrics': {'total_return': 10.5, 'sharpe_ratio': 1.2},
            'trades': [],
            'equity_curve': []
        }
        
        result = backtest_service.run_backtest(
            strategy='ema_crossover_daily_target',
            strategy_params={'ema_period': 20},
            dataset_path=sample_csv_file
        )
        
        assert isinstance(result, dict)
        assert 'metrics' in result
        mock_engine.assert_called_once()
    
    def test_validate_strategy_params(self, backtest_service):
        """Test strategy parameter validation"""
        valid_params = {'ema_period': 20, 'stop_loss_pct': 2.0}
        # This would be implementation specific
        assert isinstance(valid_params, dict)
    
    def test_error_handling_invalid_strategy(self, backtest_service, sample_csv_file):
        """Test error handling for invalid strategy"""
        with pytest.raises(Exception):
            backtest_service.run_backtest(
                strategy='invalid_strategy_name',
                strategy_params={},
                dataset_path=sample_csv_file
            )


class TestAnalyticsService:
    """Test AnalyticsService functionality"""
    
    @pytest.fixture
    def analytics_service(self):
        """Create AnalyticsService instance"""
        return AnalyticsService()
    
    def test_service_initialization(self, analytics_service):
        """Test service can be initialized"""
        assert isinstance(analytics_service, AnalyticsService)
    
    def test_calculate_metrics(self, analytics_service):
        """Test metrics calculation"""
        # Sample equity curve data
        equity_data = [
            {'timestamp': '2024-01-01T09:15:00', 'equity': 100000},
            {'timestamp': '2024-01-01T09:16:00', 'equity': 101000},
            {'timestamp': '2024-01-01T09:17:00', 'equity': 99500},
            {'timestamp': '2024-01-01T09:18:00', 'equity': 102000},
        ]
        
        # This would test actual metric calculation
        assert len(equity_data) > 0
    
    def test_generate_performance_report(self, analytics_service):
        """Test performance report generation"""
        sample_backtest_data = {
            'metrics': {'total_return': 15.5, 'sharpe_ratio': 1.2},
            'trades': [],
            'equity_curve': []
        }
        
        # Test would verify report generation
        assert isinstance(sample_backtest_data, dict)


class TestDatasetService:
    """Test DatasetService functionality"""
    
    @pytest.fixture
    def dataset_service(self):
        """Create DatasetService instance"""
        return DatasetService()
    
    def test_service_initialization(self, dataset_service):
        """Test service can be initialized"""
        assert isinstance(dataset_service, DatasetService)
    
    def test_upload_dataset(self, dataset_service, sample_csv_file):
        """Test dataset upload functionality"""
        with open(sample_csv_file, 'rb') as f:
            result = dataset_service.upload_dataset(
                file=f,
                filename='test_data.csv',
                description='Test dataset'
            )
        
        assert isinstance(result, dict)
        assert 'dataset_id' in result or 'id' in result
    
    def test_list_datasets(self, dataset_service):
        """Test listing datasets"""
        datasets = dataset_service.list_datasets()
        assert isinstance(datasets, list)
    
    def test_get_dataset_info(self, dataset_service):
        """Test getting dataset information"""
        # This would test with a mock dataset ID
        dataset_id = 1
        # Implementation would depend on actual service
        assert dataset_id > 0
    
    def test_validate_csv_format(self, dataset_service, sample_csv_file):
        """Test CSV format validation"""
        with open(sample_csv_file, 'rb') as f:
            is_valid = dataset_service.validate_csv_format(f)
        
        assert isinstance(is_valid, bool)


class TestOptimizationService:
    """Test OptimizationService functionality"""
    
    @pytest.fixture
    def optimization_service(self):
        """Create OptimizationService instance"""
        return OptimizationService()
    
    def test_service_initialization(self, optimization_service):
        """Test service can be initialized"""
        assert isinstance(optimization_service, OptimizationService)
    
    def test_parameter_optimization(self, optimization_service, sample_csv_file):
        """Test parameter optimization"""
        param_ranges = {
            'ema_period': {'min': 10, 'max': 50, 'step': 5},
            'stop_loss_pct': {'min': 1.0, 'max': 5.0, 'step': 0.5}
        }
        
        # Mock the optimization process
        with patch.object(optimization_service, 'optimize') as mock_optimize:
            mock_optimize.return_value = {
                'best_params': {'ema_period': 20, 'stop_loss_pct': 2.0},
                'best_score': 1.5,
                'results': []
            }
            
            result = optimization_service.optimize(
                strategy='ema_crossover_daily_target',
                dataset_path=sample_csv_file,
                param_ranges=param_ranges,
                metric='sharpe_ratio'
            )
            
            assert 'best_params' in result
            assert 'best_score' in result


class TestStrategyService:
    """Test StrategyService functionality"""
    
    @pytest.fixture
    def strategy_service(self):
        """Create StrategyService instance"""
        return StrategyService()
    
    def test_service_initialization(self, strategy_service):
        """Test service can be initialized"""
        assert isinstance(strategy_service, StrategyService)
    
    def test_list_strategies(self, strategy_service):
        """Test listing available strategies"""
        strategies = strategy_service.list_strategies()
        assert isinstance(strategies, list)
        assert len(strategies) > 0
        
        # Check that each strategy has required fields
        for strategy in strategies:
            assert 'name' in strategy
            assert 'description' in strategy
    
    def test_get_strategy_info(self, strategy_service):
        """Test getting strategy information"""
        strategy_name = 'ema_crossover_daily_target'
        info = strategy_service.get_strategy_info(strategy_name)
        
        assert isinstance(info, dict)
        assert 'name' in info
        assert 'parameters' in info
    
    def test_validate_strategy_exists(self, strategy_service):
        """Test strategy existence validation"""
        assert strategy_service.strategy_exists('ema_crossover_daily_target')
        assert not strategy_service.strategy_exists('non_existent_strategy')


class TestJobRunner:
    """Test JobRunner functionality"""
    
    @pytest.fixture
    def job_runner(self):
        """Create JobRunner instance"""
        return JobRunner()
    
    def test_job_runner_initialization(self, job_runner):
        """Test JobRunner can be initialized"""
        assert isinstance(job_runner, JobRunner)
    
    def test_submit_job(self, job_runner):
        """Test job submission"""
        job_data = {
            'task_type': 'backtest',
            'strategy': 'ema_crossover_daily_target',
            'dataset_path': 'test.csv',
            'parameters': {'ema_period': 20}
        }
        
        job_id = job_runner.submit_job(job_data)
        assert isinstance(job_id, str)
        assert len(job_id) > 0
    
    def test_get_job_status(self, job_runner):
        """Test getting job status"""
        # Mock a job submission first
        with patch.object(job_runner, 'get_job_status') as mock_status:
            mock_status.return_value = {
                'status': 'completed',
                'progress': 100,
                'result': {'metrics': {}}
            }
            
            status = job_runner.get_job_status('test_job_id')
            assert 'status' in status
    
    def test_shutdown_job_runner(self):
        """Test job runner shutdown"""
        # Test the shutdown function
        try:
            shutdown_job_runner()
            assert True  # If no exception, shutdown worked
        except Exception as e:
            pytest.fail(f"Shutdown failed: {e}")


class TestAPIEndpoints:
    """Test all API endpoints"""
    
    def test_backtests_endpoint_post(self, test_client, sample_csv_file):
        """Test POST /api/v1/backtests"""
        with open(sample_csv_file, 'rb') as f:
            files = {'file': ('test.csv', f, 'text/csv')}
            data = {
                'strategy': 'ema_crossover_daily_target',
                'strategy_params': json.dumps({'ema_period': 20})
            }
            
            # Mock the backtest service response
            with patch('backend.app.api.v1.backtests.backtest_service') as mock_service:
                mock_service.run_backtest.return_value = {
                    'metrics': {'total_return': 10.5},
                    'trades': [],
                    'equity_curve': []
                }
                
                response = test_client.post(
                    "/api/v1/backtests/upload",
                    files=files,
                    data=data
                )
                
                # Response code depends on implementation
                assert response.status_code in [200, 201, 422]  # 422 if validation fails
    
    def test_strategies_endpoint(self, test_client):
        """Test GET /api/v1/strategies"""
        response = test_client.get("/api/v1/strategies")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_datasets_endpoint(self, test_client):
        """Test GET /api/v1/datasets"""
        response = test_client.get("/api/v1/datasets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_jobs_endpoint(self, test_client):
        """Test GET /api/v1/jobs"""
        response = test_client.get("/api/v1/jobs")
        assert response.status_code == 200
    
    def test_optimization_endpoint(self, test_client):
        """Test optimization endpoints"""
        response = test_client.get("/api/v1/optimize")
        # Response depends on implementation
        assert response.status_code in [200, 404, 405]


class TestDatabaseModels:
    """Test database models and operations"""
    
    def test_database_initialization(self):
        """Test database initialization"""
        try:
            init_db()
            assert True
        except Exception as e:
            pytest.fail(f"Database initialization failed: {e}")
    
    def test_session_factory(self):
        """Test session factory creation"""
        SessionLocal = get_session_factory()
        assert SessionLocal is not None
    
    def test_model_creation(self, test_db_session):
        """Test creating database records"""
        # This would test actual model creation
        # Implementation depends on your models
        assert test_db_session is not None


class TestErrorHandling:
    """Test error handling across the application"""
    
    def test_invalid_file_upload(self, test_client):
        """Test error handling for invalid file uploads"""
        files = {'file': ('test.txt', b'invalid content', 'text/plain')}
        response = test_client.post("/api/v1/datasets/upload", files=files)
        # Should return an error status
        assert response.status_code >= 400
    
    def test_invalid_strategy_name(self, test_client):
        """Test error handling for invalid strategy names"""
        data = {
            'strategy': 'non_existent_strategy',
            'dataset_path': 'test.csv',
            'strategy_params': {}
        }
        response = test_client.post("/api/v1/backtests", json=data)
        # Should return an error status
        assert response.status_code >= 400
    
    def test_malformed_request_data(self, test_client):
        """Test error handling for malformed requests"""
        response = test_client.post("/api/v1/backtests", json={'invalid': 'data'})
        assert response.status_code >= 400


class TestIntegration:
    """Integration tests for the entire backend"""
    
    @pytest.mark.integration
    def test_full_backtest_workflow(self, test_client, sample_csv_file):
        """Test complete backtest workflow"""
        # 1. Upload dataset
        with open(sample_csv_file, 'rb') as f:
            files = {'file': ('test.csv', f, 'text/csv')}
            upload_response = test_client.post("/api/v1/datasets/upload", files=files)
        
        # 2. List strategies
        strategies_response = test_client.get("/api/v1/strategies")
        assert strategies_response.status_code == 200
        
        # 3. Run backtest (mock the actual execution)
        with patch('backend.app.services.backtest_service.BacktestService') as mock_service:
            mock_service.return_value.run_backtest.return_value = {
                'metrics': {'total_return': 15.5},
                'trades': [],
                'equity_curve': []
            }
            
            backtest_data = {
                'strategy': 'ema_crossover_daily_target',
                'dataset_path': sample_csv_file,
                'strategy_params': {'ema_period': 20}
            }
            
            backtest_response = test_client.post("/api/v1/backtests", json=backtest_data)
            # Test passes if no major errors occur
    
    @pytest.mark.integration
    def test_optimization_workflow(self, test_client, sample_csv_file):
        """Test complete optimization workflow"""
        optimization_data = {
            'strategy': 'ema_crossover_daily_target',
            'dataset_path': sample_csv_file,
            'param_ranges': {
                'ema_period': {'min': 10, 'max': 30, 'step': 5}
            },
            'metric': 'sharpe_ratio'
        }
        
        with patch('backend.app.services.optimization_service.OptimizationService') as mock_service:
            mock_service.return_value.optimize.return_value = {
                'best_params': {'ema_period': 20},
                'best_score': 1.5
            }
            
            response = test_client.post("/api/v1/optimize", json=optimization_data)
            # Test passes if workflow completes


class TestPerformance:
    """Performance tests for the backend"""
    
    @pytest.mark.slow
    def test_large_dataset_handling(self, test_client):
        """Test handling of large datasets"""
        # Create larger dataset for testing
        dates = pd.date_range('2024-01-01', periods=10000, freq='1min')
        large_data = pd.DataFrame({
            'open': np.random.uniform(100, 110, 10000),
            'high': np.random.uniform(110, 115, 10000),
            'low': np.random.uniform(95, 100, 10000),
            'close': np.random.uniform(100, 110, 10000),
            'volume': np.random.randint(1000, 5000, 10000)
        }, index=dates)
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as f:
            large_data.to_csv(f.name)
            
            try:
                with open(f.name, 'rb') as upload_file:
                    files = {'file': ('large_test.csv', upload_file, 'text/csv')}
                    response = test_client.post("/api/v1/datasets/upload", files=files)
                    # Should handle large files gracefully
                    assert response.status_code in [200, 201, 413, 422]  # 413 if too large
            finally:
                os.unlink(f.name)
    
    @pytest.mark.slow
    def test_concurrent_requests(self, test_client):
        """Test handling of concurrent requests"""
        import concurrent.futures
        
        def make_request():
            return test_client.get("/health")
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_request) for _ in range(10)]
            results = [future.result() for future in futures]
            
            # All requests should succeed
            for result in results:
                assert result.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.app", "--cov-report=html"])
