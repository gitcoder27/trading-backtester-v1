"""
Comprehensive Database Models Test - Targeting 100% Coverage
Tests all database models and functions in backend/app/database/models.py
"""

import pytest
import tempfile
import os
import json
from datetime import datetime, timedelta
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys

# Add project root to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from backend.app.database.models import (
    Base, BacktestJob, Trade, BacktestMetrics, Dataset, Strategy, Backtest,
    get_engine, get_session_factory, create_tables, get_db, init_db
)


@pytest.fixture
def test_engine():
    """Create an in-memory SQLite engine for testing"""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    return engine


@pytest.fixture
def test_session_factory(test_engine):
    """Create a session factory for testing"""
    return sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture
def test_db_session(test_session_factory):
    """Create a database session for testing"""
    session = test_session_factory()
    try:
        yield session
    finally:
        session.close()


class TestBacktestJobModel:
    """Test BacktestJob model - targeting 100% coverage"""
    
    def test_backtest_job_creation(self, test_db_session):
        """Test creating a BacktestJob record"""
        job = BacktestJob(
            strategy="test_strategy",
            strategy_params={"param1": 10, "param2": "value"},
            engine_options={"option1": True},
            dataset_path="/path/to/dataset.csv"
        )
        
        test_db_session.add(job)
        test_db_session.commit()
        test_db_session.refresh(job)
        
        assert job.id is not None
        assert job.status == "pending"  # Default value
        assert job.strategy == "test_strategy"
        assert job.strategy_params["param1"] == 10
        assert job.progress == 0.0  # Default value
        assert job.created_at is not None
        assert isinstance(job.created_at, datetime)
    
    def test_backtest_job_status_updates(self, test_db_session):
        """Test updating BacktestJob status and progress"""
        job = BacktestJob(strategy="test_strategy", dataset_path="test.csv")
        test_db_session.add(job)
        test_db_session.commit()
        
        # Update status to running
        job.status = "running"
        job.started_at = datetime.utcnow()
        job.progress = 0.5
        job.current_step = "Processing data"
        job.total_steps = 100
        test_db_session.commit()
        
        assert job.status == "running"
        assert job.progress == 0.5
        assert job.current_step == "Processing data"
        assert job.total_steps == 100
        assert job.started_at is not None
    
    def test_backtest_job_completion(self, test_db_session):
        """Test completing a BacktestJob with results"""
        job = BacktestJob(strategy="test_strategy", dataset_path="test.csv")
        test_db_session.add(job)
        test_db_session.commit()
        
        # Complete the job
        results = {"metrics": {"total_return": 15.5}, "trades": []}
        job.status = "completed"
        job.completed_at = datetime.utcnow()
        job.progress = 1.0
        job.result_data = json.dumps(results)
        job.actual_duration = 120.5
        test_db_session.commit()
        
        assert job.status == "completed"
        assert job.progress == 1.0
        assert job.completed_at is not None
        assert json.loads(job.result_data)["metrics"]["total_return"] == 15.5
        assert job.actual_duration == 120.5
    
    def test_backtest_job_failure(self, test_db_session):
        """Test BacktestJob failure scenario"""
        job = BacktestJob(strategy="test_strategy", dataset_path="test.csv")
        test_db_session.add(job)
        test_db_session.commit()
        
        # Fail the job
        job.status = "failed"
        job.error_message = "Strategy not found"
        job.completed_at = datetime.utcnow()
        test_db_session.commit()
        
        assert job.status == "failed"
        assert job.error_message == "Strategy not found"
        assert job.completed_at is not None


