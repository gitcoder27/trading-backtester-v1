"""
Analytics API endpoints
Provides comprehensive analytics and visualization for backtest results
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
analytics_service = AnalyticsService()


class CompareStrategiesRequest(BaseModel):
    backtest_ids: List[int]


@router.get("/performance/{backtest_id}")
async def get_performance_summary(backtest_id: int) -> Dict[str, Any]:
    """
    Get comprehensive performance analytics for a backtest
    
    Returns:
    - Basic metrics (return, Sharpe, drawdown, etc.)
    - Advanced analytics (volatility, skewness, Sortino ratio, etc.)
    - Trade analysis (win rate, avg win/loss, consecutive trades, etc.)
    - Risk metrics (VaR, CVaR, max consecutive losses, etc.)
    - Time analysis (performance by hour, weekday, month)
    """
    result = analytics_service.get_performance_summary(backtest_id)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/charts/{backtest_id}")
async def get_charts(
    backtest_id: int,
    chart_types: Optional[List[str]] = Query(None, description="Chart types to generate: equity, drawdown, returns, trades, monthly_returns")
) -> Dict[str, Any]:
    """
    Generate charts for a backtest
    
    Available chart types:
    - equity: Equity curve over time
    - drawdown: Drawdown chart with underwater curve
    - returns: Returns distribution histogram
    - trades: Trade markers overlaid on equity curve
    - monthly_returns: Monthly returns heatmap
    
    Returns Plotly JSON that can be rendered directly in frontend
    """
    result = analytics_service.get_charts(backtest_id, chart_types)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.post("/compare")
async def compare_strategies(request: CompareStrategiesRequest) -> Dict[str, Any]:
    """
    Compare performance across multiple backtests
    
    Returns:
    - Comparison table with key metrics
    - Normalized equity curves chart
    - Performance ranking
    """
    if len(request.backtest_ids) < 2:
        raise HTTPException(status_code=400, detail="At least 2 backtests required for comparison")
    
    if len(request.backtest_ids) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 backtests allowed for comparison")
    
    result = analytics_service.compare_strategies(request.backtest_ids)
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/charts/{backtest_id}/equity")
async def get_equity_chart(backtest_id: int) -> Dict[str, Any]:
    """Get equity curve chart for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['equity'])
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('equity')
    }


@router.get("/charts/{backtest_id}/drawdown")
async def get_drawdown_chart(backtest_id: int) -> Dict[str, Any]:
    """Get drawdown chart for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['drawdown'])
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('drawdown')
    }


@router.get("/charts/{backtest_id}/returns")
async def get_returns_chart(backtest_id: int) -> Dict[str, Any]:
    """Get returns distribution chart for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['returns'])
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('returns')
    }


@router.get("/charts/{backtest_id}/trades")
async def get_trades_chart(backtest_id: int) -> Dict[str, Any]:
    """Get trades chart overlaid on equity curve"""
    result = analytics_service.get_charts(backtest_id, ['trades'])
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('trades')
    }


@router.get("/charts/{backtest_id}/monthly_returns")
async def get_monthly_returns_chart(backtest_id: int) -> Dict[str, Any]:
    """Get monthly returns heatmap for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['monthly_returns'])
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('monthly_returns')
    }


@router.get("/{backtest_id}/trades")
async def get_trades_data(
    backtest_id: int,
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    page_size: int = Query(100, ge=1, le=1000, description="Number of trades per page"),
    sort_by: Optional[str] = Query("entry_time", description="Sort field: entry_time, pnl, duration"),
    sort_order: Optional[str] = Query("desc", description="Sort order: asc, desc"),
    filter_profitable: Optional[bool] = Query(None, description="Filter by profitable trades: true, false, or null for all")
) -> Dict[str, Any]:
    """
    Get paginated trade data for a backtest with filtering and sorting
    """
    result = analytics_service.get_trades_data(
        backtest_id=backtest_id,
        page=page,
        page_size=page_size,
        sort_by=sort_by,
        sort_order=sort_order,
        filter_profitable=filter_profitable
    )
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/summary/metrics")
async def get_metrics_summary() -> Dict[str, Any]:
    """
    Get summary of all analytics metrics and their descriptions
    
    Useful for frontend to understand available metrics
    """
    return {
        'success': True,
        'metrics': {
            'basic_metrics': {
                'total_return_pct': 'Total return percentage',
                'sharpe_ratio': 'Risk-adjusted return metric',
                'max_drawdown_pct': 'Maximum peak-to-trough decline',
                'win_rate': 'Percentage of winning trades',
                'profit_factor': 'Ratio of gross profits to gross losses',
                'total_trades': 'Total number of trades executed'
            },
            'advanced_analytics': {
                'volatility_annualized': 'Annualized volatility of returns',
                'skewness': 'Asymmetry of return distribution',
                'kurtosis': 'Tail risk of return distribution',
                'downside_deviation': 'Volatility of negative returns only',
                'sortino_ratio': 'Return/downside deviation ratio',
                'calmar_ratio': 'Return/max drawdown ratio'
            },
            'risk_metrics': {
                'var_95': 'Value at Risk (95% confidence)',
                'var_99': 'Value at Risk (99% confidence)',
                'cvar_95': 'Conditional Value at Risk (95%)',
                'cvar_99': 'Conditional Value at Risk (99%)',
                'max_consecutive_losses': 'Maximum consecutive losing periods'
            },
            'trade_analysis': {
                'avg_win': 'Average winning trade P&L',
                'avg_loss': 'Average losing trade P&L',
                'largest_win': 'Largest single winning trade',
                'largest_loss': 'Largest single losing trade',
                'consecutive_wins': 'Maximum consecutive winning trades',
                'consecutive_losses': 'Maximum consecutive losing trades'
            }
        },
        'chart_types': {
            'equity': 'Equity curve showing portfolio value over time',
            'drawdown': 'Underwater curve showing peak-to-trough declines',
            'returns': 'Histogram of return distribution',
            'trades': 'Trade entry/exit points overlaid on equity curve',
            'monthly_returns': 'Heatmap of monthly performance'
        }
    }


@router.get("/chart-data/{backtest_id}")
async def get_chart_data(
    backtest_id: int,
    include_trades: bool = Query(True, description="Include trade markers"),
    include_indicators: bool = Query(True, description="Include strategy indicators"),
    max_candles: Optional[int] = Query(None, description="Maximum number of candles to return")
) -> Dict[str, Any]:
    """
    Get candlestick chart data with trade overlays for TradingView Lightweight Charts
    
    Returns:
    - Candlestick data (OHLC with timestamps)
    - Trade markers (entry/exit points)
    - Indicator data (strategy indicators like moving averages, etc.)
    
    Optimized for TradingView Lightweight Charts format
    """
    result = analytics_service.get_chart_data(
        backtest_id=backtest_id,
        include_trades=include_trades,
        include_indicators=include_indicators,
        max_candles=max_candles
    )
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result
