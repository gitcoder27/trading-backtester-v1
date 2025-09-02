"""
Test analytics service functionality
"""

import pytest
import pandas as pd
import numpy as np
from backend.app.services.analytics_service import AnalyticsService
from backend.app.database.models import init_db, get_session_factory, Backtest
from datetime import datetime, timedelta
import json


@pytest.fixture(scope="module")
def analytics_service():
    """Create analytics service instance"""
    init_db()  # Initialize test database
    return AnalyticsService()


@pytest.fixture
def sample_backtest_data():
    """Create sample backtest data for testing"""
    # Create sample equity curve
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='H')
    equity_curve = []
    equity = 100000
    
    for i, date in enumerate(dates):
        # Add some random walk with slight upward trend
        change = np.random.normal(0.001, 0.02)  # 0.1% mean return, 2% volatility
        equity *= (1 + change)
        
        equity_curve.append({
            'timestamp': date.isoformat(),
            'equity': equity
        })
    
    # Create sample trades
    trades = []
    for i in range(20):
        entry_time = dates[i * 10] if i * 10 < len(dates) else dates[-1]
        exit_time = entry_time + timedelta(hours=2)
        pnl = np.random.normal(50, 200)  # Random P&L
        
        trades.append({
            'entry_time': entry_time.isoformat(),
            'exit_time': exit_time.isoformat(),
            'entry_price': 100 + np.random.normal(0, 5),
            'exit_price': 102 + np.random.normal(0, 5),
            'pnl': pnl,
            'direction': 'long' if pnl > 0 else 'short'
        })
    
    # Create sample metrics
    metrics = {
        'total_return_pct': 15.5,
        'sharpe_ratio': 1.2,
        'max_drawdown_pct': -5.2,
        'win_rate': 0.65,
        'profit_factor': 1.8,
        'total_trades': len(trades)
    }
    
    return {
        'equity_curve': equity_curve,
        'trades': trades,
        'metrics': metrics
    }


