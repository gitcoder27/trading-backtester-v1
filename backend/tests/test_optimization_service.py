"""
Test optimization service functionality
"""

import pytest
import pandas as pd
import numpy as np
from backend.app.services.optimization_service import OptimizationService, create_parameter_range
from backend.app.database.models import init_db, get_session_factory, Dataset
from datetime import datetime
import tempfile
import os


@pytest.fixture(scope="module")
def optimization_service():
    """Create optimization service instance"""
    init_db()  # Initialize test database
    return OptimizationService()


@pytest.fixture
def sample_dataset():
    """Create a sample dataset for testing"""
    # Create sample market data
    dates = pd.date_range(start='2024-01-01', end='2024-01-03', freq='1min')
    data = []
    
    price = 100.0
    for date in dates:
        # Simple random walk
        price *= (1 + np.random.normal(0, 0.001))
        
        data.append({
            'timestamp': date,
            'open': price,
            'high': price * (1 + abs(np.random.normal(0, 0.005))),
            'low': price * (1 - abs(np.random.normal(0, 0.005))),
            'close': price,
            'volume': np.random.randint(1000, 10000)
        })
    
    df = pd.DataFrame(data)
    
    # Save to temporary file
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    df.to_csv(temp_file.name, index=False)
    temp_file.close()
    
    # Create dataset record in database
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        dataset = Dataset(
            name="test_dataset",
            filename=os.path.basename(temp_file.name),
            file_path=temp_file.name,
            file_size=os.path.getsize(temp_file.name),
            rows_count=len(df),
            columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'],
            created_at=datetime.utcnow()
        )
        db.add(dataset)
        db.commit()
        db.refresh(dataset)
        
        yield dataset.id
        
        # Cleanup
        db.query(Dataset).filter(Dataset.id == dataset.id).delete()
        db.commit()
        os.unlink(temp_file.name)
    finally:
        db.close()


def test_optimization_service_initialization(optimization_service):
    """Test optimization service can be initialized"""
    assert optimization_service is not None
    assert hasattr(optimization_service, 'backtest_service')
    assert hasattr(optimization_service, 'job_runner')


def test_parameter_range_creation():
    """Test parameter range creation helpers"""
    # Test range type
    range_config = create_parameter_range('range', start=10, stop=50, step=5)
    assert range_config['type'] == 'range'
    assert range_config['start'] == 10
    assert range_config['stop'] == 50
    assert range_config['step'] == 5
    
    # Test choice type
    choice_config = create_parameter_range('choice', values=[14, 21, 28])
    assert choice_config['type'] == 'choice'
    assert choice_config['values'] == [14, 21, 28]


def test_generate_parameter_combinations(optimization_service):
    """Test parameter combination generation"""
    param_ranges = {
        'param1': {
            'type': 'range',
            'start': 10,
            'stop': 20,
            'step': 5
        },
        'param2': {
            'type': 'choice',
            'values': [0.1, 0.2, 0.3]
        }
    }
    
    combinations = optimization_service._generate_parameter_combinations(param_ranges)
    
    # Should have 3 values for param1 (10, 15, 20) * 3 values for param2 = 9 combinations
    assert len(combinations) == 9
    
    # Check structure
    for combo in combinations:
        assert 'param1' in combo
        assert 'param2' in combo
        assert combo['param1'] in [10, 15, 20]
        assert combo['param2'] in [0.1, 0.2, 0.3]


def test_split_data(optimization_service):
    """Test data splitting for validation"""
    # Create sample data
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01', periods=100, freq='H'),
        'close': np.random.randn(100)
    })
    
    # Test 30% validation split
    train_data, validation_data = optimization_service._split_data(data, 0.3)
    
    assert len(train_data) == 70
    assert len(validation_data) == 30
    assert len(train_data) + len(validation_data) == len(data)
    
    # Test edge cases
    train_data, validation_data = optimization_service._split_data(data, 0.0)
    assert len(train_data) == 100
    assert len(validation_data) == 0


def test_start_optimization_job_validation(optimization_service):
    """Test optimization job validation"""
    # Test with non-existent dataset
    result = optimization_service.start_optimization_job(
        strategy_path="strategies.ema10_scalper.EMA10ScalperStrategy",
        dataset_id=99999,
        param_ranges={'param1': {'type': 'choice', 'values': [1, 2, 3]}},
        optimization_metric='sharpe_ratio'
    )
    
    assert result['success'] is False
    assert 'not found' in result['error'].lower()


