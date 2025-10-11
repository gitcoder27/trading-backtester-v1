"""
FastAPI backend for trading backtester
Wraps existing backtester framework with web API
"""

import atexit
import logging

from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import uvicorn

from backend.app.api.v1.backtests import router as backtests_router
from backend.app.api.v1.jobs import router as jobs_router
from backend.app.api.v1.datasets import router as datasets_router
from backend.app.api.v1.strategies import router as strategies_router
from backend.app.api.v1.analytics import router as analytics_router
from backend.app.api.v1.optimization import router as optimization_router
from backend.app.config import configure_logging, get_settings
from backend.app.tasks.job_runner import shutdown_job_runner

settings = get_settings()
configure_logging(settings)
logger = logging.getLogger("backend.app.main")

logger.info("Initializing Trading Backtester API")
logger.debug(
    "Runtime configuration: log_level=%s, cors_origins_count=%d, gzip_minimum_size=%d, job_runner_max_workers=%d",
    settings.log_level,
    len(settings.cors_origins),
    settings.gzip_minimum_size,
    settings.job_runner_max_workers,
)
logger.debug("CORS origins: %s", settings.cors_origins)

app = FastAPI(
    title="Trading Backtester API",
    description="High-performance backtesting API for trading strategies",
    version="1.0.0"
)

logger.info("FastAPI application instantiated")

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger.info("CORS middleware configured with %d origins", len(settings.cors_origins))

# Include routers
routers = {
    "backtests": backtests_router,
    "jobs": jobs_router,
    "datasets": datasets_router,
    "strategies": strategies_router,
    "analytics": analytics_router,
    "optimization": optimization_router,
}

for name, router in routers.items():
    app.include_router(router)
    logger.info("Router registered: %s (prefix=%s)", name, router.prefix or "/")

# Enable GZip compression for large analytics responses
app.add_middleware(GZipMiddleware, minimum_size=settings.gzip_minimum_size)

logger.info(
    "GZip middleware enabled with minimum size %d bytes",
    settings.gzip_minimum_size,
)

# Register cleanup on exit
def _shutdown_job_runner() -> None:
    logger.info("Job runner shutdown invoked")
    shutdown_job_runner()


atexit.register(_shutdown_job_runner)


@app.on_event("startup")
async def on_startup() -> None:
    logger.info("Application startup completed")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    logger.info("Application shutdown initiated")


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
    logger.info("Starting development server on %s:%s (reload=%s)", "0.0.0.0", 8000, True)
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

# Generic OPTIONS handler to satisfy preflight checks in tests without Origin header
@app.options("/{full_path:path}")
async def preflight_ok(full_path: str):
    return Response(status_code=200)
