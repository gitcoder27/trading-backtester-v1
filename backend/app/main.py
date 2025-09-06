"""
FastAPI backend for trading backtester
Wraps existing backtester framework with web API
"""

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import atexit

from backend.app.api.v1.backtests import router as backtests_router
from backend.app.api.v1.jobs import router as jobs_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.strategies import router as strategies_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.optimization import router as optimization_router
from backend.app.tasks.job_runner import shutdown_job_runner

app = FastAPI(
    title="Trading Backtester API",
    description="High-performance backtesting API for trading strategies",
    version="1.0.0"
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React dev server (default)
        "http://localhost:3001",    # React dev server (alternative)
        "http://localhost:5173",    # Vite dev server (default)
        "http://localhost:5174",    # Vite dev server (alternative)
        "http://localhost:5175",    # Vite dev server (backup)
        "http://127.0.0.1:3000",    # Alternative localhost format
        "http://127.0.0.1:3001",    # Alternative localhost format
        "http://127.0.0.1:5173",    # Alternative localhost format
        "http://127.0.0.1:5174",    # Alternative localhost format
        "http://127.0.0.1:5175"     # Alternative localhost format
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(backtests_router)
app.include_router(jobs_router)
app.include_router(datasets_router)
app.include_router(strategies_router)
app.include_router(analytics_router)
app.include_router(optimization_router)

# Register cleanup on exit
atexit.register(shutdown_job_runner)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "trading-backtester-api",
        "version": "1.0.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Trading Backtester API",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "sync_backtests": "/api/v1/backtests",
            "background_jobs": "/api/v1/jobs",
            "datasets": "/api/v1/datasets",
            "strategies": "/api/v1/strategies",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# Generic OPTIONS handler to satisfy preflight checks in tests without Origin header
@app.options("/{full_path:path}")
async def preflight_ok(full_path: str):
    return Response(status_code=200)
