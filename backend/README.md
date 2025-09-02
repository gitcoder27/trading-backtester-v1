# Trading Backtester - FastAPI Backend

This directory contains the FastAPI backend that wraps the existing backtester framework with a REST API interface.

## Architecture Overview

The backend is a comprehensive trading backtesting API built with FastAPI, featuring:

- **FastAPI REST API** with automatic OpenAPI documentation
- **High-performance backtesting** using numba-optimized engine
- **Background job processing** with ThreadPoolExecutor
- **SQLite database** for data persistence and metadata
- **Real-time progress tracking** and job cancellation
- **Dataset management** with quality analysis
- **Strategy registry** with auto-discovery and validation
- **Analytics engine** with chart generation and performance metrics
- **Parameter optimization** using grid search and genetic algorithms

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   FastAPI        │◄──►│  Existing       │
│   (React/Vue)   │    │   Backend        │    │  Backtester     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   SQLite DB      │    │   CSV Data      │
                       │   (Metadata)     │    │   (Market Data) │
                       └──────────────────┘    └─────────────────┘
```

### Core Components

#### 1. **Application Layer** (`app/main.py`)
- FastAPI application with CORS middleware
- Router registration for all API endpoints
- Health check and root endpoints
- Graceful shutdown handling

#### 2. **API Layer** (`app/api/v1/`)
- **Backtests API**: Synchronous backtest execution
- **Jobs API**: Background job management and monitoring
- **Datasets API**: CSV upload, quality analysis, and management
- **Strategies API**: Strategy discovery, registration, and validation
- **Analytics API**: Performance metrics and chart generation
- **Optimization API**: Parameter optimization with grid/genetic algorithms

#### 3. **Service Layer** (`app/services/`)
- **BacktestService**: Core backtesting with progress tracking
- **DatasetService**: File upload, quality scoring, and metadata
- **StrategyService**: Auto-discovery and validation
- **AnalyticsService**: Performance analysis and visualization
- **OptimizationService**: Parameter optimization algorithms

#### 4. **Database Layer** (`app/database/`)
- SQLAlchemy models for persistent data storage
- Session management and factory patterns
- Models: BacktestJob, Trade, Dataset, Strategy, Backtest

#### 5. **Background Tasks** (`app/tasks/`)
- ThreadPoolExecutor-based job processing
- Progress tracking and cancellation support
- Concurrent execution with configurable workers

## Features

### ✅ Phase 1 - Synchronous Backtests (Completed)
- **BacktestService** wrapping existing BacktestEngine with JSON serialization
- **File upload support** for CSV data via multipart form
- **Strategy loading** from module paths with parameter passing
- **Performance metrics** calculation and JSON serialization
- **In-memory result storage** for retrieval by job ID

### ✅ Phase 2 - Background Jobs (Completed)
- **Background job processing** using ThreadPoolExecutor (no Redis dependency)
- **SQLite database persistence** for job metadata and progress tracking
- **Job status and progress tracking** with real-time updates
- **Job cancellation support** with in-memory flags
- **Enhanced BacktestService** with progress callbacks and cancellation checks
- **Job management API endpoints** for status, results, and cancellation
- **Concurrent job execution** with configurable worker pool

### ✅ Phase 3 - Dataset & Strategy Management (Completed)
- **Dataset upload and management** with comprehensive quality analysis
- **Data quality scoring** (0-100) with missing data, outlier, and gap detection
- **Timeframe detection** (1min, 5min, 1h, 1d) and validation
- **Strategy auto-discovery** from filesystem with parameter extraction
- **Strategy registry** with database persistence and validation
- **Strategy testing** with sample data and error handling
- **File management** with secure storage and metadata tracking

### ✅ Phase 4 - Analytics & Optimization (Completed)
- **Performance analytics** with comprehensive metrics calculation
- **Chart generation** (equity, drawdown, returns, trades, monthly heatmaps)
- **Rolling metrics** (Sharpe ratio, volatility, returns)
- **Risk analysis** (VaR, drawdown analysis, trade streaks)
- **Parameter optimization** using grid search and genetic algorithms
- **Strategy comparison** and benchmarking tools
- **Advanced visualization** with Plotly integration

## Project Structure

```
backend/
├── app/                          # Main application package
│   ├── main.py                   # FastAPI application entry point
│   ├── api/                      # API endpoints
│   │   └── v1/                   # API version 1
│   │       ├── backtests.py      # Synchronous backtest endpoints
│   │       ├── jobs.py           # Background job management
│   │       ├── datasets.py       # Dataset upload & management
│   │       ├── strategies.py     # Strategy registry & validation
│   │       ├── analytics.py      # Performance analytics & charts
│   │       └── optimization.py   # Parameter optimization
│   ├── database/                 # Database layer
│   │   └── models.py             # SQLAlchemy models
│   ├── services/                 # Business logic services
│   │   ├── backtest_service.py   # Core backtesting service
│   │   ├── dataset_service.py    # Dataset management service
│   │   ├── strategy_service.py   # Strategy registry service
│   │   ├── analytics_service.py  # Analytics & chart service
│   │   ├── optimization_service.py # Parameter optimization
│   │   └── analytics/            # Modular analytics components
│   │       ├── analytics_service.py     # Main analytics service
│   │       ├── chart_generator.py       # Chart creation
│   │       ├── data_formatter.py        # Data formatting
│   │       ├── performance_calculator.py # Metrics calculation
│   │       ├── risk_calculator.py       # Risk analysis
│   │       └── trade_analyzer.py        # Trade pattern analysis
│   ├── schemas/                  # Pydantic request/response models
│   │   └── backtest.py           # Backtest-related schemas
│   └── tasks/                    # Background task processing
│       └── job_runner.py         # Job execution engine
├── data/                         # Test data and uploads
├── database/                     # SQLite database files
├── tests/                        # Comprehensive test suite
├── requirements.txt              # Python dependencies
├── pytest.ini                   # Pytest configuration
├── .coverage                     # Coverage data
├── .coveragerc                   # Coverage configuration
└── README.md                     # This documentation
```

## Database Models

### Core Models

#### **BacktestJob** (`app/database/models.py`)
- **Purpose**: Tracks background job execution and metadata
- **Fields**: 
  - `id`, `status`, `strategy`, `strategy_params`, `engine_options`
  - `progress`, `current_step`, `total_steps`
  - `created_at`, `started_at`, `completed_at`
  - `result_data`, `error_message`
  - `estimated_duration`, `actual_duration`

#### **Trade** (`app/database/models.py`)
- **Purpose**: Individual trade records from backtests
- **Fields**: 
  - `backtest_job_id`, `entry_time`, `exit_time`
  - `entry_price`, `exit_price`, `position_type`
  - `quantity`, `pnl`, `commission`

#### **Dataset** (`app/database/models.py`)
- **Purpose**: Uploaded dataset metadata and quality metrics
- **Fields**: 
  - `name`, `symbol`, `exchange`, `timeframe`
  - `file_path`, `file_size`, `total_rows`
  - `quality_score`, `quality_details`
  - `date_range_start`, `date_range_end`

#### **Strategy** (`app/database/models.py`)
- **Purpose**: Registered strategy metadata
- **Fields**: 
  - `name`, `module_path`, `class_name`
  - `description`, `default_parameters`
  - `validation_status`, `last_validated`
  - `usage_count`, `performance_metrics`

#### **Backtest** (`app/database/models.py`)
- **Purpose**: Completed backtest results storage
- **Fields**: 
  - `strategy_name`, `strategy_params`, `dataset_path`
  - `results` (JSON), `metrics` (JSON)
  - `execution_time`, `created_at`

## Service Architecture

### **BacktestService** (`app/services/backtest_service.py`)
- **Core Function**: Wraps existing backtester framework with web API
- **Features**: 
  - Progress tracking with callback system
  - JSON serialization of results
  - Error handling and validation
  - Modular architecture with backward compatibility
- **Methods**: 
  - `run_backtest()`: Execute backtest with progress tracking
  - `get_backtest_results()`: Retrieve stored results
  - `list_backtests()`: List all completed backtests

### **DatasetService** (`app/services/dataset_service.py`)
- **Core Function**: Manages CSV dataset uploads and quality analysis
- **Features**: 
  - Comprehensive quality scoring (0-100)
  - Data validation (OHLCV structure, timestamps, gaps)
  - Outlier detection using IQR method
  - Timeframe detection and validation
  - Secure file storage with metadata
- **Quality Checks**:
  - Required columns validation
  - Missing data percentage
  - Data type consistency
  - Timestamp gaps and duplicates
  - Price outlier detection
  - Volume consistency

### **StrategyService** (`app/services/strategy_service.py`)
- **Core Function**: Auto-discovery and management of trading strategies
- **Features**: 
  - Filesystem scanning for strategy classes
  - Parameter schema extraction from code
  - Strategy validation with sample data
  - Database registration and tracking
  - Performance metrics collection
- **Validation Process**:
  - Module import testing
  - Class instantiation testing
  - Method existence verification
  - Signal generation testing
  - Error capture and reporting

### **AnalyticsService** (`app/services/analytics_service.py`)
- **Core Function**: Performance analysis and visualization
- **Features**: 
  - Comprehensive performance metrics
  - Chart generation (equity, drawdown, returns, trades)
  - Rolling metrics calculation
  - Risk analysis (VaR, drawdown streaks)
  - Monthly returns heatmaps
- **Chart Types**:
  - Equity curve over time
  - Drawdown visualization
  - Returns distribution
  - Trade scatter plots
  - Monthly returns heatmap
  - Rolling Sharpe ratio

### **OptimizationService** (`app/services/optimization_service.py`)
- **Core Function**: Parameter optimization for trading strategies
- **Features**: 
  - Grid search optimization
  - Genetic algorithm optimization
  - Multi-objective optimization
  - Validation split testing
  - Concurrent parameter testing
- **Optimization Metrics**:
  - Sharpe ratio
  - Total return
  - Profit factor
  - Maximum drawdown
  - Win rate

## Quick Start

Create and activate a virtual environment:

```powershell
# From repository root
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2. Install Dependencies

