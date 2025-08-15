# Gemini Code Assistant Context

This document provides context for the Gemini Code Assistant to understand the `trading-backtester-v1` project.

## Project Overview

This project is a powerful and interactive backtesting framework for algorithmic trading strategies, built in Python. It allows users to test and analyze trading strategies on historical market data.

The project has two main interfaces:

1.  **Streamlit Web App (`app.py`):** A feature-rich graphical user interface for interactive backtesting, visualization, and analysis.
2.  **Command-Line Interface (`main.py`):** For automated backtesting and scripting.

The core backtesting logic is located in the `backtester/` directory, and individual trading strategies are defined in the `strategies/` directory.

### Key Technologies

*   **Backend:** Python
*   **Web UI:** Streamlit
*   **Data Handling:** pandas
*   **Charting:** Plotly, Matplotlib, Seaborn
*   **Testing:** Playwright (for UI testing)

## Building and Running

### 1. Installation

First, install the required dependencies from `requirements.txt`:

```bash
pip install -r requirements.txt
```

### 2. Running the Web App (Recommended)

To launch the interactive web interface, run:

```bash
streamlit run app.py
```

This will start a local web server, and you can access the application in your browser at `http://localhost:8501`.

### 3. Running from the Command-Line

The CLI can be used for automated backtesting. Here's the basic usage:

```bash
python main.py -f <data_file.csv> -s <start_date> -e <end_date> --strategy <StrategyName>
```

For a full list of options, run:

```bash
python main.py --help
```

## Development Conventions

### Adding a New Strategy

To add a new trading strategy:

1.  Create a new Python file in the `strategies/` directory (e.g., `my_strategy.py`).
2.  Define a new class that inherits from `backtester.strategy_base.StrategyBase`.
3.  Implement the `generate_signals` and `should_exit` methods in your new class.
4.  Register your new strategy in `webapp/strategies_registry.py` by adding it to the `STRATEGY_MAP` dictionary.

### Code Style

The project follows standard Python coding conventions (PEP 8).

### Testing

The project includes some tests. The file `jules-scratch/verification/verify_advanced_chart.py` contains a Playwright test for the advanced chart feature in the web UI.

## Project Structure

```
trading-backtester-v1/
│
├── app.py                       # Entry point for the Streamlit web app
├── main.py                      # Entry point for the CLI
│
├── backtester/                  # Core backtesting engine and utilities
│   ├── engine.py                # The core backtesting engine
│   ├── strategy_base.py         # Base class for all strategies
│   ├── metrics.py               # Performance metrics calculations
│   ├── plotting.py              # Plotting and visualization functions
│   └── ...
│
├── strategies/                  # Directory for trading strategy implementations
│   ├── ema10_scalper.py         # Example: EMA10 scalper strategy
│   └── ...
│
├── webapp/                      # Code specific to the Streamlit web app
│   ├── strategies_registry.py   # Registration of available strategies
│   └── ...
│
├── data/                        # Directory for historical data (CSV files)
├── results/                     # Directory for output files (trade logs, reports)
│
├── requirements.txt             # Project dependencies
├── README.md                    # Project documentation
└── GEMINI.md                    # This file
```