class TestTradeModel:
    """Test Trade model - targeting 100% coverage"""
    
    def test_trade_creation(self, test_db_session):
        """Test creating a Trade record"""
        trade = Trade(
            backtest_job_id=1,
            entry_time=datetime(2024, 1, 1, 9, 15),
            entry_price=100.50,
            quantity=100,
            side="long",
            entry_signal="EMA_CROSSOVER"
        )
        
        test_db_session.add(trade)
        test_db_session.commit()
        test_db_session.refresh(trade)
        
        assert trade.id is not None
        assert trade.backtest_job_id == 1
        assert trade.entry_time == datetime(2024, 1, 1, 9, 15)
        assert trade.entry_price == 100.50
        assert trade.quantity == 100
        assert trade.side == "long"
        assert trade.entry_signal == "EMA_CROSSOVER"
        assert trade.created_at is not None
    
    def test_trade_completion(self, test_db_session):
        """Test completing a trade with exit details"""
        trade = Trade(
            backtest_job_id=1,
            entry_time=datetime(2024, 1, 1, 9, 15),
            entry_price=100.50,
            quantity=100,
            side="long"
        )
        test_db_session.add(trade)
        test_db_session.commit()
        
        # Complete the trade
        trade.exit_time = datetime(2024, 1, 1, 10, 30)
        trade.exit_price = 102.00
        trade.pnl = 150.0
        trade.pnl_percent = 1.49
        trade.holding_time_minutes = 75
        trade.exit_signal = "TAKE_PROFIT"
        trade.max_profit = 200.0
        trade.max_loss = -50.0
        test_db_session.commit()
        
        assert trade.exit_time == datetime(2024, 1, 1, 10, 30)
        assert trade.exit_price == 102.00
        assert trade.pnl == 150.0
        assert trade.pnl_percent == 1.49
        assert trade.holding_time_minutes == 75
        assert trade.exit_signal == "TAKE_PROFIT"
        assert trade.max_profit == 200.0
        assert trade.max_loss == -50.0
    
    def test_short_trade(self, test_db_session):
        """Test creating a short trade"""
        trade = Trade(
            backtest_job_id=1,
            entry_time=datetime(2024, 1, 1, 9, 15),
            entry_price=100.50,
            exit_price=98.50,
            quantity=100,
            side="short",
            pnl=200.0,
            pnl_percent=1.99
        )
        
        test_db_session.add(trade)
        test_db_session.commit()
        
        assert trade.side == "short"
        assert trade.pnl == 200.0  # Profit from short position


class TestBacktestMetricsModel:
    """Test BacktestMetrics model - targeting 100% coverage"""
    
    def test_backtest_metrics_creation(self, test_db_session):
        """Test creating comprehensive BacktestMetrics"""
        metrics = BacktestMetrics(
            backtest_job_id=1,
            total_return=5000.0,
            total_return_percent=5.0,
            sharpe_ratio=1.25,
            sortino_ratio=1.8,
            max_drawdown=-1500.0,
            max_drawdown_percent=-1.5,
            total_trades=50,
            winning_trades=32,
            losing_trades=18,
            win_rate=0.64,
            profit_factor=1.8,
            largest_win=800.0,
            largest_loss=-300.0,
            average_win=250.0,
            average_loss=-125.0,
            average_holding_time=45.5,
            max_consecutive_wins=8,
            max_consecutive_losses=3,
            volatility=0.15,
            var_95=-250.0,
            cvar_95=-400.0,
            total_trading_days=25,
            profitable_days=18,
            daily_target_hit_rate=0.72
        )
        
        test_db_session.add(metrics)
        test_db_session.commit()
        test_db_session.refresh(metrics)
        
        # Test all basic metrics
        assert metrics.id is not None
        assert metrics.backtest_job_id == 1
        assert metrics.total_return == 5000.0
        assert metrics.total_return_percent == 5.0
        assert metrics.sharpe_ratio == 1.25
        assert metrics.sortino_ratio == 1.8
        assert metrics.max_drawdown == -1500.0
        assert metrics.max_drawdown_percent == -1.5
        
        # Test trade statistics
        assert metrics.total_trades == 50
        assert metrics.winning_trades == 32
        assert metrics.losing_trades == 18
        assert metrics.win_rate == 0.64
        assert metrics.profit_factor == 1.8
        
        # Test trade amounts
        assert metrics.largest_win == 800.0
        assert metrics.largest_loss == -300.0
        assert metrics.average_win == 250.0
        assert metrics.average_loss == -125.0
        
        # Test time-based metrics
        assert metrics.average_holding_time == 45.5
        assert metrics.max_consecutive_wins == 8
        assert metrics.max_consecutive_losses == 3
        
        # Test risk metrics
        assert metrics.volatility == 0.15
        assert metrics.var_95 == -250.0
        assert metrics.cvar_95 == -400.0
        
        # Test period metrics
        assert metrics.total_trading_days == 25
        assert metrics.profitable_days == 18
        assert metrics.daily_target_hit_rate == 0.72
        
        assert metrics.created_at is not None