@pytest.fixture
def sample_backtest_in_db(sample_backtest_data):
    """Create a sample backtest in the database"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        backtest = Backtest(
            strategy_name="TestStrategy",
            strategy_params={'param1': 10},
            dataset_id=1,
            status="completed",
            results=sample_backtest_data,
            created_at=datetime.utcnow()
        )
        db.add(backtest)
        db.commit()
        db.refresh(backtest)
        
        yield backtest.id
        
        # Cleanup
        db.query(Backtest).filter(Backtest.id == backtest.id).delete()
        db.commit()
    finally:
        db.close()


def test_analytics_service_initialization(analytics_service):
    """Test analytics service can be initialized"""
    assert analytics_service is not None
    assert hasattr(analytics_service, 'SessionLocal')


def test_get_performance_summary_success(analytics_service, sample_backtest_in_db):
    """Test getting performance summary for valid backtest"""
    result = analytics_service.get_performance_summary(sample_backtest_in_db)
    
    assert result['success'] is True
    assert result['backtest_id'] == sample_backtest_in_db
    assert 'performance' in result
    
    performance = result['performance']
    assert 'basic_metrics' in performance
    assert 'advanced_analytics' in performance
    assert 'trade_analysis' in performance
    assert 'risk_metrics' in performance
    
    # Check basic metrics are present
    basic_metrics = performance['basic_metrics']
    assert 'total_return_pct' in basic_metrics
    assert 'sharpe_ratio' in basic_metrics
    assert 'win_rate' in basic_metrics


def test_get_performance_summary_not_found(analytics_service):
    """Test performance summary for non-existent backtest"""
    result = analytics_service.get_performance_summary(99999)
    
    assert result['success'] is False
    assert 'not found' in result['error'].lower()


def test_get_charts_success(analytics_service, sample_backtest_in_db):
    """Test getting charts for valid backtest"""
    result = analytics_service.get_charts(sample_backtest_in_db)
    
    assert result['success'] is True
    assert result['backtest_id'] == sample_backtest_in_db
    assert 'charts' in result
    
    charts = result['charts']
    expected_charts = ['equity', 'drawdown', 'returns', 'trades', 'monthly_returns']
    
    for chart_type in expected_charts:
        assert chart_type in charts
        # Verify it's valid JSON (Plotly format)
        assert isinstance(charts[chart_type], str)
        # Try to parse as JSON to ensure it's valid
        chart_data = json.loads(charts[chart_type])
        assert isinstance(chart_data, dict)


def test_get_charts_specific_types(analytics_service, sample_backtest_in_db):
    """Test getting specific chart types"""
    chart_types = ['equity', 'drawdown']
    result = analytics_service.get_charts(sample_backtest_in_db, chart_types)
    
    assert result['success'] is True
    charts = result['charts']
    
    # Should only have requested charts
    assert len(charts) == len(chart_types)
    for chart_type in chart_types:
        assert chart_type in charts


def test_compare_strategies(analytics_service, sample_backtest_in_db):
    """Test strategy comparison"""
    # Create another backtest for comparison
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        backtest2 = Backtest(
            strategy_name="TestStrategy2",
            strategy_params={'param1': 20},
            dataset_id=1,
            status="completed",
            results={
                'equity_curve': [
                    {'timestamp': '2024-01-01T00:00:00', 'equity': 100000},
                    {'timestamp': '2024-01-02T00:00:00', 'equity': 105000}
                ],
                'trades': [
                    {'entry_time': '2024-01-01T00:00:00', 'pnl': 1000, 'direction': 'long'}
                ],
                'metrics': {
                    'total_return_pct': 20.0,
                    'sharpe_ratio': 1.5,
                    'max_drawdown_pct': -3.0,
                    'win_rate': 0.7,
                    'profit_factor': 2.0,
                    'total_trades': 1
                }
            },
            created_at=datetime.utcnow()
        )
        db.add(backtest2)
        db.commit()
        db.refresh(backtest2)
        
        # Test comparison
        result = analytics_service.compare_strategies([sample_backtest_in_db, backtest2.id])
        
        assert result['success'] is True
        assert 'comparison_data' in result
        assert 'comparison_chart' in result
        
        comparison_data = result['comparison_data']
        assert len(comparison_data) == 2
        
        # Verify structure of comparison data
        for data in comparison_data:
            required_fields = ['backtest_id', 'strategy_name', 'total_return', 'sharpe_ratio']
            for field in required_fields:
                assert field in data
        
        # Cleanup
        db.query(Backtest).filter(Backtest.id == backtest2.id).delete()
        db.commit()
    finally:
        db.close()


def test_advanced_analytics_calculations(analytics_service):
    """Test advanced analytics calculation methods"""
    # Create sample equity curve DataFrame
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    equity_values = 100000 * (1 + np.cumsum(np.random.normal(0.001, 0.02, 100)))
    
    equity_curve = pd.DataFrame({
        'timestamp': dates,
        'equity': equity_values
    })
    
    # Test returns calculation
    returns = analytics_service._compute_returns(equity_curve)
    assert len(returns) == len(equity_curve) - 1
    assert isinstance(returns, pd.Series)
    
    # Test drawdown calculation
    drawdown_data = analytics_service._compute_drawdown(equity_curve)
    assert len(drawdown_data) == len(equity_curve)
    assert 'drawdown' in drawdown_data.columns
    assert all(drawdown_data['drawdown'] <= 0)  # Drawdowns should be negative or zero
    
    # Test rolling Sharpe calculation
    rolling_sharpe = analytics_service._compute_rolling_sharpe(equity_curve, window=20)
    assert len(rolling_sharpe) == len(equity_curve) - 1  # One less due to returns calculation
    assert 'rolling_sharpe' in rolling_sharpe.columns


def test_risk_metrics_calculations(analytics_service):
    """Test risk metrics calculations"""
    # Create sample equity curve with known characteristics
    dates = pd.date_range(start='2024-01-01', periods=100, freq='H')
    # Create returns with some negative outliers for VaR testing
    returns = np.random.normal(0.001, 0.02, 100)
    returns[10] = -0.05  # Add a large loss
    returns[50] = -0.03  # Add another loss
    
    equity_values = 100000 * np.cumprod(1 + returns)
    equity_curve = pd.DataFrame({
        'timestamp': dates,
        'equity': equity_values
    })
    
    risk_metrics = analytics_service._compute_risk_metrics(equity_curve)
    
    assert 'var_95' in risk_metrics
    assert 'var_99' in risk_metrics
    assert 'cvar_95' in risk_metrics
    assert 'cvar_99' in risk_metrics
    
    # VaR 99% should be more extreme than VaR 95%
    assert risk_metrics['var_99'] <= risk_metrics['var_95']
    
    # CVaR should be more extreme than VaR
    assert risk_metrics['cvar_95'] <= risk_metrics['var_95']
    assert risk_metrics['cvar_99'] <= risk_metrics['var_99']


def test_trade_analysis(analytics_service):
    """Test trade analysis functionality"""
    # Create sample trades DataFrame
    trades_data = []
    for i in range(50):
        pnl = np.random.normal(100, 200)  # Some wins, some losses
        direction = 'long' if np.random.random() > 0.5 else 'short'
        entry_time = datetime(2024, 1, 1) + timedelta(hours=i)
        
        trades_data.append({
            'entry_time': entry_time,
            'pnl': pnl,
            'direction': direction
        })
    
    trades = pd.DataFrame(trades_data)
    analysis = analytics_service._analyze_trades(trades)
    
    assert 'total_trades' in analysis
    assert 'winning_trades' in analysis
    assert 'losing_trades' in analysis
    assert 'avg_win' in analysis
    assert 'avg_loss' in analysis
    
    # Check that totals add up
    assert analysis['total_trades'] == analysis['winning_trades'] + analysis['losing_trades']
    
    # Check time analysis
    assert 'trades_by_hour' in analysis
    assert 'trades_by_weekday' in analysis


def test_empty_data_handling(analytics_service):
    """Test handling of empty datasets"""
    empty_equity = pd.DataFrame({'timestamp': [], 'equity': []})
    empty_trades = pd.DataFrame()
    
    # Should not crash with empty data
    returns = analytics_service._compute_returns(empty_equity)
    assert len(returns) == 0
    
    risk_metrics = analytics_service._compute_risk_metrics(empty_equity)
    assert risk_metrics == {}
    
    trade_analysis = analytics_service._analyze_trades(empty_trades)
    assert trade_analysis == {}


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
