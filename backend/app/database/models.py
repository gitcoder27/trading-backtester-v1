"""
Database models for the trading backtester backend
Using SQLAlchemy with SQLite for local persistence
"""

from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
import json
import os

from backend.app.config import get_settings

Base = declarative_base()


class BacktestJob(Base):
    """Model for backtest job metadata and status"""
    __tablename__ = "backtest_jobs"
    
    id = Column(Integer, primary_key=True, index=True)
    status = Column(String(50), default="pending")  # pending, running, completed, failed, cancelled
    strategy = Column(String(200), nullable=False)
    strategy_params = Column(JSON)
    engine_options = Column(JSON)
    dataset_path = Column(String(500))
    
    # Progress tracking
    progress = Column(Float, default=0.0)  # 0.0 to 1.0
    current_step = Column(String(200))
    total_steps = Column(Integer)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Results (stored as JSON)
    result_data = Column(Text)  # JSON string of results
    error_message = Column(Text)
    
    # Metadata
    estimated_duration = Column(Float)  # seconds
    actual_duration = Column(Float)     # seconds


class Trade(Base):
    """Model for individual trades from backtests"""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_job_id = Column(Integer, index=True)  # Reference to BacktestJob
    
    # Trade details
    entry_time = Column(DateTime, nullable=False)
    exit_time = Column(DateTime)
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    side = Column(String(10), nullable=False)  # 'long' or 'short'
    
    # P&L and metrics
    pnl = Column(Float)
    pnl_percent = Column(Float)
    holding_time_minutes = Column(Float)
    
    # Trade metadata
    entry_signal = Column(String(100))
    exit_signal = Column(String(100))
    max_profit = Column(Float)
    max_loss = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


class BacktestMetrics(Base):
    """Model for detailed backtest performance metrics"""
    __tablename__ = "backtest_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    backtest_job_id = Column(Integer, index=True, unique=True)  # One-to-one with BacktestJob
    
    # Basic performance metrics
    total_return = Column(Float)
    total_return_percent = Column(Float)
    sharpe_ratio = Column(Float)
    sortino_ratio = Column(Float)
    max_drawdown = Column(Float)
    max_drawdown_percent = Column(Float)
    
    # Trade statistics
    total_trades = Column(Integer)
    winning_trades = Column(Integer)
    losing_trades = Column(Integer)
    win_rate = Column(Float)
    profit_factor = Column(Float)
    
    # Trade amounts
    largest_win = Column(Float)
    largest_loss = Column(Float)
    average_win = Column(Float)
    average_loss = Column(Float)
    
    # Time-based metrics
    average_holding_time = Column(Float)  # minutes
    max_consecutive_wins = Column(Integer)
    max_consecutive_losses = Column(Integer)
    
    # Risk metrics
    volatility = Column(Float)
    var_95 = Column(Float)  # Value at Risk 95%
    cvar_95 = Column(Float)  # Conditional Value at Risk 95%
    
    # Period metrics
    total_trading_days = Column(Integer)
    profitable_days = Column(Integer)
    daily_target_hit_rate = Column(Float)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# Enhance existing Dataset model with more details
class Dataset(Base):
    """Model for uploaded datasets with enhanced metadata"""
    __tablename__ = "datasets"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    filename = Column(String(200), nullable=True)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer)
    
    # Data characteristics
    rows_count = Column(Integer)
    # Backward-compat alias for code/tests that reference `rows`.
    # Do not map a separate DB column to avoid schema mismatch errors.
    @property
    def rows(self):  # type: ignore[override]
        return self.rows_count

    @rows.setter
    def rows(self, value):  # type: ignore[override]
        self.rows_count = value
    columns = Column(JSON)  # List of column names
    timeframe = Column(String(20))  # 1min, 5min, etc.
    start_date = Column(DateTime)
    end_date = Column(DateTime)
    
    # Quality metrics
    missing_data_pct = Column(Float)
    data_quality_score = Column(Float)
    has_gaps = Column(Boolean, default=False)
    timezone = Column(String(50))
    
    # Market metadata
    symbol = Column(String(20))
    exchange = Column(String(50))
    data_source = Column(String(100))
    
    # Quality checks
    quality_checks = Column(JSON)  # Results of data quality validation
    
    # Usage tracking
    backtest_count = Column(Integer, default=0)
    last_used = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    last_accessed = Column(DateTime)


class Strategy(Base):
    """Model for strategy metadata"""
    __tablename__ = "strategies"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    module_path = Column(String(500), nullable=False)
    class_name = Column(String(200), nullable=False)
    
    # Metadata
    description = Column(Text)
    parameters_schema = Column(JSON)  # JSON schema for parameters
    default_parameters = Column(JSON)
    
    # Performance tracking
    total_backtests = Column(Integer, default=0)
    avg_performance = Column(Float)
    last_used = Column(DateTime)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)


class Backtest(Base):
    """Model for storing backtest results for analytics"""
    __tablename__ = "backtests"
    
    id = Column(Integer, primary_key=True, index=True)
    strategy_name = Column(String(200), nullable=False)
    strategy_params = Column(JSON)
    dataset_id = Column(Integer, index=True)
    
    # Status
    status = Column(String(50), default="completed")  # completed, failed
    
    # Results (comprehensive analytics data)
    results = Column(JSON)  # Contains equity_curve, trades, metrics
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)


# Database configuration
settings = get_settings()
DATABASE_URL = settings.database_url

def get_engine():
    """Get SQLAlchemy engine"""
    connect_args = {}
    if DATABASE_URL.startswith("sqlite"):
        db_path = DATABASE_URL.replace("sqlite:///", "", 1)
        if db_path:
            db_dir = os.path.dirname(os.path.abspath(db_path))
            os.makedirs(db_dir, exist_ok=True)
        connect_args = {"check_same_thread": False}

    engine = create_engine(
        DATABASE_URL,
        connect_args=connect_args
    )
    return engine

def get_session_factory():
    """Get SQLAlchemy session factory"""
    engine = get_engine()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    return SessionLocal

def create_tables():
    """Create all database tables"""
    engine = get_engine()
    Base.metadata.create_all(bind=engine)

def get_db():
    """Dependency to get database session"""
    SessionLocal = get_session_factory()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Initialize database on import
def init_db():
    """Initialize database with tables"""
    create_tables()
    print(f"Database initialized at: {DATABASE_URL}")

if __name__ == "__main__":
    init_db()
