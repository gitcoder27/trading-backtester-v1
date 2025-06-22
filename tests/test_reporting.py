import pytest
import pandas as pd
import os
import plotly.graph_objs as go
from plotly.graph_objs import Figure as OriginalPlotlyFigure # Store real Figure class
from unittest.mock import patch, MagicMock

# Import functions from the re-exporting reporting.py
from backtester.reporting import (
    plot_trades_on_candlestick_plotly,
    plot_equity_curve,
    plot_trades_on_price,
    save_trade_log,
    comparison_table,
    generate_html_report
)
# Also import from submodules if direct testing is preferred or for fixtures
from backtester.plotting import plot_trades_on_candlestick_plotly as ptocp_direct
from backtester.trade_log import save_trade_log as stl_direct
from backtester.comparison import comparison_table as ct_direct
from backtester.html_report import generate_html_report as ghr_direct
from backtester.data_loader import load_csv # For loading sample data

# --- Fixtures ---
@pytest.fixture
def sample_ohlc_data():
    # Load sample data using the project's data_loader
    base_dir = os.path.dirname(__file__)
    csv_path = os.path.join(base_dir, 'fixtures', 'sample_data.csv')
    return load_csv(csv_path)

@pytest.fixture
def sample_trades_df():
    trades = [
        {'trade_id': 1, 'entry_time': '2023-01-01 09:15:00', 'exit_time': '2023-01-01 09:17:00', 'entry_price': 100, 'exit_price': 102, 'pnl': 2, 'direction': 'long'},
        {'trade_id': 2, 'entry_time': '2023-01-01 09:18:00', 'exit_time': '2023-01-01 09:19:00', 'entry_price': 103, 'exit_price': 101, 'pnl': -2, 'direction': 'short'}
    ]
    df = pd.DataFrame(trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    return df

@pytest.fixture
def sample_equity_curve_df():
    timestamps = pd.to_datetime(['2023-01-01 09:15', '2023-01-01 09:16', '2023-01-01 09:17'])
    equity = [10000, 10020, 10010]
    return pd.DataFrame({'timestamp': timestamps, 'equity': equity})

@pytest.fixture
def sample_indicators_df(sample_ohlc_data):
    df = pd.DataFrame({
        'timestamp': sample_ohlc_data['timestamp'],
        'sma_fast': sample_ohlc_data['close'].rolling(window=2).mean(),
        'rsi': pd.Series([50,60,70,40,30] + [0]*(len(sample_ohlc_data)-5))[:len(sample_ohlc_data)] # Simple RSI mock
    }).dropna()
    return df

@pytest.fixture
def sample_indicator_cfg():
    return [
        {'column': 'sma_fast', 'label': 'SMA Fast', 'color': 'blue', 'type': 'solid', 'panel': 1, 'plot': True}, # Changed 'line' to 'solid'
        {'column': 'rsi', 'label': 'RSI', 'color': 'purple', 'type': 'solid', 'panel': 2, 'plot': True}    # Changed 'line' to 'solid'
    ]

@pytest.fixture
def sample_metrics_dict(sample_indicator_cfg): # Pass sample_indicator_cfg as a fixture
    return {
        'Total Return': 0.1, 'Sharpe Ratio': 1.5, 'Max Drawdown': -0.05, 'Win Rate': 0.6,
        'indicator_cfg': sample_indicator_cfg # Use the fixture result directly
    }

# --- Tests for plotting.py functions ---
@patch('plotly.graph_objs.Figure.show') # Mock show to prevent charts appearing during tests
def test_plot_trades_on_candlestick_plotly(mock_show, sample_ohlc_data, sample_trades_df, sample_indicators_df, sample_indicator_cfg):
    """Test plot_trades_on_candlestick_plotly returns a Figure object."""
    fig = plot_trades_on_candlestick_plotly(
        sample_ohlc_data,
        sample_trades_df,
        indicators=sample_indicators_df,
        indicator_cfg=sample_indicator_cfg,
        show=False
    )
    assert isinstance(fig, go.Figure)
    # Check if main candlestick trace is present
    assert any(isinstance(trace, go.Candlestick) for trace in fig.data)
    # Check if trade markers are present (at least 2 per trade: entry + exit)
    # Ensure we only check .mode on Scatter traces
    trade_marker_count = sum(1 for trace in fig.data if isinstance(trace, go.Scatter) and trace.mode == 'markers')
    assert trade_marker_count >= len(sample_trades_df) * 2
    # Check if indicator traces are present
    indicator_trace_count = sum(1 for trace in fig.data if trace.name in [cfg['label'] for cfg in sample_indicator_cfg])
    assert indicator_trace_count == len([cfg for cfg in sample_indicator_cfg if cfg.get('plot',True)])
    # Check for panel 2 y-axis title if RSI is plotted
    if any(cfg['column'] == 'rsi' and cfg.get('panel') == 2 for cfg in sample_indicator_cfg):
         assert fig.layout.yaxis2.title.text == 'RSI'


@patch('plotly.graph_objs.Figure.show')
def test_plot_equity_curve_interactive(mock_show, sample_equity_curve_df):
    """Test plot_equity_curve in interactive mode (Plotly)."""
    # This function in reporting.py calls the one in plotting.py
    # The plotting.py one creates a figure and calls show() if interactive=True
    plot_equity_curve(sample_equity_curve_df, interactive=True)
    mock_show.assert_called_once() # Check that Plotly's show() was called

@patch('matplotlib.pyplot.show') # Mock matplotlib's show
def test_plot_equity_curve_static(mock_show, sample_equity_curve_df):
    """Test plot_equity_curve in static mode (Matplotlib)."""
    plot_equity_curve(sample_equity_curve_df, interactive=False)
    # mock_show.assert_called_once() # For Matplotlib, this would be the check
    # Harder to check if plt.plot was called without more extensive mocking of plt itself.
    # For now, just ensure it runs without error.
    pass


@patch('plotly.graph_objs.Figure.show')
def test_plot_trades_on_price_interactive(mock_show, sample_ohlc_data, sample_trades_df, sample_indicators_df, sample_indicator_cfg):
    """Test plot_trades_on_price in interactive mode."""
    plot_trades_on_price(sample_ohlc_data, sample_trades_df, indicators=sample_indicators_df, indicator_cfg=sample_indicator_cfg, interactive=True)
    mock_show.assert_called_once()

@patch('matplotlib.pyplot.show')
def test_plot_trades_on_price_static(mock_show, sample_ohlc_data, sample_trades_df):
    """Test plot_trades_on_price in static mode."""
    # Static plot_trades_on_price uses matplotlib
    plot_trades_on_price(sample_ohlc_data, sample_trades_df, interactive=False)
    # mock_show.assert_called_once() # Would be for matplotlib
    pass

# --- Tests for trade_log.py functions ---
def test_save_trade_log(tmp_path, sample_trades_df):
    """Test save_trade_log creates a CSV with correct columns."""
    filepath = tmp_path / "tradelog.csv"
    stl_direct(sample_trades_df, str(filepath)) # Use direct import for clarity

    assert filepath.exists()
    df = pd.read_csv(filepath)
    assert 'final_pnl' in df.columns
    assert 'trade_date' in df.columns
    assert 'day_pnl' in df.columns
    assert len(df) == len(sample_trades_df)
    # Check cumulative PnL calculation
    expected_final_pnl = sample_trades_df['pnl'].cumsum()
    pd.testing.assert_series_equal(df['final_pnl'], expected_final_pnl, check_names=False)

# --- Tests for comparison.py functions ---
def test_comparison_table_returns_df():
    """Test comparison_table returns a DataFrame."""
    results_list = [
        {'strategy': 'A', 'total_return': 0.1, 'sharpe': 1.2},
        {'strategy': 'B', 'total_return': 0.2, 'sharpe': 1.5}
    ]
    df = ct_direct(results_list) # Use direct import
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 2
    assert list(df.columns) == ['strategy', 'total_return', 'sharpe']

def test_comparison_table_saves_csv(tmp_path):
    """Test comparison_table saves a CSV when filepath is provided."""
    results_list = [{'strategy': 'A', 'total_return': 0.1}]
    filepath = tmp_path / "comparison.csv"
    ct_direct(results_list, filepath=str(filepath)) # Use direct import

    assert filepath.exists()
    df = pd.read_csv(filepath)
    assert len(df) == 1
    assert df['strategy'].iloc[0] == 'A'

# --- Tests for html_report.py functions ---

# Patch order: bottom-up or use specific `new_callable` if needed. Standard order is fine.
@patch('plotly.graph_objs.Scatter')                     # Mocked as mock_go_scatter
@patch('plotly.offline.plot')                           # Mocked as mock_pyo_plot
@patch('plotly.graph_objs.Figure')                      # Mocked as mock_go_figure_constructor
@patch('backtester.html_report.plot_trades_on_candlestick_plotly') # Mocked as mock_plot_candlestick
def test_generate_html_report(mock_plot_candlestick, mock_go_figure_constructor, mock_pyo_plot, mock_go_scatter, tmp_path, sample_equity_curve_df, sample_ohlc_data, sample_trades_df, sample_indicators_df, sample_metrics_dict):
    """Test generate_html_report creates an HTML file and uses the main candlestick plot path."""

    # Setup for equity curve plot part (first call to go.Figure)
    mock_equity_fig_instance = MagicMock() # Removed spec
    mock_equity_fig_instance.update_layout = MagicMock()
    mock_equity_fig_instance.add_trace = MagicMock()
    # mock_go_figure_constructor is the mock for 'plotly.graph_objs.Figure'
    mock_go_figure_constructor.return_value = mock_equity_fig_instance
    mock_pyo_plot.return_value = "<div>Mock Equity Plot</div>" # plotly.offline.plot for equity curve

    # Setup for the primary candlestick plot path
    mock_candlestick_fig_successful = MagicMock() # Removed spec
    # Ensure to_html itself is a mock that returns the desired string
    mock_candlestick_fig_successful.to_html = MagicMock(return_value="<div>Mock Candlestick Chart HTML</div>")
    mock_plot_candlestick.return_value = mock_candlestick_fig_successful

    report_file = tmp_path / "report.html"

    ghr_direct(
        equity_curve=sample_equity_curve_df,
        data=sample_ohlc_data,
        trades=sample_trades_df,
        indicators=sample_indicators_df,
        metrics=sample_metrics_dict,
        filepath=str(report_file)
    )

    assert report_file.exists()
    content = report_file.read_text()

    assert "<div>Mock Equity Plot</div>" in content # Check equity plot mock
    assert "<div>Mock Candlestick Chart HTML</div>" in content # Check candlestick plot mock

    mock_plot_candlestick.assert_called_once() # Ensure primary candlestick function was called
    # Check args of plot_trades_on_candlestick_plotly
    call_args_list = mock_plot_candlestick.call_args_list
    assert len(call_args_list) == 1
    args, kwargs = call_args_list[0]
    pd.testing.assert_frame_equal(args[0], sample_ohlc_data)
    # trades df gets trade_id added and index reset in html_report.py before passing
    expected_trades_in_call = sample_trades_df.reset_index(drop=True).copy()
    expected_trades_in_call['trade_id'] = expected_trades_in_call.index
    pd.testing.assert_frame_equal(args[1], expected_trades_in_call)
    pd.testing.assert_frame_equal(kwargs['indicators'], sample_indicators_df)
    assert kwargs['indicator_cfg'] == sample_metrics_dict['indicator_cfg']
    assert kwargs['title'] == "Trades on Candlestick Chart"
    assert not kwargs['show']

    # Check calls for equity plot
    mock_go_figure_constructor.assert_called_once() # For equity fig
    mock_pyo_plot.assert_called_once_with(mock_equity_fig_instance, include_plotlyjs=False, output_type='div')

    # Assert that the mock_candlestick_fig_successful.to_html was called correctly
    mock_candlestick_fig_successful.to_html.assert_called_once_with(full_html=False, include_plotlyjs='cdn', div_id='trade_chart')


@patch('plotly.graph_objs.Scatter')                         # Outermost decorator, last mock argument if listed from left to right
@patch('backtester.html_report.plot_trades_on_candlestick_plotly') # Middle decorator
@patch('plotly.graph_objs.Figure')                          # Middle decorator
@patch('plotly.offline.plot')                               # Innermost decorator, first mock argument
def test_generate_html_report_fallback_plotting(mock_pyo_plot, mock_go_figure_constructor, mock_plot_candlestick_main, mock_go_scatter, tmp_path, sample_equity_curve_df, sample_ohlc_data, sample_trades_df): # Removed sample_metrics_dict
    """Test HTML report generation uses fallback if advanced plotting fails."""
    # Parameter order for mocks should be:
    # mock_pyo_plot (from @patch('plotly.offline.plot'))
    # mock_go_figure_constructor (from @patch('plotly.graph_objs.Figure'))
    # mock_plot_candlestick_main (from @patch('backtester.html_report.plot_trades_on_candlestick_plotly'))
    # mock_go_scatter (from @patch('plotly.graph_objs.Scatter'))
    # The current signature is correct based on this bottom-up reading of decorators.

    mock_plot_candlestick_main.side_effect = Exception("Simulated Plotting error for candlestick")

    # Mocks for the equity curve part (first call to go.Figure)
    # 1. @patch('plotly.offline.plot') -> mock_pyo_plot
    # 2. @patch('plotly.graph_objs.Figure') -> mock_go_figure_constructor
    # 3. @patch('backtester.html_report.plot_trades_on_candlestick_plotly') -> mock_plot_candlestick_main
    # 4. @patch('plotly.graph_objs.Scatter') -> mock_go_scatter
    # The signature was (mock_offline_plot, mock_go_figure, mock_ptocp, tmp_path, ...)
    # It should be (mock_go_scatter, mock_ptocp, mock_go_figure, mock_offline_plot, tmp_path, ...)
    # No, the order of parameters in the function definition must match the order of decorators as they appear (from closest to function outwards).
    # So if decorators are:
    # @patch('Scatter') -> mock_go_scatter
    # @patch('plot_trades') -> mock_plot_candlestick_main
    # @patch('Figure') -> mock_go_figure_constructor
    # @patch('offline.plot') -> mock_pyo_plot
    # def test_func(mock_pyo_plot, mock_go_figure_constructor, mock_plot_candlestick_main, mock_go_scatter, ...): is correct.

    mock_plot_candlestick_main.side_effect = Exception("Simulated Plotting error for candlestick")

    # Mocks for the equity curve part (first call to go.Figure)
    mock_equity_fig_instance = MagicMock() # Removed spec
    mock_equity_fig_instance.update_layout = MagicMock()
    mock_equity_fig_instance.add_trace = MagicMock()

    # Mocks for the fallback candlestick part (second call to go.Figure, if primary fails)
    mock_fallback_candlestick_fig_instance = MagicMock() # Removed spec
    mock_fallback_candlestick_fig_instance.to_html.return_value = "<div>Fallback Plotly Chart</div>"
    mock_fallback_candlestick_fig_instance.update_layout = MagicMock()
    mock_fallback_candlestick_fig_instance.add_trace = MagicMock()

    # mock_go_figure_constructor is the mock for 'plotly.graph_objs.Figure'
    mock_go_figure_constructor.side_effect = [mock_equity_fig_instance, mock_fallback_candlestick_fig_instance]
    mock_pyo_plot.return_value = "<div>Equity Curve Plot</div>" # For pyo.plot(eq_fig,...)

    report_file = tmp_path / "report_fallback.html"
    ghr_direct(
        equity_curve=sample_equity_curve_df,
        data=sample_ohlc_data,
        trades=sample_trades_df,
        indicators=None,
        metrics=sample_metrics_dict,
        filepath=str(report_file)
    )

    assert report_file.exists()
    content = report_file.read_text()
    assert "<div>Equity Curve Plot</div>" in content
    assert "<div>Fallback Plotly Chart</div>" in content
    mock_plot_candlestick_main.assert_called_once() # It was called and failed

    # Check that go.Figure was called twice (1 for equity, 1 for fallback candlestick)
    assert mock_go_figure_constructor.call_count == 2
    # Check that offline.plot was called once (for equity)
    mock_pyo_plot.assert_called_once_with(mock_equity_fig_instance, include_plotlyjs=False, output_type='div')

    # Ensure the fallback added traces (Candlestick, trades)
    # This requires checking calls to mock_fallback_candlestick_fig_instance.add_trace
    assert any("Candlestick" in str(call_args) for call_args, _ in mock_fallback_candlestick_fig_instance.add_trace.call_args_list)
    scatter_calls = sum(1 for call_args, _ in mock_fallback_candlestick_fig_instance.add_trace.call_args_list if "Scatter" in str(call_args))
    assert scatter_calls >= len(sample_trades_df) * 3


# Note: For `generate_html_report` test to robustly find `report_template.html`,
# ensure that the `backtester` package structure is correctly understood by the test runner,
# or consider making the template path configurable for tests.
# If `backtester` is installed (e.g., `pip install .`), `__file__` will point to site-packages,
# and the template needs to be there (usually handled by `package_data` in `setup.py`).
# If running from source without install, `PYTHONPATH` needs to be set correctly.
# The current structure assumes `backtester/report_template.html` is found relative to `html_report.py`.
    # This might require copying the template or adjusting paths if tests run from a different CWD.
    # For simplicity, assume it can find it or mock Jinja2's FileSystemLoader.

    # Create a dummy report_template.html in the tmp_path/backtester directory for the test
    # This is because generate_html_report uses FileSystemLoader(os.path.dirname(__file__))
    # which will point to the installed package location, not necessarily the test context.
    # A better solution would be to inject the template path or use a test-specific template.

    # For this test, we'll mock the template loading part if direct file access is complex in testing environment.
    # Let's assume the FileSystemLoader in html_report.py can find the template.
    # The critical part is that it *tries* to write a file.

    # Need to ensure the 'backtester' directory exists in tmp_path for FileSystemLoader
    # if generate_html_report is called from a path where __file__ is .../tmp_path/backtester/html_report.py
    # However, during tests, __file__ for html_report.py will be its location in the source tree or site-packages.
    # The FileSystemLoader will look for 'report_template.html' in the same directory as html_report.py

    # To make this test robust, we can mock the Jinja environment and template rendering.
    # However, let's first try to make it work by ensuring the template is accessible.
    # The `generate_html_report` uses `os.path.dirname(__file__)` for loader.
    # We need to ensure `report_template.html` is discoverable by `html_report.py`.
    # If running tests from repo root, and `backtester/report_template.html` exists, it should be fine.

    report_file = tmp_path / "report.html"

    # Patching the plot_trades_on_candlestick_plotly specifically within html_report's context
    with patch('backtester.html_report.plot_trades_on_candlestick_plotly') as mock_plot_trades_candlestick:
        # Make the patched function return a mock Figure that has a to_html method
        mock_fig = MagicMock(spec=go.Figure)
        mock_fig.to_html.return_value = "<div>Mock Candlestick Chart HTML</div>"
        mock_plot_trades_candlestick.return_value = mock_fig

        ghr_direct(
            equity_curve=sample_equity_curve_df,
            data=sample_ohlc_data,
            trades=sample_trades_df,
            indicators=sample_indicators_df, # Passed to plot_trades_on_candlestick_plotly
            metrics=sample_metrics_dict,     # Contains indicator_cfg
            filepath=str(report_file)
        )

    assert report_file.exists()
    content = report_file.read_text()
    assert "Equity Curve" in content
    assert "Trades on Candlestick Chart" in content # Title from plot_trades_on_candlestick_plotly
    assert "Mock Candlestick Chart HTML" in content # From our patched to_html
    assert "<td>Total Return</td>" in content # Check if metrics table is rendered
    assert "<td>0.1</td>" in content       # Check if a metric value is rendered
    assert "Trade Log" in content # Check for trade log table title
    assert f"<td>{sample_trades_df['pnl'].iloc[0]}</td>" in content # Check for a PnL value in trade log

    # Check that plotly.offline.plot was called for the equity curve
    # It's called with include_plotlyjs=False, output_type='div'
    # The first call to mock_plotly_plot is for the equity curve.
    args, kwargs = mock_plotly_plot.call_args_list[0]
    assert isinstance(args[0], go.Figure) # First arg is the figure
    assert kwargs['output_type'] == 'div'
    assert not kwargs['include_plotlyjs']

    # Check that plot_trades_on_candlestick_plotly was called
    mock_plot_trades_candlestick.assert_called_once()
    call_args = mock_plot_trades_candlestick.call_args[0]
    call_kwargs = mock_plot_trades_candlestick.call_args[1]
    pd.testing.assert_frame_equal(call_args[0], sample_ohlc_data)
    pd.testing.assert_frame_equal(call_args[1], sample_trades_df.reset_index(drop=True).assign(trade_id=sample_trades_df.index)) # trades df gets trade_id added
    pd.testing.assert_frame_equal(call_kwargs['indicators'], sample_indicators_df)
    assert call_kwargs['indicator_cfg'] == sample_metrics_dict['indicator_cfg']
    assert call_kwargs['title'] == "Trades on Candlestick Chart"
    assert not call_kwargs['show']


# Make sure to have a `report_template.html` accessible to `backtester/html_report.py`
# This might mean `backtester/report_template.html` must exist relative to the project root when tests are run.
# A simple `report_template.html` for testing could be:
"""
<html>
<head><title>Test Report</title></head>
<body>
    <h1>Metrics</h1>{{ metrics_table | safe }}
    <h1>Equity Curve</h1>{{ eq_div | safe }}
    <h1>Trades Chart</h1>{{ trade_div | safe }}
    <h1>Trade Log</h1>
    <table>
        <thead>
            <tr>{% for col in trade_log_columns %}<th>{{ col }}</th>{% endfor %}</tr>
        </thead>
        <tbody>
            {% for trade in trade_log %}
            <tr>{% for col in trade_log_columns %}<td>{{ trade[col] }}</td>{% endfor %}</tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
"""
# This template should reside in `backtester/report_template.html` for the test to pass as is.
# The actual `generate_html_report` uses `FileSystemLoader(os.path.dirname(__file__))`, so it will
# correctly locate `report_template.html` if it's in the same directory as `html_report.py`.
# No need to create a dummy one in tmp_path IF the test runner can resolve this.
# The key is that `backtester.html_report.generate_html_report` is the item under test,
# and its internal `__file__` reference will point to its actual location.
# So, as long as `backtester/report_template.html` exists in the source tree (and is installed), it should work.

# Final check: The `reporting.py` re-exports. Ensure one of the re-exported functions works.
@patch('plotly.graph_objs.Figure.show')
def test_reexported_plot_function_callable(mock_show, sample_equity_curve_df):
    """Test that a re-exported plotting function is callable via reporting.py."""
    # plot_equity_curve is re-exported.
    plot_equity_curve(sample_equity_curve_df, interactive=True)
    mock_show.assert_called_once()

# It might be good to also test the fallback logic in generate_html_report if the
# plot_trades_on_candlestick_plotly call fails.
@patch('backtester.html_report.plot_trades_on_candlestick_plotly')
@patch('plotly.graph_objs.Figure') # Mock the Figure constructor used in fallback
@patch('plotly.offline.plot')
def test_generate_html_report_fallback_plotting(mock_offline_plot, mock_go_figure, mock_ptocp, tmp_path, sample_equity_curve_df, sample_ohlc_data, sample_trades_df, sample_metrics_dict):
    """Test HTML report generation uses fallback if advanced plotting fails."""
    mock_ptocp.side_effect = Exception("Plotting error") # Simulate failure

    # Mock the Figure object that would be created by the fallback
    mock_fallback_fig_instance = MagicMock()
    mock_fallback_fig_instance.to_html.return_value = "<div>Fallback Plotly Chart</div>"
    mock_go_figure.return_value = mock_fallback_fig_instance

    mock_offline_plot.return_value = "<div>Equity Curve Plot</div>" # For equity curve

    report_file = tmp_path / "report_fallback.html"
    ghr_direct(
        equity_curve=sample_equity_curve_df,
        data=sample_ohlc_data,
        trades=sample_trades_df,
            indicators=None,
            metrics={'Total Return': 0.1, 'Note': 'Simple metrics for fallback test'}, # Use simple metrics
        filepath=str(report_file)
    )

    assert report_file.exists()
    content = report_file.read_text()
    assert "Equity Curve Plot" in content
    assert "Fallback Plotly Chart" in content
    mock_ptocp.assert_called_once() # It was called and failed
    mock_go_figure.assert_called() # Fallback Figure constructor was called
    assert mock_fallback_fig_instance.to_html.call_count > 0 # to_html on fallback fig

    # Ensure the fallback added traces (Candlestick, trades)
    # This requires checking calls to mock_fallback_fig_instance.add_trace
    # At least one Candlestick trace
    assert any("Candlestick" in str(call_args) for call_args, _ in mock_fallback_fig_instance.add_trace.call_args_list)
    # Multiple Scatter traces for trades
    scatter_calls = sum(1 for call_args, _ in mock_fallback_fig_instance.add_trace.call_args_list if "Scatter" in str(call_args))
    # Each trade adds 3 traces in fallback: entry marker, exit marker, line between them
    assert scatter_calls >= len(sample_trades_df) * 3


# Note: For `generate_html_report` test to robustly find `report_template.html`,
# ensure that the `backtester` package structure is correctly understood by the test runner,
# or consider making the template path configurable for tests.
# If `backtester` is installed (e.g., `pip install .`), `__file__` will point to site-packages,
# and the template needs to be there (usually handled by `package_data` in `setup.py`).
# If running from source without install, `PYTHONPATH` needs to be set correctly.
# The current structure assumes `backtester/report_template.html` is found relative to `html_report.py`.