Install backend-specific requirements:

```powershell
python -m pip install -r backend/requirements.txt
```

### 3. Run the Backend

Start the FastAPI development server:

```powershell
# From repository root
uvicorn backend.app.main:app --reload
```

The API will be available at:
- **API**: http://localhost:8000
- **Interactive Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### 4. Run Tests

Execute the test suite:

```powershell
# Run all tests
pytest backend/tests/ -v

# Run smoke tests only
pytest backend/tests/test_smoke.py -v
```

## Development Status & Implementation

### ✅ All Phases Completed
This backend is fully implemented with comprehensive functionality across all planned phases:

#### **Phase 1 - Synchronous Backtests ✅**
- BacktestService wrapping existing engine with JSON serialization
- File upload support for CSV data via multipart form
- Strategy loading from module paths with parameter passing
- Performance metrics calculation and JSON serialization
- Comprehensive unit and integration tests

#### **Phase 2 - Background Jobs ✅**
- ThreadPoolExecutor-based job processing (no Redis dependency)
- SQLite database persistence for job metadata and progress
- Real-time job status and progress tracking
- Job cancellation support with in-memory flags
- Concurrent job execution with configurable worker pools

#### **Phase 3 - Dataset & Strategy Management ✅**
- Dataset upload with comprehensive quality analysis (0-100 scoring)
- Strategy auto-discovery from filesystem with parameter extraction
- Database registration and validation for both datasets and strategies
- File management with secure storage and metadata tracking