class TestDatasetModel:
    """Test Dataset model - targeting 100% coverage"""
    
    def test_dataset_creation(self, test_db_session):
        """Test creating a Dataset record with all fields"""
        dataset = Dataset(
            name="NIFTY 1min Data",
            filename="nifty_1min.csv",
            file_path="/data/nifty_1min.csv",
            file_size=1024000,
            rows_count=50000,
            columns=["open", "high", "low", "close", "volume"],
            timeframe="1min",
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 12, 31),
            missing_data_pct=0.1,
            data_quality_score=0.95,
            has_gaps=False,
            timezone="Asia/Kolkata",
            symbol="NIFTY",
            exchange="NSE",
            data_source="Yahoo Finance",
            quality_checks={"gaps": False, "duplicates": 0},
            backtest_count=5,
            last_used=datetime.utcnow()
        )
        
        test_db_session.add(dataset)
        test_db_session.commit()
        test_db_session.refresh(dataset)
        
        assert dataset.id is not None
        assert dataset.name == "NIFTY 1min Data"
        assert dataset.filename == "nifty_1min.csv"
        assert dataset.file_path == "/data/nifty_1min.csv"
        assert dataset.file_size == 1024000
        assert dataset.rows_count == 50000
        assert dataset.columns == ["open", "high", "low", "close", "volume"]
        assert dataset.timeframe == "1min"
        assert dataset.start_date == datetime(2024, 1, 1)
        assert dataset.end_date == datetime(2024, 12, 31)
        assert dataset.missing_data_pct == 0.1
        assert dataset.data_quality_score == 0.95
        assert dataset.has_gaps is False
        assert dataset.timezone == "Asia/Kolkata"
        assert dataset.symbol == "NIFTY"
        assert dataset.exchange == "NSE"
        assert dataset.data_source == "Yahoo Finance"
        assert dataset.quality_checks["gaps"] is False
        assert dataset.backtest_count == 5
        assert dataset.last_used is not None
        assert dataset.created_at is not None
    
    def test_dataset_usage_tracking(self, test_db_session):
        """Test dataset usage tracking"""
        dataset = Dataset(
            name="Test Dataset",
            filename="test.csv",
            file_path="/test.csv"
        )
        test_db_session.add(dataset)
        test_db_session.commit()
        
        # Update usage
        dataset.backtest_count = 10
        dataset.last_used = datetime.utcnow()
        dataset.last_accessed = datetime.utcnow()
        test_db_session.commit()
        
        assert dataset.backtest_count == 10
        assert dataset.last_used is not None
        assert dataset.last_accessed is not None


class TestStrategyModel:
    """Test Strategy model - targeting 100% coverage"""
    
    def test_strategy_creation(self, test_db_session):
        """Test creating a Strategy record"""
        strategy = Strategy(
            name="EMA Crossover",
            module_path="strategies.ema_crossover",
            class_name="EMACrossoverStrategy",
            description="Simple EMA crossover strategy",
            parameters_schema={
                "fast_ema": {"type": "integer", "default": 12},
                "slow_ema": {"type": "integer", "default": 26}
            },
            default_parameters={"fast_ema": 12, "slow_ema": 26},
            total_backtests=25,
            avg_performance=1.15,
            last_used=datetime.utcnow(),
            is_active=True
        )
        
        test_db_session.add(strategy)
        test_db_session.commit()
        test_db_session.refresh(strategy)
        
        assert strategy.id is not None
        assert strategy.name == "EMA Crossover"
        assert strategy.module_path == "strategies.ema_crossover"
        assert strategy.class_name == "EMACrossoverStrategy"
        assert strategy.description == "Simple EMA crossover strategy"
        assert strategy.parameters_schema["fast_ema"]["default"] == 12
        assert strategy.default_parameters["slow_ema"] == 26
        assert strategy.total_backtests == 25
        assert strategy.avg_performance == 1.15
        assert strategy.last_used is not None
        assert strategy.is_active is True
        assert strategy.created_at is not None
    
    def test_strategy_deactivation(self, test_db_session):
        """Test deactivating a strategy"""
        strategy = Strategy(
            name="Test Strategy",
            module_path="test.strategy",
            class_name="TestStrategy"
        )
        test_db_session.add(strategy)
        test_db_session.commit()
        
        # Deactivate strategy
        strategy.is_active = False
        test_db_session.commit()
        
        assert strategy.is_active is False


