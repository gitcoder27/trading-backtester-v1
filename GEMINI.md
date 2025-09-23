# GEMINI.md - Trading Backtester Pro

This document provides a comprehensive overview of the Trading Backtester Pro project, its architecture, and development guidelines. It is intended to be used as a reference for developers and AI agents working on the project.

## 1. Project Overview

This is a high-performance, modular trading backtesting framework with a FastAPI backend and a modern React + TypeScript frontend. The core backtester engine is optimized with Numba for high-speed processing of large intraday datasets. The framework provides rich metrics, HTML reporting, and a comprehensive analytics API.

**Key Technologies:**

*   **Backend:** Python, FastAPI, SQLAlchemy, Numba, Pandas
*   **Frontend:** React, TypeScript, Vite, Tailwind CSS, React Query
*   **Database:** SQLite (default)
*   **Testing:** Pytest, Vitest

---

## 2. Architecture

The project is structured into three main components:

### 2.1. Backend (FastAPI + SQLAlchemy)

*   **Entry Point:** `backend/app/main.py`
*   **Routers:** `backend/app/api/v1/` for `backtests.py`, `jobs.py`, `datasets.py`, `strategies.py`, `analytics.py`, `optimization.py`.
*   **Database:** `backend/app/database/models.py` defines the database models. The default database is SQLite, located at `backend/database/backtester.db`.
*   **Services:** `backend/app/services/` contains the business logic for the application.
*   **Background Jobs:** `backend/app/tasks/job_runner.py` manages threaded jobs with progress and cancellation.
*   **Schemas:** `backend/app/schemas/` contains Pydantic models for request and response validation.

### 2.2. Frontend (React + Vite + TS)

*   **Entry Point:** `src/main.tsx`
*   **State Management:** Zustand for global state management (`src/stores/`).
*   **Data Fetching:** `@tanstack/react-query` for data fetching and caching (`src/lib/queryClient.ts`).
*   **UI Components:** Reusable UI components are located in `src/components/ui/`.
*   **Pages:** Route-level components are located in `src/pages/`.
*   **Styling:** Tailwind CSS for styling (`tailwind.config.js`).

### 2.3. Backtester (Core Engine)

*   **Engine:** `backtester/engine.py` executes strategies on data.
*   **Strategy Base:** `backtester/strategy_base.py` defines the `StrategyBase` class that all strategies must inherit from.
*   **Data Loading:** `backtester/data_loader.py` for loading and preparing data.
*   **Metrics:** `backtester/metrics.py` for calculating performance metrics.
*   **Reporting:** `backtester/reporting.py` for generating reports.

---

## 3. Building and Running

### 3.1. Prerequisites

*   Python 3.10+
*   Node.js 18+
*   `npm`

### 3.2. Installation

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd <repository-directory>
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install Python dependencies:**
    ```bash
    pip install -r requirements.txt
    pip install -r backend/requirements.txt
    ```

4.  **Install frontend dependencies:**
    ```bash
    npm -C frontend install
    ```

### 3.3. Running the Application

1.  **Start the backend server:**
    ```bash
    uvicorn backend.app.main:app --reload
    ```
    The API will be available at `http://localhost:8000`.

2.  **Start the frontend development server:**
    ```bash
    npm -C frontend run dev
    ```
    The frontend will be available at `http://localhost:5173`.

---

## 4. Development Conventions

### 4.1. Code Style

*   **Python:** Follow the PEP 8 style guide.
*   **TypeScript/React:** Follow the conventions enforced by the ESLint configuration.

### 4.2. Testing

*   **Frameworks:** Pytest for the backend and core engine, and Vitest for the frontend.
*   **Core Tests:** `pytest tests -q`
*   **Backend Tests:** `pytest -c backend/pytest.ini -q`
*   **Frontend Tests:** `npm -C frontend run test`

### 4.3. Strategies

*   New trading strategies should be added to the `strategies/` directory.
*   Each strategy should be in its own file (e.g., `my_strategy.py`) and inherit from the `StrategyBase` class.

### 4.4. Commits

*   Commit messages should be clear and concise, following the conventional commit format.

---

## 5. Agent Instructions

*   **Do not run backend or frontend servers unless explicitly instructed.**
*   Prefer minimal, focused diffs.
*   Use `rg` for searching and `fd` for finding files.
*   Use `jq` for parsing JSON.
*   Cap file reads at 250 lines.