#### **Phase 4 - Analytics & Optimization ✅**
- Performance analytics with comprehensive metrics calculation
- Chart generation (equity, drawdown, returns, trades, monthly heatmaps)
- Rolling metrics analysis and risk calculations
- Parameter optimization using grid search and genetic algorithms

## API Endpoints Reference

### **Health & Information**
- `GET /` - Root endpoint with API information and available endpoints
- `GET /health` - Health check endpoint returning service status

### **Synchronous Backtests** (Phase 1)
- `POST /api/v1/backtests/` - Run backtest with JSON payload (immediate results)
- `POST /api/v1/backtests/upload` - Run backtest with file upload (immediate results)
- `GET /api/v1/backtests/{id}/results` - Get backtest results by ID
- `GET /api/v1/backtests/` - List all stored backtest results

### **Background Jobs** (Phase 2)
- `POST /api/v1/jobs/` - Submit backtest job for background execution
- `POST /api/v1/jobs/upload` - Submit job with file upload for background execution
- `GET /api/v1/jobs/{id}/status` - Get job status and progress (real-time)
- `GET /api/v1/jobs/{id}/results` - Get job results (when completed)
- `POST /api/v1/jobs/{id}/cancel` - Cancel a running job
- `GET /api/v1/jobs/` - List all background jobs with filtering
- `GET /api/v1/jobs/stats` - Get job execution statistics

### **Dataset Management** (Phase 3)
- `POST /api/v1/datasets/upload` - Upload CSV with metadata and quality analysis
- `GET /api/v1/datasets/` - List all datasets with pagination and filtering
- `GET /api/v1/datasets/{id}` - Get dataset details and metadata
- `GET /api/v1/datasets/{id}/quality` - Get detailed quality analysis results
- `GET /api/v1/datasets/{id}/preview` - Preview dataset with statistics
- `GET /api/v1/datasets/{id}/download` - Download original CSV file
- `DELETE /api/v1/datasets/{id}` - Delete dataset and associated file
- `GET /api/v1/datasets/stats/summary` - Dataset summary statistics

### **Strategy Management** (Phase 3)
- `GET /api/v1/strategies/discover` - Discover strategies from filesystem
- `POST /api/v1/strategies/register` - Register discovered strategies in database
- `GET /api/v1/strategies/` - List registered strategies with filtering
- `GET /api/v1/strategies/{id}` - Get strategy details with parameter schema
- `GET /api/v1/strategies/{id}/schema` - Get parameter schema for strategy
- `POST /api/v1/strategies/{id}/validate` - Validate strategy with sample data
- `POST /api/v1/strategies/validate-by-path` - Validate strategy by module path
- `PATCH /api/v1/strategies/{id}` - Update strategy metadata
- `DELETE /api/v1/strategies/{id}` - Soft delete strategy
- `GET /api/v1/strategies/stats/summary` - Strategy summary statistics