class TestBacktestModel:
    """Test Backtest model - targeting 100% coverage"""
    
    def test_backtest_creation(self, test_db_session):
        """Test creating a Backtest record"""
        results_data = {
            "equity_curve": [
                {"timestamp": "2024-01-01T09:15:00", "equity": 100000},
                {"timestamp": "2024-01-01T09:16:00", "equity": 101000}
            ],
            "trades": [
                {"entry_time": "2024-01-01T09:15:00", "pnl": 500}
            ],
            "metrics": {"total_return": 5.5, "sharpe_ratio": 1.2}
        }
        
        backtest = Backtest(
            strategy_name="EMA Crossover",
            strategy_params={"fast_ema": 12, "slow_ema": 26},
            dataset_id=1,
            status="completed",
            results=results_data,
            completed_at=datetime.utcnow()
        )
        
        test_db_session.add(backtest)
        test_db_session.commit()
        test_db_session.refresh(backtest)
        
        assert backtest.id is not None
        assert backtest.strategy_name == "EMA Crossover"
        assert backtest.strategy_params["fast_ema"] == 12
        assert backtest.dataset_id == 1
        assert backtest.status == "completed"
        assert backtest.results["metrics"]["total_return"] == 5.5
        assert backtest.completed_at is not None
        assert backtest.created_at is not None
    
    def test_backtest_failure(self, test_db_session):
        """Test failed backtest"""
        backtest = Backtest(
            strategy_name="Test Strategy",
            strategy_params={},
            dataset_id=1,
            status="failed"
        )
        
        test_db_session.add(backtest)
        test_db_session.commit()
        
        assert backtest.status == "failed"


class TestDatabaseFunctions:
    """Test database utility functions - targeting 100% coverage"""
    
    def test_get_engine(self):
        """Test get_engine function"""
        engine = get_engine()
        assert engine is not None
        assert "sqlite" in str(engine.url)
    
    def test_get_session_factory(self):
        """Test get_session_factory function"""
        SessionLocal = get_session_factory()
        assert SessionLocal is not None
        
        # Test creating a session
        session = SessionLocal()
        assert session is not None
        session.close()
    
    def test_create_tables(self):
        """Test create_tables function"""
        # This should not raise an exception
        create_tables()
        assert True
    
    def test_get_db_generator(self):
        """Test get_db dependency generator"""
        db_gen = get_db()
        db = next(db_gen)
        assert db is not None
        
        # Close the generator
        try:
            next(db_gen)
        except StopIteration:
            pass  # Expected
    
    def test_init_db(self, capsys):
        """Test init_db function"""
        init_db()
        captured = capsys.readouterr()
        assert "Database initialized" in captured.out


class TestModelRelationships:
    """Test relationships and constraints between models"""
    
    def test_backtest_job_and_metrics_relationship(self, test_db_session):
        """Test one-to-one relationship between BacktestJob and BacktestMetrics"""
        # Create backtest job
        job = BacktestJob(strategy="test", dataset_path="test.csv")
        test_db_session.add(job)
        test_db_session.commit()
        
        # Create metrics for this job
        metrics = BacktestMetrics(
            backtest_job_id=job.id,
            total_return=1000.0,
            win_rate=0.6
        )
        test_db_session.add(metrics)
        test_db_session.commit()
        
        assert metrics.backtest_job_id == job.id
    
    def test_dataset_and_backtest_relationship(self, test_db_session):
        """Test relationship between Dataset and Backtest"""
        # Create dataset
        dataset = Dataset(
            name="Test Dataset",
            filename="test.csv",
            file_path="/test.csv"
        )
        test_db_session.add(dataset)
        test_db_session.commit()
        
        # Create backtest using this dataset
        backtest = Backtest(
            strategy_name="Test Strategy",
            dataset_id=dataset.id,
            results={"metrics": {}}
        )
        test_db_session.add(backtest)
        test_db_session.commit()
        
        assert backtest.dataset_id == dataset.id
    
    def test_trade_and_backtest_job_relationship(self, test_db_session):
        """Test relationship between Trade and BacktestJob"""
        # Create backtest job
        job = BacktestJob(strategy="test", dataset_path="test.csv")
        test_db_session.add(job)
        test_db_session.commit()
        
        # Create trades for this job
        trade1 = Trade(
            backtest_job_id=job.id,
            entry_time=datetime.utcnow(),
            entry_price=100.0,
            quantity=100,
            side="long"
        )
        trade2 = Trade(
            backtest_job_id=job.id,
            entry_time=datetime.utcnow(),
            entry_price=105.0,
            quantity=50,
            side="short"
        )
        
        test_db_session.add_all([trade1, trade2])
        test_db_session.commit()
        
        assert trade1.backtest_job_id == job.id
        assert trade2.backtest_job_id == job.id


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--cov=backend.app.database.models", "--cov-report=term-missing"])
