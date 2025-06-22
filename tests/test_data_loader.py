import pytest
import pandas as pd
from backtester.data_loader import load_csv
import os

@pytest.fixture
def sample_csv_file(tmp_path):
    """Create a temporary sample CSV file for testing."""
    content = """timestamp,open,high,low,close,volume
2023-01-01 09:15:00,100,102,99,101,1000
2023-01-01 09:16:00,101,103,100,102,1200
2023-01-01 09:17:00,102,104,101,103,1100
2023-01-01 09:18:00,103,105,102,104,1300
2023-01-01 09:19:00,104,106,103,105,1050"""
    file_path = tmp_path / "sample_data.csv"
    file_path.write_text(content)
    return str(file_path)

@pytest.fixture
def sample_csv_file_for_resample(tmp_path):
    """Create a temporary sample CSV file for resampling tests."""
    content = """timestamp,open,high,low,close,volume
2023-01-01 09:15:00,100,102,99,101,100
2023-01-01 09:15:30,101,103,100,102,200
2023-01-01 09:16:00,102,104,101,103,300
2023-01-01 09:16:30,103,105,102,104,400
2023-01-01 09:17:00,104,106,103,105,500"""
    file_path = tmp_path / "sample_data_resample.csv"
    file_path.write_text(content)
    return str(file_path)

def test_load_csv_successful(sample_csv_file):
    """Test loading a valid CSV file."""
    df = load_csv(sample_csv_file)
    assert not df.empty
    assert isinstance(df, pd.DataFrame)
    assert 'timestamp' in df.columns
    assert pd.api.types.is_datetime64_any_dtype(df['timestamp'])
    assert list(df.columns) == ['timestamp', 'open', 'high', 'low', 'close', 'volume']
    assert len(df) == 5

def test_load_csv_default_timeframe(sample_csv_file):
    """Test loading with default timeframe '1T' (which implies no resampling if data is already 1min)."""
    df = load_csv(sample_csv_file, timeframe='1T')
    assert len(df) == 5 # No change in length if data is effectively 1-min and timeframe is 1T
    # Check that 'timestamp' is the first column after reset_index
    assert df.columns[0] == 'timestamp'

def test_load_csv_with_resampling(sample_csv_file_for_resample):
    """Test loading and resampling data to a 2-minute timeframe."""
    df = load_csv(sample_csv_file_for_resample, timeframe='2T') # Resample to 2 minutes
    assert not df.empty
    assert len(df) < 5 # Resampling should reduce the number of rows

    # Expected resampled data for 2T:
    # Timestamp              Open  High  Low  Close  Volume
    # 2023-01-01 09:14:00    100   103  99    102    300  (data from 09:15:00, 09:15:30, ends at 09:15:59.99)
    # 2023-01-01 09:16:00    102   105  101   104    700  (data from 09:16:00, 09:16:30, ends at 09:16:59.99)
    # 2023-01-01 09:18:00    104   106  103   105    500  (data from 09:17:00, ends at 09:17:59.99) - this is how pandas resamples by default (label=left)

    # Pandas resampling can be tricky with labels. Default is 'left'.
    # For '2023-01-01 09:14:00' label, it includes data from 09:14:00 up to (but not including) 09:16:00
    # So, for our data:
    # 09:15:00 (o:100, h:102, l:99, c:101, v:100)
    # 09:15:30 (o:101, h:103, l:100, c:102, v:200)
    # These fall into the 09:14:00 bin. Expected: o:100, h:103, l:99, c:102, v:300

    # 09:16:00 (o:102, h:104, l:101, c:103, v:300)
    # 09:16:30 (o:103, h:105, l:102, c:104, v:400)
    # These fall into the 09:16:00 bin. Expected: o:102, h:105, l:101, c:104, v:700

    # 09:17:00 (o:104, h:106, l:103, c:105, v:500)
    # This falls into the 09:16:00 bin if label='right' and closed='right', but with default label='left', closed='left'
    # it would be the start of a new bin labeled 09:16:00.
    # The actual behavior of resample().agg() is:
    # df.set_index('timestamp').resample('2T').agg(...)
    # For 09:15:00, 09:15:30 -> bin [2023-01-01 09:14:00, 2023-01-01 09:16:00) -> label 2023-01-01 09:14:00
    # For 09:16:00, 09:16:30 -> bin [2023-01-01 09:16:00, 2023-01-01 09:18:00) -> label 2023-01-01 09:16:00
    # For 09:17:00          -> bin [2023-01-01 09:16:00, 2023-01-01 09:18:00) -> also label 2023-01-01 09:16:00 (if not careful)
    # Let's re-check the load_csv logic: it sets index, resamples, then resets index.
    # The sample data starts at 09:15:00.
    # Bin 1: [09:15:00, 09:17:00) -> label 09:15:00 (using origin='start_day' or similar effective behavior)
    #   Includes: 09:15:00, 09:15:30, 09:16:00, 09:16:30
    #   Open: 100 (from 09:15:00)
    #   High: max(102,103,104,105) = 105
    #   Low:  min(99,100,101,102) = 99
    #   Close: 104 (from 09:16:30)
    #   Volume: 100+200+300+400 = 1000
    # Bin 2: [09:17:00, 09:19:00) -> label 09:17:00
    #   Includes: 09:17:00
    #   Open: 104
    #   High: 106
    #   Low:  103
    #   Close: 105
    #   Volume: 500
    # So, 2 rows are expected.
    # Actual pandas resampling behavior for this data with '2T'
    # Bin 1: label 09:14:00 (includes 09:15:00, 09:15:30)
    #   Open: 100, High: 103, Low: 99, Close: 102, Volume: 300
    # Bin 2: label 09:16:00 (includes 09:16:00, 09:16:30, 09:17:00)
    #   Open: 102, High: 106, Low: 101, Close: 105, Volume: 1200
    # Timestamps after reset_index will be the labels of these bins.

    assert len(df) == 2 # This part is correct based on the number of bins formed.

    expected_opens = pd.Series([100, 102], name='open')
    expected_highs = pd.Series([103, 106], name='high')
    expected_lows = pd.Series([99, 101], name='low')
    expected_closes = pd.Series([102, 105], name='close')
    expected_volumes = pd.Series([300, 1200], name='volume', dtype=df['volume'].dtype) # Match dtype for volume
    # Timestamps will be the start of the resampled periods if origin is not altered significantly by data start
    # Given data starts at 09:15:00, first bin is [09:14:00, 09:16:00) labeled 09:14:00
    # Second bin is [09:16:00, 09:18:00) labeled 09:16:00
    expected_timestamps = pd.to_datetime(["2023-01-01 09:14:00", "2023-01-01 09:16:00"])

    pd.testing.assert_series_equal(df['open'], expected_opens, check_dtype=False)
    pd.testing.assert_series_equal(df['high'], expected_highs, check_dtype=False)
    pd.testing.assert_series_equal(df['low'], expected_lows, check_dtype=False)
    pd.testing.assert_series_equal(df['close'], expected_closes, check_dtype=False)
    pd.testing.assert_series_equal(df['volume'], expected_volumes, check_dtype=False) # check_dtype=False should be fine for int types too
    pd.testing.assert_series_equal(df['timestamp'], pd.Series(expected_timestamps, name='timestamp'), check_dtype=False)