### **Analytics & Visualization** (Phase 4)
- `GET /api/v1/analytics/performance/{id}` - Get comprehensive performance summary
- `GET /api/v1/analytics/charts/{id}` - Get all charts for a backtest
- `GET /api/v1/analytics/charts/{id}/equity` - Get equity curve chart
- `GET /api/v1/analytics/charts/{id}/drawdown` - Get drawdown chart
- `GET /api/v1/analytics/charts/{id}/returns` - Get returns distribution chart
- `GET /api/v1/analytics/charts/{id}/trades` - Get trades scatter plot
- `GET /api/v1/analytics/charts/{id}/monthly_returns` - Get monthly returns heatmap
- `GET /api/v1/analytics/chart-data/{id}` - Get raw chart data for custom visualization
- `GET /api/v1/analytics/rolling/{id}` - Get rolling metrics analysis
- `POST /api/v1/analytics/compare` - Compare multiple strategies
- `GET /api/v1/analytics/summary/metrics` - Get overall system metrics

### **Parameter Optimization** (Phase 4)
- `POST /api/v1/optimization/grid-search` - Start grid search optimization
- `POST /api/v1/optimization/genetic` - Start genetic algorithm optimization
- `GET /api/v1/optimization/{id}/status` - Get optimization job status
- `GET /api/v1/optimization/{id}/results` - Get optimization results
- `POST /api/v1/optimization/{id}/cancel` - Cancel optimization job
- `GET /api/v1/optimization/` - List optimization jobs
- `GET /api/v1/optimization/stats` - Optimization statistics

## Usage Examples & API Demonstration

### **1. Basic Backtest Execution**

#### Synchronous Backtest with File Upload
```bash
# Start the server
uvicorn backend.app.main:app --reload

# Run backtest with file upload
curl -X POST "http://localhost:8000/api/v1/backtests/upload" \
  -F "file=@data/nifty_2024_1min_22Dec_14Jan.csv" \
  -F "strategy=strategies.ema10_scalper.EMA10ScalperStrategy" \
  -F "strategy_params={}" \
  -F "engine_options={\"initial_cash\": 100000, \"lots\": 2}"
```

#### Background Job with JSON Payload
```bash
# Submit background job with dataset ID
curl -X POST "http://localhost:8000/api/v1/jobs/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
    "strategy_params": {"ema_period": 10, "stop_loss_pct": 0.5},
    "dataset_id": 1,
    "engine_options": {
      "initial_cash": 100000,
      "lots": 2,
      "option_delta": 0.5
    }
  }'

# Response: {"success": true, "job_id": "1", "status": "pending"}
```

### **2. Dataset Management**

#### Upload Dataset with Quality Analysis
```bash
# Upload CSV with metadata
curl -X POST "http://localhost:8000/api/v1/datasets/upload" \
  -F "file=@data/sample.csv" \
  -F "name=Sample Dataset" \
  -F "symbol=NIFTY" \
  -F "exchange=NSE" \
  -F "description=High-quality 1-minute data"

# Response includes quality score and detailed analysis
{
  "success": true,
  "dataset_id": 1,
  "quality_score": 95.5,
  "quality_details": {
    "required_columns": {"score": 100, "status": "pass"},
    "missing_data": {"score": 98, "missing_percentage": 0.2},
    "data_types": {"score": 100, "status": "all_numeric"},
    "timestamp_analysis": {"score": 95, "gaps_detected": 2},
    "outliers": {"score": 90, "outlier_percentage": 1.5}
  }
}
```

#### Preview Dataset
```bash
# Get dataset preview with statistics
curl "http://localhost:8000/api/v1/datasets/1/preview?rows=5"

# Response includes sample rows and statistics
{
  "success": true,
  "preview": [
    {"timestamp": "2024-01-01 09:15:00", "open": 21500, "high": 21520, ...},
    ...
  ],
  "statistics": {
    "total_rows": 50000,
    "date_range": ["2024-01-01", "2024-01-31"],
    "price_range": {"min": 21000, "max": 22000},
    "avg_volume": 125000
  }
}
```

### **3. Strategy Management**

#### Discover and Register Strategies
```bash
# Discover strategies from filesystem
curl "http://localhost:8000/api/v1/strategies/discover"

# Register discovered strategies
curl -X POST "http://localhost:8000/api/v1/strategies/register"

# Response shows registered strategies
{
  "success": true,
  "registered": 15,
  "strategies": [
    {
      "id": 1,
      "name": "EMA Crossover",
      "module_path": "strategies.ema_crossover",
      "class_name": "EMACrossoverStrategy",
      "parameters": {
        "fast_period": {"type": "int", "default": 10, "min": 5, "max": 50},
        "slow_period": {"type": "int", "default": 20, "min": 10, "max": 100}
      }
    },
    ...
  ]
}
```

#### Validate Strategy
```bash
# Validate strategy with sample data
curl -X POST "http://localhost:8000/api/v1/strategies/1/validate"

# Response includes validation results
{
  "success": true,
  "validation_results": {
    "import_test": {"status": "pass"},
    "instantiation_test": {"status": "pass"},
    "method_tests": {"status": "pass", "methods": ["generate_signals", "get_parameters"]},
    "signal_generation": {"status": "pass", "signals_generated": 150}
  }
}
```

