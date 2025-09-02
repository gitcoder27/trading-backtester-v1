"""
Pydantic schemas for backtest API
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List
from datetime import datetime


class EngineOptions(BaseModel):
    """Configuration options for the backtest engine"""
    initial_cash: float = Field(default=100000, description="Initial cash amount")
    lots: int = Field(default=2, description="Number of lots to trade")
    option_delta: float = Field(default=0.5, description="Option delta")
    option_price_per_unit: float = Field(default=1.0, description="Option price per unit")
    fee_per_trade: float = Field(default=0.0, description="Fee per trade")
    slippage: float = Field(default=0.0, description="Slippage amount")
    intraday: bool = Field(default=True, description="Enable intraday trading")
    daily_profit_target: float = Field(default=30.0, description="Daily profit target")


class BacktestRequest(BaseModel):
    """Request schema for running a backtest"""
    strategy: str = Field(description="Strategy module path (e.g., 'strategies.ema10_scalper.EMA10ScalperStrategy')")
    strategy_params: Dict[str, Any] = Field(default_factory=dict, description="Parameters for strategy constructor")
    dataset: Optional[str] = Field(default=None, description="Dataset ID to use for backtest")
    dataset_path: Optional[str] = Field(default=None, description="Path to CSV dataset file (alternative to dataset)")
    engine_options: Optional[EngineOptions] = Field(default=None, description="Engine configuration options")


class EquityPoint(BaseModel):
    """Single point in equity curve"""
    timestamp: str = Field(description="ISO timestamp")
    equity: float = Field(description="Equity value")


class TradeRecord(BaseModel):
    """Single trade record"""
    entry_time: Optional[str] = Field(description="Trade entry timestamp")
    exit_time: Optional[str] = Field(description="Trade exit timestamp")
    entry_price: Optional[float] = Field(description="Entry price")
    exit_price: Optional[float] = Field(description="Exit price")
    position: Optional[str] = Field(description="Position type (long/short)")
    pnl: Optional[float] = Field(description="Profit/Loss")
    duration: Optional[float] = Field(description="Trade duration")


class PerformanceMetrics(BaseModel):
    """Performance metrics for a backtest"""
    total_return: float = Field(description="Total return percentage")
    sharpe_ratio: float = Field(description="Sharpe ratio")
    max_drawdown: float = Field(description="Maximum drawdown percentage")
    win_rate: float = Field(description="Win rate percentage")
    profit_factor: float = Field(description="Profit factor")
    total_trades: int = Field(description="Total number of trades")


class IndicatorPoint(BaseModel):
    """Single indicator value"""
    timestamp: str = Field(description="ISO timestamp")
    value: Optional[float] = Field(description="Indicator value")


class BacktestResult(BaseModel):
    """Complete backtest result"""
    equity_curve: List[EquityPoint] = Field(description="Equity curve data")
    trade_log: List[TradeRecord] = Field(description="List of all trades")
    metrics: PerformanceMetrics = Field(description="Performance metrics")
    indicators: Dict[str, List[IndicatorPoint]] = Field(default_factory=dict, description="Indicator data")
    engine_config: Dict[str, Any] = Field(description="Engine configuration used")


class BacktestResponse(BaseModel):
    """Response schema for backtest API"""
    success: bool = Field(description="Whether the backtest was successful")
    result: Optional[BacktestResult] = Field(default=None, description="Backtest results")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    job_id: Optional[str] = Field(default=None, description="Job ID for asynchronous processing")


class ErrorResponse(BaseModel):
    """Error response schema"""
    success: bool = False
    error: str = Field(description="Error message")
    details: Optional[Dict[str, Any]] = Field(default=None, description="Additional error details")
