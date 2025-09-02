"""
Tests for strategy registry and validation functionality (Phase 3)
"""

import pytest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

from backend.app.services.strategy_service import StrategyRegistry
from backend.app.database.models import create_tables


@pytest.fixture
def temp_db():
    """Create a temporary database for testing"""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
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
def strategy_registry(temp_db):
    """Create a StrategyRegistry instance with test database"""
    with patch('backend.app.database.models.DATABASE_URL', f"sqlite:///{temp_db}"):
        registry = StrategyRegistry()
        yield registry


@pytest.fixture
def temp_strategies_dir():
    """Create a temporary strategies directory with sample strategy"""
    with tempfile.TemporaryDirectory() as temp_dir:
        strategies_dir = Path(temp_dir) / "strategies"
        strategies_dir.mkdir()
        
        # Create __init__.py
        (strategies_dir / "__init__.py").write_text("")
        
        # Create a sample strategy file
        sample_strategy = '''
"""Sample strategy for testing"""
import pandas as pd
from backtester.strategy_base import StrategyBase

class TestStrategy(StrategyBase):
    """A simple test strategy"""
    
    NAME = "Test Strategy"
    
    def __init__(self, ema_period=20, threshold=0.01):
        self.ema_period = ema_period
        self.threshold = threshold
    
    def generate_signals(self, data):
        """Generate simple signals based on EMA"""
        if len(data) < self.ema_period:
            return pd.Series(index=data.index, dtype=float)
        
        ema = data['close'].ewm(span=self.ema_period).mean()
        signals = pd.Series(index=data.index, dtype=float)
        
        # Simple strategy: buy when price is above EMA + threshold
        buy_condition = data['close'] > (ema * (1 + self.threshold))
        sell_condition = data['close'] < (ema * (1 - self.threshold))
        
        signals[buy_condition] = 1.0  # Buy signal
        signals[sell_condition] = -1.0  # Sell signal
        
        return signals
    
    @classmethod
    def get_params_config(cls):
        """Return parameter configuration"""
        return {
            'ema_period': {
                'type': 'int',
                'default': 20,
                'min': 5,
                'max': 100,
                'description': 'EMA period for signal generation'
            },
            'threshold': {
                'type': 'float',
                'default': 0.01,
                'min': 0.001,
                'max': 0.1,
                'description': 'Threshold for signal generation'
            }
        }
'''
        
        (strategies_dir / "test_strategy.py").write_text(sample_strategy)
        
        # Add to Python path
        if str(temp_dir) not in sys.path:
            sys.path.insert(0, str(temp_dir))
        
        yield strategies_dir
        
        # Clean up Python path
        if str(temp_dir) in sys.path:
            sys.path.remove(str(temp_dir))


def test_strategy_registry_initialization(strategy_registry):
    """Test StrategyRegistry can be initialized"""
    assert strategy_registry is not None
    assert strategy_registry.strategies_dir == Path("strategies")


def test_discover_strategies(temp_strategies_dir):
    """Test strategy discovery"""
    registry = StrategyRegistry(strategies_dir=str(temp_strategies_dir))
    strategies = registry.discover_strategies()
    
    assert len(strategies) == 1
    strategy = strategies[0]
    
    assert strategy['name'] == "Test Strategy"
    assert strategy['class_name'] == "TestStrategy"
    assert strategy['module_path'] == "strategies.test_strategy"
    assert strategy['is_valid'] is True
    assert 'parameters_schema' in strategy
    assert 'default_parameters' in strategy


def test_strategy_parameter_extraction(temp_strategies_dir):
    """Test parameter extraction from strategy"""
    registry = StrategyRegistry(strategies_dir=str(temp_strategies_dir))
    strategies = registry.discover_strategies()
    
    strategy = strategies[0]
    
    # Check parameters schema
    schema = strategy['parameters_schema']
    assert 'ema_period' in schema
    assert 'threshold' in schema
    assert schema['ema_period']['type'] == 'int'
    assert schema['threshold']['type'] == 'float'
    
    # Check default parameters
    defaults = strategy['default_parameters']
    assert defaults['ema_period'] == 20
    assert defaults['threshold'] == 0.01


def test_register_strategies(strategy_registry, temp_strategies_dir):
    """Test strategy registration"""
    strategy_registry.strategies_dir = Path(temp_strategies_dir)
    
    result = strategy_registry.register_strategies()
    
    assert result['success'] is True
    assert result['registered'] == 1
    assert result['discovered'] == 1
    assert len(result['errors']) == 0


def test_list_strategies(strategy_registry, temp_strategies_dir):
    """Test listing registered strategies"""
    strategy_registry.strategies_dir = Path(temp_strategies_dir)
    
    # Register strategies first
    strategy_registry.register_strategies()
    
    # List strategies
    strategies = strategy_registry.list_strategies()
    
    assert len(strategies) == 1
    strategy = strategies[0]
    
    assert 'id' in strategy
    assert strategy['name'] == "Test Strategy"
    assert strategy['is_active'] is True