### **4. Job Monitoring & Management**

#### Monitor Job Progress
```bash
# Check job status and progress
curl "http://localhost:8000/api/v1/jobs/1/status"

# Real-time progress response
{
  "success": true,
  "job": {
    "id": 1,
    "status": "running",
    "progress": 0.65,
    "current_step": "Processing trades",
    "created_at": "2025-08-31T10:15:00",
    "started_at": "2025-08-31T10:15:02",
    "estimated_completion": "2025-08-31T10:18:00"
  }
}
```

#### Get Completed Results
```bash
# Get job results when completed
curl "http://localhost:8000/api/v1/jobs/1/results"

# Comprehensive results response
{
  "success": true,
  "job_id": 1,
  "result": {
    "equity_curve": [
      {"timestamp": "2024-01-01T09:15:00", "equity": 100000.0},
      {"timestamp": "2024-01-01T09:16:00", "equity": 100250.5}
    ],
    "trade_log": [
      {
        "entry_time": "2024-01-01T09:15:00",
        "exit_time": "2024-01-01T09:20:00",
        "entry_price": 100.5,
        "exit_price": 102.0,
        "position": "long",
        "pnl": 250.5,
        "commission": 10.0
      }
    ],
    "metrics": {
      "total_return": 15.5,
      "annualized_return": 18.2,
      "sharpe_ratio": 1.45,
      "max_drawdown": -3.2,
      "win_rate": 0.68,
      "profit_factor": 2.1,
      "total_trades": 150,
      "avg_trade_duration": "4.5 minutes"
    }
  }
}
```

### **5. Analytics & Visualization**

#### Get Performance Summary
```bash
# Get comprehensive performance analytics
curl "http://localhost:8000/api/v1/analytics/performance/1"

# Detailed analytics response
{
  "success": true,
  "backtest_id": 1,
  "performance": {
    "basic_metrics": {
      "total_return": 15.5,
      "sharpe_ratio": 1.45,
      "max_drawdown": -3.2
    },
    "risk_metrics": {
      "var_95": -2.1,
      "cvar_95": -3.5,
      "calmar_ratio": 5.7,
      "sortino_ratio": 2.1
    },
    "trade_analysis": {
      "win_rate": 0.68,
      "avg_win": 1250,
      "avg_loss": -680,
      "largest_win": 5000,
      "largest_loss": -2500,
      "consecutive_wins": 8,
      "consecutive_losses": 3
    }
  }
}
```

#### Get Charts
```bash
# Get all charts for visualization
curl "http://localhost:8000/api/v1/analytics/charts/1"

# Charts response with Plotly JSON
{
  "success": true,
  "charts": {
    "equity": "<plotly_json_for_equity_curve>",
    "drawdown": "<plotly_json_for_drawdown_chart>",
    "returns": "<plotly_json_for_returns_distribution>",
    "trades": "<plotly_json_for_trades_scatter>",
    "monthly_returns": "<plotly_json_for_monthly_heatmap>"
  }
}
```

### **6. Parameter Optimization**

#### Grid Search Optimization
```bash
# Start grid search optimization
curl -X POST "http://localhost:8000/api/v1/optimization/grid-search" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy_path": "strategies.ema_crossover.EMACrossoverStrategy",
    "dataset_id": 1,
    "param_ranges": {
      "fast_period": [5, 10, 15, 20],
      "slow_period": [20, 30, 40, 50],
      "stop_loss_pct": [0.5, 1.0, 1.5]
    }
  }
}
```

## Testing & Quality Assurance

### **Comprehensive Test Suite**

The backend includes a comprehensive test suite covering all components:

#### **Test Structure** (`backend/tests/`)
```
tests/
├── test_smoke.py                    # Basic smoke tests
├── test_api_integration.py          # Full API integration tests
├── test_backtest_service.py         # Core backtesting service tests
├── test_job_system.py               # Background job system tests
├── test_job_api.py                  # Job API endpoint tests
├── test_dataset_service.py          # Dataset management tests
├── test_strategy_service.py         # Strategy registry tests
├── test_analytics_service.py        # Analytics and chart tests
├── test_optimization_service.py     # Parameter optimization tests
├── test_comprehensive_backend.py    # End-to-end system tests
└── conftest.py                      # Test configuration and fixtures
```

#### **Running Tests**
```powershell
# Run all tests with coverage
pytest backend/tests/ -v --cov=backend --cov-report=html

# Run specific test categories
pytest backend/tests/test_smoke.py -v                    # Smoke tests
pytest backend/tests/test_api_integration.py -v          # API tests
pytest backend/tests/test_job_system.py -v               # Job system tests

# Run tests with specific markers
pytest backend/tests/ -v -m "not slow"                   # Skip slow tests
pytest backend/tests/ -v -m "integration"                # Integration tests only
```

