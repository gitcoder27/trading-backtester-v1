"""
Tests for dataset management functionality (Phase 3)
"""

import pytest
import tempfile
import os
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch
import json

from backend.app.services.dataset_service import DatasetService
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
def temp_data_dir():
    """Create a temporary data directory"""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


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
    
    return data.to_csv().encode('utf-8')


@pytest.fixture
def dataset_service(temp_db, temp_data_dir):
    """Create a DatasetService instance with test database"""
    with patch('backend.app.database.models.DATABASE_URL', f"sqlite:///{temp_db}"):
        service = DatasetService(data_dir=temp_data_dir)
        yield service


def test_dataset_service_initialization(dataset_service, temp_data_dir):
    """Test DatasetService can be initialized"""
    assert dataset_service is not None
    assert dataset_service.data_dir == Path(temp_data_dir)
    assert dataset_service.data_dir.exists()


def test_upload_dataset(dataset_service, sample_csv_data):
    """Test uploading a dataset"""
    result = dataset_service.upload_dataset(
        file_name="test_data.csv",
        file_content=sample_csv_data,
        name="Test Dataset",
        symbol="TEST",
        exchange="TEST_EXCHANGE"
    )
    
    assert result['success'] is True
    assert 'dataset_id' in result
    assert 'analysis' in result
    
    dataset = result['dataset']
    assert dataset['name'] == "Test Dataset"
    assert dataset['symbol'] == "TEST"
    assert dataset['exchange'] == "TEST_EXCHANGE"
    assert dataset['rows_count'] == 50
    assert 'data_quality_score' in dataset


def test_dataset_quality_analysis(dataset_service, sample_csv_data):
    """Test dataset quality analysis"""
    # Upload dataset first
    result = dataset_service.upload_dataset(
        file_name="test_data.csv",
        file_content=sample_csv_data
    )
    
    dataset_id = result['dataset_id']
    
    # Get quality analysis
    quality_result = dataset_service.get_dataset_quality(dataset_id)
    
    assert quality_result['success'] is True
    assert 'quality_analysis' in quality_result
    
    quality = quality_result['quality_analysis']
    assert 'has_timestamp' in quality
    assert 'required_columns' in quality
    assert 'missing_data' in quality
    assert 'data_types' in quality


def test_list_datasets(dataset_service, sample_csv_data):
    """Test listing datasets"""
    # Upload a few datasets
    for i in range(3):
        dataset_service.upload_dataset(
            file_name=f"test_data_{i}.csv",
            file_content=sample_csv_data,
            name=f"Test Dataset {i}"
        )
    
    # List datasets
    datasets = dataset_service.list_datasets()
    
    assert len(datasets) == 3
    assert all('name' in dataset for dataset in datasets)
    assert all('id' in dataset for dataset in datasets)


def test_delete_dataset(dataset_service, sample_csv_data):
    """Test deleting a dataset"""
    # Upload dataset
    result = dataset_service.upload_dataset(
        file_name="test_data.csv",
        file_content=sample_csv_data
    )
    
    dataset_id = result['dataset_id']
    
    # Delete dataset
    delete_result = dataset_service.delete_dataset(dataset_id)
    
    assert delete_result['success'] is True
    
    # Verify file is deleted
    # The file path should be in the dataset object from upload_dataset result
    dataset_info = result['dataset']
    file_path = Path(dataset_info['file_path'])
    assert not file_path.exists()


def test_dataset_analysis_with_gaps():
    """Test dataset analysis with timestamp gaps"""
    # Create data with gaps
    dates1 = pd.date_range('2024-01-01 09:15:00', periods=10, freq='1min')
    dates2 = pd.date_range('2024-01-01 10:00:00', periods=10, freq='1min')  # 45 min gap
    dates = dates1.append(dates2)
    
    data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(100, 110, 20),
        'high': np.random.uniform(110, 115, 20),
        'low': np.random.uniform(95, 100, 20),
        'close': np.random.uniform(100, 110, 20),
        'volume': np.random.randint(1000, 5000, 20)
    })
    
    csv_data = data.to_csv(index=False).encode('utf-8')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = DatasetService(data_dir=temp_dir)
        result = service.upload_dataset(
            file_name="gap_data.csv",
            file_content=csv_data
        )
    
    analysis = result['analysis']
    assert analysis['has_gaps'] is True
    assert analysis['quality_checks']['timestamp_gaps']['has_gaps'] is True


def _write_sample_csv(path: Path) -> None:
    content = """timestamp,open,high,low,close,volume
2024-01-01 09:15:00,100,101,99,100.5,1000
2024-01-01 09:16:00,100.5,102,100,101,1100
2024-01-01 09:17:00,101,103,100.2,102,1200
"""
    path.write_text(content.strip() + "\n")