def test_get_strategy_metadata(strategy_registry, temp_strategies_dir):
    """Test getting strategy metadata"""
    strategy_registry.strategies_dir = Path(temp_strategies_dir)
    
    # Register strategies first
    strategy_registry.register_strategies()
    
    # Get all strategies to find the ID
    strategies = strategy_registry.list_strategies()
    strategy_id = strategies[0]['id']
    
    # Get metadata
    metadata = strategy_registry.get_strategy_metadata(strategy_id)
    
    assert metadata['name'] == "Test Strategy"
    assert 'parameters_schema' in metadata
    assert 'default_parameters' in metadata


def test_validate_strategy_success(strategy_registry, temp_strategies_dir):
    """Test successful strategy validation"""
    strategy_registry.strategies_dir = Path(temp_strategies_dir)
    
    # Register strategies first
    strategy_registry.register_strategies()
    
    # Get strategy ID
    strategies = strategy_registry.list_strategies()
    strategy_id = strategies[0]['id']
    
    # Validate strategy
    result = strategy_registry.validate_strategy(strategy_id)
    
    assert result['is_valid'] is True
    assert len(result['errors']) == 0
    assert 'Signal generation successful' in result['tests_passed']


def test_validate_strategy_with_custom_data(strategy_registry, temp_strategies_dir):
    """Test strategy validation with custom data"""
    strategy_registry.strategies_dir = Path(temp_strategies_dir)
    
    # Register strategies first
    strategy_registry.register_strategies()
    
    # Get strategy ID
    strategies = strategy_registry.list_strategies()
    strategy_id = strategies[0]['id']
    
    # Create custom sample data
    dates = pd.date_range('2024-01-01 09:15:00', periods=50, freq='1min')
    sample_data = pd.DataFrame({
        'open': np.random.uniform(100, 110, 50),
        'high': np.random.uniform(110, 115, 50),
        'low': np.random.uniform(95, 100, 50),
        'close': np.random.uniform(100, 110, 50),
        'volume': np.random.randint(1000, 5000, 50)
    }, index=dates)
    sample_data.index.name = 'timestamp'
    
    csv_data = sample_data.to_csv().encode('utf-8')
    
    # Validate with custom data
    result = strategy_registry.validate_strategy(
        strategy_id=strategy_id,
        sample_data=csv_data,
        parameters={'ema_period': 10, 'threshold': 0.02}
    )
    
    assert result['is_valid'] is True
    assert len(result['errors']) == 0


def test_validate_strategy_by_path(strategy_registry, temp_strategies_dir):
    """Test strategy validation by module path"""
    # Validate strategy by path without registration
    result = strategy_registry.validate_strategy_by_path(
        module_path="strategies.test_strategy",
        class_name="TestStrategy",
        parameters={'ema_period': 15}
    )
    
    assert result['is_valid'] is True
    assert len(result['errors']) == 0


def test_validate_nonexistent_strategy(strategy_registry):
    """Test validation of nonexistent strategy"""
    with pytest.raises(ValueError):
        strategy_registry.validate_strategy(999)


def test_validate_invalid_strategy():
    """Test validation of invalid strategy"""
    registry = StrategyRegistry()
    
    # Try to validate a non-existent module
    result = registry.validate_strategy_by_path(
        module_path="nonexistent.module",
        class_name="NonexistentStrategy"
    )
    
    assert result['is_valid'] is False
    assert len(result['errors']) > 0
    assert 'Import error' in result['errors'][0]


def test_strategy_discovery_error_handling(tmp_path):
    """Test error handling during strategy discovery"""
    strategies_dir = tmp_path / "strategies"
    strategies_dir.mkdir()
    
    # Create invalid Python file
    (strategies_dir / "invalid_strategy.py").write_text("invalid python syntax $$$ !!!")
    
    registry = StrategyRegistry(strategies_dir=str(strategies_dir))
    strategies = registry.discover_strategies()
    
    # Should return one strategy with error info
    assert len(strategies) == 1
    strategy = strategies[0]
    assert strategy['is_valid'] is False
    assert 'error' in strategy


def test_sample_data_creation(strategy_registry):
    """Test sample data creation"""
    sample_df = strategy_registry._create_sample_data()
    
    assert len(sample_df) == 100
    assert list(sample_df.columns) == ['open', 'high', 'low', 'close', 'volume']
    assert sample_df.index.name == 'timestamp'
    assert all(sample_df['high'] >= sample_df['low'])
    assert all(sample_df['high'] >= sample_df['open'])
    assert all(sample_df['high'] >= sample_df['close'])
    assert all(sample_df['low'] <= sample_df['open'])
    assert all(sample_df['low'] <= sample_df['close'])