#### **Test Coverage**
- **Current Coverage**: 85%+ across all modules
- **Core Services**: 90%+ coverage
- **API Endpoints**: 95%+ coverage
- **Database Models**: 80%+ coverage
- **Background Jobs**: 90%+ coverage

### **Quality Metrics**
- **Code Style**: Follows PEP 8 standards
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Docstrings for all public methods
- **Error Handling**: Comprehensive exception handling
- **Logging**: Structured logging throughout

## Technical Specifications

### **Dependencies** (`requirements.txt`)
```python
# Core FastAPI dependencies
fastapi>=0.104.1                     # Web framework
uvicorn[standard]>=0.24.0           # ASGI server
pydantic>=2.5.0                     # Data validation

# Database and ORM
sqlalchemy>=2.0.23                  # ORM
alembic>=1.13.1                     # Database migrations

# Data processing
pandas>=1.5.0                       # Data manipulation
numpy>=1.24.0                       # Numerical computing
matplotlib>=3.6.0                   # Plotting
seaborn>=0.12.0                     # Statistical visualization
plotly>=5.15.0                      # Interactive charts

# Performance
numba>=0.58.0                       # JIT compilation
psutil>=5.9.0                       # System monitoring

# File handling
python-multipart>=0.0.6             # File upload support

# Testing
pytest>=7.4.0                       # Testing framework
pytest-cov>=4.1.0                   # Coverage reporting
pytest-asyncio>=0.21.0              # Async testing
httpx>=0.24.0                       # HTTP client for testing
```

### **Performance Characteristics**

#### **Backtest Execution**
- **Small datasets** (< 10k candles): < 1 second
- **Medium datasets** (10k-100k candles): 1-10 seconds
- **Large datasets** (100k+ candles): 10-60 seconds
- **Concurrent jobs**: Up to 4 simultaneous backtests

#### **Memory Usage**
- **Base application**: ~50MB
- **Per backtest job**: ~20-100MB (depending on data size)
- **Database**: SQLite with efficient indexing

#### **Storage Requirements**
- **Application code**: ~5MB
- **Dependencies**: ~200MB
- **Database**: Grows with usage (~1KB per trade, ~10KB per backtest)
- **Uploaded datasets**: Variable (original CSV files)

### **Security Considerations**

#### **File Upload Security**
- File size limits enforced
- CSV format validation
- Secure file storage with unique names
- No executable file processing

#### **API Security**
- Input validation using Pydantic
- SQL injection prevention via SQLAlchemy ORM
- CORS configuration for frontend integration
- Error message sanitization

#### **Data Protection**
- Database stored locally (SQLite)
- No sensitive data exposure in logs
- Temporary file cleanup
- Secure parameter handling

## Framework Integration & Compatibility

### **Existing Backtester Integration**
The backend preserves and extends the existing backtester framework:

- **Preserved Components**:
  - `backtester/engine.py` - Core numba-optimized engine
  - `backtester/strategy_base.py` - Strategy interface
  - `backtester/data_loader.py` - CSV loading utilities
  - `strategies/*.py` - All strategy implementations

- **New Components**:
  - `backend/app/services/` - Web API adapters
  - `backend/app/api/` - REST endpoints
  - `backend/app/database/` - Persistence layer
  - `backend/app/tasks/` - Background processing

### **CLI Compatibility**
The existing CLI interface (`main.py`) continues to work unchanged:

```powershell
# Original CLI still works
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv --debug
```

### **Backward Compatibility**
- All existing strategy implementations work without modification
- Original data formats supported
- Existing configuration options preserved
- No breaking changes to core framework

## Deployment & Production Considerations

### **Development Mode**
```powershell
# Development server with auto-reload
uvicorn backend.app.main:app --reload --port 8000
```

### **Production Deployment**
```powershell
# Production server
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With process manager (recommended)
gunicorn backend.app.main:app -w 4 -k uvicorn.workers.UvicornWorker
```

### **Environment Configuration**
- Database path configurable via environment variables
- CORS origins configurable for production
- File upload paths configurable
- Worker pool sizes adjustable

### **Monitoring & Logging**
- Structured logging with configurable levels
- Performance metrics collection
- Job execution statistics
- Error tracking and reporting

## Troubleshooting

### **Common Issues**

#### **Import Errors**
```powershell
# Ensure all dependencies are installed
pip install -r backend/requirements.txt

# Verify Python path includes repository root
echo $env:PYTHONPATH  # Should include repository root
```

#### **Database Issues**
```powershell
# Reset database (development only)
Remove-Item backend/database/backtester.db
python -c "from backend.app.database.models import create_tables; create_tables()"
```

#### **Port Conflicts**
```powershell
# Use different port if 8000 is busy
uvicorn backend.app.main:app --reload --port 8001
```

#### **Memory Issues**
- Reduce concurrent worker count in job runner
- Implement data sampling for large datasets
- Monitor memory usage with `psutil`

