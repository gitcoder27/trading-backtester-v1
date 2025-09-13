"""
Analytics API endpoints
Provides comprehensive analytics and visualization for backtest results
"""

from fastapi import APIRouter, HTTPException, Query, Request, Response
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
import hashlib
from datetime import datetime

from backend.app.services.analytics_service import AnalyticsService
from backend.app.database.models import get_session_factory, Backtest

router = APIRouter(prefix="/api/v1/analytics", tags=["analytics"])
analytics_service = AnalyticsService()
SessionLocal = get_session_factory()


def _etag_for_backtest(backtest_id: int, extra: str = "") -> Dict[str, str]:
    """Compute ETag and Last-Modified headers for a backtest payload.

    extra: string derived from query params to vary the cache key.
    """
    db = SessionLocal()
    try:
        bt = db.query(Backtest).filter(Backtest.id == backtest_id).first()
        last_mod_dt: Optional[datetime] = bt.completed_at if bt and bt.completed_at else (bt.created_at if bt else None)
        last_mod = last_mod_dt.isoformat() + 'Z' if last_mod_dt else '0'
        raw = f"{backtest_id}:{last_mod}:{extra}"
        etag = hashlib.md5(raw.encode('utf-8')).hexdigest()
        return {
            'ETag': etag,
            'Last-Modified': last_mod,
            'Cache-Control': 'public, max-age=60'
        }
    finally:
        db.close()


class CompareStrategiesRequest(BaseModel):
    backtest_ids: List[int]


@router.get("/performance/{backtest_id}")
async def get_performance_summary(
    request: Request,
    response: Response,
    backtest_id: int,
    sections: Optional[List[str]] = Query(
        None,
        description=(
            "Optional sections to compute/return: "
            "basic_metrics, advanced_analytics, risk_metrics, trade_analysis, daily_target_stats, drawdown_analysis"
        ),
    ),
) -> Dict[str, Any]:
    """
    Get comprehensive performance analytics for a backtest
    
    Returns:
    - Basic metrics (return, Sharpe, drawdown, etc.)
    - Advanced analytics (volatility, skewness, Sortino ratio, etc.)
    - Trade analysis (win rate, avg win/loss, consecutive trades, etc.)
    - Risk metrics (VaR, CVaR, max consecutive losses, etc.)
    - Time analysis (performance by hour, weekday, month)
    """
    result = analytics_service.get_performance_summary(backtest_id, sections)
    # Attach caching headers (no conditional 304 to keep clients simple)
    extra = ",".join(sorted(sections)) if sections else "all"
    headers = _etag_for_backtest(backtest_id, extra=extra)
    for k, v in headers.items():
        response.headers[k] = v
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result


@router.get("/charts/{backtest_id}")
async def get_charts(
    request: Request,
    response: Response,
    backtest_id: int,
    chart_types: Optional[List[str]] = Query(None, description="Chart types to generate: equity, drawdown, returns, trades, monthly_returns"),
    max_points: Optional[int] = Query(None, ge=100, le=200000, description="Maximum points per series (downsampling)"),
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
    result = analytics_service.get_charts(backtest_id, chart_types, max_points=max_points)
    extra = f"{','.join(sorted(chart_types)) if chart_types else 'all'}:{max_points or 'none'}"
    headers = _etag_for_backtest(backtest_id, extra=extra)
    for k, v in headers.items():
        response.headers[k] = v
    
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
async def get_equity_chart(request: Request, response: Response, backtest_id: int, max_points: Optional[int] = Query(None, ge=100, le=200000)) -> Dict[str, Any]:
    """Get equity curve chart for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['equity'], max_points=max_points)
    headers = _etag_for_backtest(backtest_id, extra=f"equity:{max_points or 'none'}")
    for k, v in headers.items():
        response.headers[k] = v
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('equity')
    }


@router.get("/charts/{backtest_id}/drawdown")
async def get_drawdown_chart(request: Request, response: Response, backtest_id: int, max_points: Optional[int] = Query(None, ge=100, le=200000)) -> Dict[str, Any]:
    """Get drawdown chart for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['drawdown'], max_points=max_points)
    headers = _etag_for_backtest(backtest_id, extra=f"drawdown:{max_points or 'none'}")
    for k, v in headers.items():
        response.headers[k] = v
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('drawdown')
    }


@router.get("/charts/{backtest_id}/returns")
async def get_returns_chart(request: Request, response: Response, backtest_id: int) -> Dict[str, Any]:
    """Get returns distribution chart for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['returns'])
    headers = _etag_for_backtest(backtest_id, extra="returns")
    for k, v in headers.items():
        response.headers[k] = v
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('returns')
    }


@router.get("/charts/{backtest_id}/trades")
async def get_trades_chart(request: Request, response: Response, backtest_id: int, max_points: Optional[int] = Query(None, ge=100, le=200000)) -> Dict[str, Any]:
    """Get trades chart overlaid on equity curve"""
    result = analytics_service.get_charts(backtest_id, ['trades'], max_points=max_points)
    headers = _etag_for_backtest(backtest_id, extra=f"trades:{max_points or 'none'}")
    for k, v in headers.items():
        response.headers[k] = v
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return {
        'success': True,
        'backtest_id': backtest_id,
        'chart': result['charts'].get('trades')
    }


@router.get("/charts/{backtest_id}/monthly_returns")
async def get_monthly_returns_chart(request: Request, response: Response, backtest_id: int) -> Dict[str, Any]:
    """Get monthly returns heatmap for a specific backtest"""
    result = analytics_service.get_charts(backtest_id, ['monthly_returns'])
    headers = _etag_for_backtest(backtest_id, extra="monthly_returns")
    for k, v in headers.items():
        response.headers[k] = v
    
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
    max_candles: Optional[int] = Query(None, ge=1, le=200000, description="Maximum number of candles to return (downsampling)"),
    start: Optional[str] = Query(None, description="Start datetime or date (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="End datetime or date (YYYY-MM-DD)"),
    tz: Optional[str] = Query(None, description="Timezone of dataset (e.g., 'Asia/Kolkata') for date parsing and display consistency")
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
        max_candles=max_candles,
        start=start,
        end=end,
        tz=tz,
    )
    
    if not result['success']:
        raise HTTPException(status_code=404, detail=result['error'])
    
    return result