def test_load_csv_file_not_found():
    """Test loading a non-existent CSV file."""
    with pytest.raises(FileNotFoundError):
        load_csv("non_existent_file.csv")

def test_load_csv_empty_file(tmp_path):
    """Test loading an empty CSV file."""
    file_path = tmp_path / "empty.csv"
    file_path.write_text("") # Empty file
    with pytest.raises(Exception): # pd.read_csv raises EmptyDataError, a subclass of Exception
        load_csv(str(file_path))

def test_load_csv_missing_columns(tmp_path):
    """Test loading a CSV with missing required columns (e.g., 'close')."""
    content = "timestamp,open,high,low\n2023-01-01 09:15:00,100,102,99"
    file_path = tmp_path / "missing_cols.csv"
    file_path.write_text(content)
    # This should raise a KeyError when 'close' is accessed in resample aggregation
    # if resampling is triggered.
    # The current code explicitly lists 'open', 'high', 'low', 'close', 'volume' in agg.
    # If a required column for aggregation (like 'close' or 'volume') is missing, pandas will raise a KeyError.
    # We must trigger resampling for this test to be effective.
    with pytest.raises(KeyError): # Pandas raises KeyError if a named aggregation column is missing during resample().agg()
        load_csv(str(file_path), timeframe='2min') # Force resampling

def test_load_csv_incorrect_timestamp_format(tmp_path):
    """Test loading a CSV with an unparseable timestamp format."""
    content = "timestamp,open,high,low,close,volume\nINVALID_DATE,100,102,99,101,1000"
    file_path = tmp_path / "bad_timestamp.csv"
    file_path.write_text(content)
    # pandas `read_csv` with `parse_dates` for a column that can't be parsed
    # usually raises a `ValueError` or `pd.errors.ParserError` or `pd.errors.DateTimeParseError`.
    # `pd.errors.ParserError` is a good general catch. `ValueError` can also occur.
    # Let's try to be more specific or catch a broader base if versions vary.
    # `pd.to_datetime` can raise `ValueError` or `pd.errors.ParserError`.
    # `read_csv` itself might raise `ValueError` due to parsing.
    # However, pandas often coerces unparseable dates to NaT.
    # Test that NaT is handled, possibly by dropping the row or returning empty.

    # Scenario 1: No resampling (default timeframe)
    df_no_resample = load_csv(str(file_path))
    # Expect empty because the NaT row is dropped by load_csv's dropna(subset=['timestamp'])
    assert df_no_resample.empty

    # Scenario 2: With resampling
    # The NaT row, when indexed, might cause resample().agg() to produce NaNs
    # which are then dropped by .dropna(), resulting in an empty DataFrame.
    df_resampled = load_csv(str(file_path), timeframe='2min')
    assert df_resampled.empty