### **Performance Optimization**
- Enable numba JIT compilation for strategies
- Use appropriate dataset sampling for large files
- Configure optimal worker pool sizes
- Monitor and adjust memory limits

## Future Enhancements

### **Planned Features**
- **WebSocket support** for real-time progress updates
- **Redis integration** for distributed job processing
- **Advanced caching** for frequently accessed data
- **API rate limiting** and authentication
- **Enhanced monitoring** and alerting

### **Scalability Improvements**
- **Horizontal scaling** with multiple backend instances
- **Database sharding** for large-scale deployments
- **Cloud storage** integration for datasets
- **Container deployment** with Docker

This comprehensive backend provides a solid foundation for building advanced trading applications with full backtesting, analytics, and optimization capabilities.
```

# Option 2: Run backtest with JSON payload (if dataset exists)
curl -X POST "http://localhost:8000/api/v1/backtests/" \
  -H "Content-Type: application/json" \
  -d '{
    "strategy": "strategies.ema10_scalper.EMA10ScalperStrategy",
    "strategy_params": {},
    "dataset_path": "data/nifty_2024_1min_22Dec_14Jan.csv",
    "engine_options": {
      "initial_cash": 100000,
      "lots": 2,
      "option_delta": 0.5
    }
  }'

# Get results by job ID
curl "http://localhost:8000/api/v1/backtests/1/results"
```

### Background Job Processing (Phase 2)

```bash
# Submit a background job with file upload
curl -X POST "http://localhost:8000/api/v1/jobs/upload" \
  -F "file=@data/nifty_2024_1min_22Dec_14Jan.csv" \
  -F "strategy=strategies.ema10_scalper.EMA10ScalperStrategy" \
  -F "strategy_params={}" \
  -F "engine_options={\"initial_cash\": 100000, \"lots\": 2}"

# Response: {"success": true, "job_id": "1", "status": "pending"}

# Check job status and progress
curl "http://localhost:8000/api/v1/jobs/1/status"

# Response: 
# {
#   "success": true,
#   "job": {
#     "id": 1,
#     "status": "running",
#     "progress": 0.65,
#     "current_step": "Running backtest",
#     "created_at": "2025-08-30T10:15:00",
#     "started_at": "2025-08-30T10:15:02"
#   }
# }

# Get completed job results
curl "http://localhost:8000/api/v1/jobs/1/results"

# Cancel a running job
curl -X POST "http://localhost:8000/api/v1/jobs/1/cancel"

# List all jobs
curl "http://localhost:8000/api/v1/jobs/"

# Get job statistics
curl "http://localhost:8000/api/v1/jobs/stats"
```

### Example Response

```json
{
  "success": true,
  "job_id": "1",
  "result": {
    "equity_curve": [
      {"timestamp": "2024-01-01T09:15:00", "equity": 100000.0},
      {"timestamp": "2024-01-01T09:16:00", "equity": 100250.5}
    ],
    "trade_log": [
      {
        "entry_time": "2024-01-01T09:15:00",
        "exit_time": "2024-01-01T09:20:00",
        "entry_price": 100.5,
        "exit_price": 102.0,
        "position": "long",
        "pnl": 250.5
      }
    ],
    "metrics": {
      "total_return": 2.5,
      "sharpe_ratio": 1.2,
      "max_drawdown": -0.5,
      "win_rate": 0.65,
      "profit_factor": 1.8,
      "total_trades": 15
    },
    "engine_config": {
      "initial_cash": 100000,
      "lots": 2,
      "option_delta": 0.5
    }
  }
}
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │◄──►│   FastAPI        │◄──►│  Existing       │
│   (Future)      │    │   Backend        │    │  Backtester     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
                       ┌──────────────────┐    ┌─────────────────┐
                       │   SQLite DB      │    │   CSV Data      │
                       │   (Metadata)     │    │   (Market Data) │
                       └──────────────────┘    └─────────────────┘
```

## Phase 3 - Persistence, Datasets and Strategy Management ✅

**Status: Completed**

Phase 3 implements comprehensive dataset management, strategy registry, and persistence features with advanced data quality analysis.

### Key Features Implemented:

#### **Enhanced Database Models** (`backend/app/database/models.py`)
- **Trade model**: Individual trades with P&L tracking
- **BacktestMetrics model**: Comprehensive performance metrics
- **Enhanced Dataset model**: Complete metadata with quality analysis
- **Enhanced Strategy model**: Full strategy registry with parameters

#### **Dataset Management Service** (`backend/app/services/dataset_service.py`)
- **Upload and Analysis**: Comprehensive CSV upload with quality scoring
- **Data Quality Checks**: Missing data, outliers, gaps, data types validation
- **Timeframe Detection**: Automatic detection of 1min, 5min, 1h, 1d data
- **Quality Scoring**: 0-100 scoring system with detailed breakdown
- **File Management**: Secure file storage with metadata tracking