def test_start_optimization_job_too_many_combinations(optimization_service, sample_dataset):
    """Test optimization job with too many parameter combinations"""
    # Create a parameter range that would generate too many combinations
    param_ranges = {
        'param1': {
            'type': 'range',
            'start': 1,
            'stop': 100,
            'step': 1
        },
        'param2': {
            'type': 'range',
            'start': 1,
            'stop': 20,
            'step': 1
        }
    }
    
    result = optimization_service.start_optimization_job(
        strategy_path="strategies.ema10_scalper.EMA10ScalperStrategy",
        dataset_id=sample_dataset,
        param_ranges=param_ranges,
        optimization_metric='sharpe_ratio'
    )
    
    assert result['success'] is False
    assert 'too many combinations' in result['error'].lower()


def test_optimization_time_estimation(optimization_service):
    """Test optimization time estimation"""
    # Test with different numbers of combinations
    assert optimization_service._estimate_optimization_time(10) > 0
    assert optimization_service._estimate_optimization_time(100) > optimization_service._estimate_optimization_time(10)


def test_parameter_sensitivity_analysis(optimization_service):
    """Test parameter sensitivity analysis"""
    # Create mock optimization results
    results = [
        {
            'parameters': {'param1': 10, 'param2': 0.1},
            'optimization_score': 1.5,
            'status': 'completed'
        },
        {
            'parameters': {'param1': 15, 'param2': 0.1},
            'optimization_score': 1.8,
            'status': 'completed'
        },
        {
            'parameters': {'param1': 20, 'param2': 0.1},
            'optimization_score': 1.2,
            'status': 'completed'
        },
        {
            'parameters': {'param1': 10, 'param2': 0.2},
            'optimization_score': 1.6,
            'status': 'completed'
        }
    ]
    
    sensitivity = optimization_service._analyze_parameter_sensitivity(results)
    
    assert 'param1' in sensitivity
    assert 'param2' in sensitivity
    
    # Check structure of sensitivity analysis
    for param in ['param1', 'param2']:
        assert 'correlation' in sensitivity[param]
        assert 'score_by_value' in sensitivity[param]
        assert 'unique_values' in sensitivity[param]
        assert 'value_range' in sensitivity[param]


def test_analyze_optimization_results(optimization_service):
    """Test optimization results analysis"""
    # Create mock results
    successful_results = [
        {'optimization_score': 1.5, 'status': 'completed'},
        {'optimization_score': 1.8, 'status': 'completed'},
        {'optimization_score': 1.2, 'status': 'completed'},
        {'optimization_score': 1.6, 'status': 'completed'}
    ]
    
    analysis = optimization_service._analyze_optimization_results(successful_results, 'sharpe_ratio')
    
    assert 'score_statistics' in analysis
    assert 'top_10_results' in analysis
    assert 'performance_distribution' in analysis
    
    # Check statistics
    stats = analysis['score_statistics']
    assert 'mean' in stats
    assert 'std' in stats
    assert 'min' in stats
    assert 'max' in stats
    
    # Verify calculations
    scores = [r['optimization_score'] for r in successful_results]
    assert stats['mean'] == pytest.approx(np.mean(scores))
    assert stats['min'] == min(scores)
    assert stats['max'] == max(scores)


def test_performance_distribution(optimization_service):
    """Test performance distribution creation"""
    scores = [1.0, 1.2, 1.5, 1.8, 2.0, 1.3, 1.7, 1.4, 1.6, 1.9]
    
    distribution = optimization_service._create_performance_distribution(scores)
    
    assert 'bin_centers' in distribution
    assert 'counts' in distribution
    assert len(distribution['bin_centers']) == len(distribution['counts'])
    assert sum(distribution['counts']) == len(scores)


def test_empty_results_handling(optimization_service):
    """Test handling of empty optimization results"""
    empty_results = []
    
    analysis = optimization_service._analyze_optimization_results(empty_results, 'sharpe_ratio')
    assert 'error' in analysis
    
    sensitivity = optimization_service._analyze_parameter_sensitivity(empty_results)
    assert sensitivity == {}


def test_optimization_progress_callback(optimization_service):
    """Test optimization progress callback"""
    callback_result = optimization_service._optimization_progress_callback(5, 10)
    
    assert 'completed' in callback_result
    assert 'total' in callback_result
    assert 'progress_percentage' in callback_result
    assert 'status' in callback_result
    
    assert callback_result['completed'] == 5
    assert callback_result['total'] == 10
    assert callback_result['progress_percentage'] == 50.0


def test_invalid_parameter_ranges(optimization_service):
    """Test handling of invalid parameter ranges"""
    # Test invalid parameter type
    with pytest.raises(ValueError):
        optimization_service._generate_parameter_combinations({
            'param1': {'type': 'invalid_type'}
        })
    
    # Test invalid range specification
    with pytest.raises(ValueError):
        optimization_service._generate_parameter_combinations({
            'param1': {'type': 'range', 'start': 'invalid', 'stop': 10}
        })
    
    # Test invalid configuration format
    with pytest.raises(ValueError):
        optimization_service._generate_parameter_combinations({
            'param1': 'invalid_config'
        })


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