def test_discover_local_datasets(dataset_service):
    csv_path = dataset_service.data_dir / "discover_sample.csv"
    _write_sample_csv(csv_path)

    discovered = dataset_service.discover_local_datasets()
    assert isinstance(discovered, list)
    match = next((item for item in discovered if item.get("file_path", "").endswith("discover_sample.csv")), None)
    assert match is not None
    assert match["registered"] is False
    assert match["rows_count"] == 3
    assert match["name"] == "discover_sample.csv"


def test_register_local_datasets(dataset_service):
    csv_path = dataset_service.data_dir / "register_sample.csv"
    _write_sample_csv(csv_path)

    result = dataset_service.register_local_datasets()
    assert result["success"] is True
    assert len(result["registered"]) == 1
    datasets = dataset_service.list_datasets()
    assert len(datasets) == 1
    assert datasets[0]["file_path"].endswith("register_sample.csv")
    assert datasets[0]["name"] == "register_sample.csv"


def test_dataset_analysis_with_missing_data():
    """Test dataset analysis with missing data"""
    data = pd.DataFrame({
        'timestamp': pd.date_range('2024-01-01 09:15:00', periods=10, freq='1min'),
        'open': [100, np.nan, 102, 103, np.nan, 105, 106, 107, 108, 109],
        'high': [110, 111, np.nan, 113, 114, 115, 116, 117, 118, 119],
        'low': [95, 96, 97, np.nan, 99, 100, 101, 102, 103, 104],
        'close': [105, 106, 107, 108, 109, np.nan, 111, 112, 113, 114],
        'volume': [1000, 1100, 1200, 1300, 1400, 1500, 1600, 1700, 1800, 1900]
    })
    
    csv_data = data.to_csv(index=False).encode('utf-8')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = DatasetService(data_dir=temp_dir)
        result = service.upload_dataset(
            file_name="missing_data.csv",
            file_content=csv_data
        )
    
    analysis = result['analysis']
    assert analysis['missing_data_pct'] > 0
    assert analysis['quality_checks']['missing_data']['has_missing'] is True
    assert analysis['quality_score'] < 100  # Should be penalized for missing data


def test_timeframe_detection():
    """Test timeframe detection in dataset analysis"""
    # Test 5-minute data
    dates = pd.date_range('2024-01-01 09:15:00', periods=20, freq='5min')
    data = pd.DataFrame({
        'timestamp': dates,
        'open': np.random.uniform(100, 110, 20),
        'high': np.random.uniform(110, 115, 20),
        'low': np.random.uniform(95, 100, 20),
        'close': np.random.uniform(100, 110, 20),
        'volume': np.random.randint(1000, 5000, 20)
    })
    
    csv_data = data.to_csv(index=False).encode('utf-8')
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = DatasetService(data_dir=temp_dir)
        result = service.upload_dataset(
            file_name="5min_data.csv",
            file_content=csv_data
        )
    
    assert result['dataset']['timeframe'] == "5min"


def test_dataset_analysis_error_handling():
    """Test error handling in dataset analysis"""
    # Test with invalid CSV data
    invalid_csv = b"not,valid,csv,data\nwith,bad,format"
    
    with tempfile.TemporaryDirectory() as temp_dir:
        service = DatasetService(data_dir=temp_dir)
        
        with pytest.raises(ValueError):
            service.upload_dataset(
                file_name="invalid.csv",
                file_content=invalid_csv
            )


def test_dataset_preview(dataset_service, sample_csv_data):
    """Ensure dataset preview returns limited rows and aggregate stats."""
    result = dataset_service.upload_dataset(
        file_name="preview.csv",
        file_content=sample_csv_data,
    )

    dataset_id = result['dataset_id']
    preview = dataset_service.preview_dataset(dataset_id, rows=5)

    assert preview['success'] is True
    assert preview['dataset_id'] == dataset_id
    assert len(preview['preview']) == 5
    assert preview['total_rows'] == 50
    assert 'open' in preview['statistics']
    stats = preview['statistics']['open']
    assert all(key in stats for key in ['mean', 'std', 'min', 'max', 'count'])


def test_nonexistent_dataset_operations(dataset_service):
    """Test operations on nonexistent datasets"""
    # Test getting quality of nonexistent dataset
    with pytest.raises(ValueError):
        dataset_service.get_dataset_quality(999)
    
    # Test deleting nonexistent dataset
    with pytest.raises(ValueError):
        dataset_service.delete_dataset(999)