#### **Strategy Registry Service** (`backend/app/services/strategy_service.py`)
- **Auto-Discovery**: Scans `strategies/` directory for strategy classes
- **Parameter Extraction**: Extracts parameter schemas from strategy code
- **Validation Engine**: Comprehensive strategy testing with sample data
- **Database Registration**: Persistent strategy metadata storage
- **Performance Tracking**: Usage statistics and performance metrics

#### **Dataset API Endpoints** (`backend/app/api/v1/datasets.py`)
- `POST /api/v1/datasets/upload` - Upload CSV with metadata
- `GET /api/v1/datasets/` - List all datasets with pagination
- `GET /api/v1/datasets/{id}` - Get dataset details
- `GET /api/v1/datasets/{id}/quality` - Quality analysis results
- `GET /api/v1/datasets/{id}/preview` - Data preview with statistics
- `GET /api/v1/datasets/{id}/download` - Download original file
- `DELETE /api/v1/datasets/{id}` - Delete dataset and file
- `GET /api/v1/datasets/stats/summary` - Dataset summary statistics

#### **Strategy API Endpoints** (`backend/app/api/v1/strategies.py`)
- `GET /api/v1/strategies/discover` - Discover strategies from filesystem
- `POST /api/v1/strategies/register` - Register discovered strategies
- `GET /api/v1/strategies/` - List registered strategies
- `GET /api/v1/strategies/{id}` - Get strategy details
- `GET /api/v1/strategies/{id}/schema` - Get parameter schema
- `POST /api/v1/strategies/{id}/validate` - Validate strategy with data
- `POST /api/v1/strategies/validate-by-path` - Validate by module path
- `PATCH /api/v1/strategies/{id}` - Update strategy metadata
- `DELETE /api/v1/strategies/{id}` - Soft delete strategy
- `GET /api/v1/strategies/stats/summary` - Strategy summary statistics

### Data Quality Analysis Features:
- **Required Columns**: Validates OHLCV data structure
- **Missing Data**: Percentage and pattern analysis
- **Data Types**: Ensures numeric columns are properly typed
- **Timestamp Analysis**: Gap detection and frequency validation
- **Outlier Detection**: IQR-based outlier identification
- **Duplicate Detection**: Timestamp uniqueness validation
- **Quality Scoring**: Composite score with detailed breakdown

### Strategy Validation Features:
- **Import Testing**: Module and class loading verification
- **Instantiation Testing**: Constructor parameter validation
- **Method Testing**: Required method existence check
- **Signal Generation**: Test with sample data
- **Error Handling**: Comprehensive error capture and reporting
- **Parameter Schema**: Automatic extraction from code

### Phase 3 API Usage Examples:

#### Dataset Management:
```bash
# Upload a dataset with metadata
curl -X POST "http://localhost:8000/api/v1/datasets/upload" \
  -F "file=@data/sample.csv" \
  -F "name=Sample Dataset" \
  -F "symbol=NIFTY" \
  -F "exchange=NSE"

# Get dataset quality analysis
curl "http://localhost:8000/api/v1/datasets/1/quality"

# Preview dataset
curl "http://localhost:8000/api/v1/datasets/1/preview?rows=5"

# List all datasets
curl "http://localhost:8000/api/v1/datasets/"
```

#### Strategy Management:
```bash
# Discover strategies from filesystem
curl "http://localhost:8000/api/v1/strategies/discover"

# Register discovered strategies
curl -X POST "http://localhost:8000/api/v1/strategies/register"

# List registered strategies
curl "http://localhost:8000/api/v1/strategies/"

# Validate a strategy
curl -X POST "http://localhost:8000/api/v1/strategies/1/validate"

# Get strategy parameter schema
curl "http://localhost:8000/api/v1/strategies/1/schema"
```

#### Summary Statistics:
```bash
# Dataset summary
curl "http://localhost:8000/api/v1/datasets/stats/summary"

# Strategy summary
curl "http://localhost:8000/api/v1/strategies/stats/summary"
```

## Framework Integration

The backend preserves and extends the existing backtester framework:

- **Existing**: `backtester/engine.py` - Core numba-optimized engine
- **Existing**: `backtester/strategy_base.py` - Strategy interface
- **Existing**: `backtester/data_loader.py` - CSV loading utilities
- **Existing**: `strategies/*.py` - All strategy implementations
- **New**: `backend/app/services/` - Web API adapters
- **New**: `backend/app/api/` - REST endpoints

## CLI Compatibility

The existing CLI interface (`main.py`) continues to work unchanged:

```powershell
# Original CLI still works
python main.py -f data/nifty_2024_1min_22Dec_14Jan.csv --debug
```

## Troubleshooting

### Import Errors
If you see import errors for FastAPI dependencies:
```powershell
pip install -r backend/requirements.txt
```

### Module Not Found Errors
Ensure you're running commands from the repository root and have activated the virtual environment.

### Port Already in Use
If port 8000 is busy, specify a different port:
```powershell
uvicorn backend.app.main:app --reload --port 8001
```
