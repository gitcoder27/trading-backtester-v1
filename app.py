"""
Streamlit Web App for the trading-backtester-v1 project.
Allows selecting data, strategy and parameters, running backtests, viewing plots,
and downloading results/reports—all from the browser.
"""
import os
import io
import tempfile
import pandas as pd
import streamlit as st

from backtester.data_loader import load_csv
from backtester.engine import BacktestEngine
from backtester.metrics import (
    total_return,
    sharpe_ratio,
    max_drawdown,
    win_rate,
    profit_factor,
    largest_winning_trade,
    largest_losing_trade,
    average_holding_time,
    max_consecutive_wins,
    max_consecutive_losses,
)
from backtester.plotting import plot_trades_on_candlestick_plotly, plot_equity_curve
from backtester.html_report import generate_html_report

from strategies.ema10_scalper import EMA10ScalperStrategy
from strategies.ema44_scalper import EMA44ScalperStrategy
from strategies.ema50_scalper import EMA50ScalperStrategy
from strategies.bbands_scalper import BBandsScalperStrategy
from strategies.first_candle_breakout import FirstCandleBreakoutStrategy
from strategies.rsi_cross_strategy import RSICrossStrategy


st.set_page_config(page_title="Strategy Backtester", layout="wide")
st.title("Strategy Backtester")
st.caption("Interactive web app for running and analyzing backtests.")


@st.cache_data(show_spinner=False)
def list_data_files(data_folder: str = "data"):
    if not os.path.isdir(data_folder):
        return []
    return [f for f in os.listdir(data_folder) if f.endswith(".csv")]


@st.cache_data(show_spinner=True)
def load_data_from_source(file_path: str | None, timeframe: str, uploaded_bytes: bytes | None):
    if uploaded_bytes is not None:
        # Save to temp and use load_csv for consistent resampling
        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            tmp.write(uploaded_bytes)
            tmp_path = tmp.name
        try:
            df = load_csv(tmp_path, timeframe=timeframe)
        finally:
            try:
                os.remove(tmp_path)
            except Exception:
                pass
        return df
    elif file_path is not None:
        return load_csv(file_path, timeframe=timeframe)
    else:
        return None


def strategy_selector():
    strategies = {
        "EMA10Scalper": EMA10ScalperStrategy,
        "EMA44Scalper": EMA44ScalperStrategy,
        "EMA50Scalper": EMA50ScalperStrategy,
        "BBandsScalper": BBandsScalperStrategy,
        "FirstCandleBreakout": FirstCandleBreakoutStrategy,
        "RSICross": RSICrossStrategy,
    }
    choice = st.selectbox("Strategy", list(strategies.keys()), index=0)
    return choice, strategies[choice]


with st.sidebar:
    st.header("Configuration")

    # Data selection
    mode = st.radio("Data Source", ["Choose from data/", "Upload CSV"], index=0)
    timeframe = st.selectbox("Timeframe", ["1T", "2T", "5T", "10T"], index=0,
                             help="Pandas resample alias: 1T=1min, etc.")

    selected_file_path = None
    uploaded_bytes = None
    if mode == "Choose from data/":
        files = list_data_files()
        if files:
            file_name = st.selectbox("CSV File", files)
            selected_file_path = os.path.join("data", file_name)
        else:
            st.info("No CSV files found in data/.")
    else:
        up = st.file_uploader("Upload CSV", type=["csv"])
        if up is not None:
            uploaded_bytes = up.read()

    # Date range filtering
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start date", value=None)
    with col2:
        end_date = st.date_input("End date", value=None)

    # Strategy selection + parameters
    st.subheader("Strategy & Params")
    strat_choice, strat_cls = strategy_selector()

    debug = st.checkbox("Enable debug logs", value=False)

    # Strategy-specific parameter widgets
    strat_params = {"debug": debug}
    if strat_choice.startswith("EMA10"):
        ema_period = st.number_input("EMA Period", min_value=5, max_value=100, value=10, step=1)
        pt = st.number_input("Profit Target (pts)", min_value=1, max_value=200, value=20, step=1)
        sl = st.number_input("Stop Loss (pts)", min_value=1, max_value=200, value=15, step=1)
        strat_params.update({"ema_period": ema_period, "profit_target": pt, "stop_loss": sl})
    elif strat_choice.startswith("EMA44"):
        st.caption("EMA44 strategy with fixed params (period=44).")
    elif strat_choice.startswith("EMA50"):
        ema_period = st.number_input("EMA Period", min_value=10, max_value=200, value=50, step=1)
        pt = st.number_input("Profit Target (pts)", min_value=1, max_value=200, value=20, step=1)
        strat_params.update({"ema_period": ema_period, "profit_target_points": pt})
    elif strat_choice.startswith("RSI"):
        rsi_period = st.number_input("RSI Period", min_value=2, max_value=50, value=9, step=1)
        overbought = st.number_input("Overbought", min_value=50, max_value=100, value=80, step=1)
        oversold = st.number_input("Oversold", min_value=0, max_value=50, value=20, step=1)
        strat_params.update({"rsi_period": rsi_period, "overbought": overbought, "oversold": oversold})
    elif strat_choice.startswith("FirstCandle"):
        st.caption("First Candle Breakout uses its internal defaults.")
    elif strat_choice.startswith("BBands"):
        st.caption("Bollinger Bands scalper uses its internal defaults.")

    # Engine params
    st.subheader("Execution & Options")
    option_delta = st.slider("Option Delta", min_value=0.1, max_value=1.0, value=0.5, step=0.05)
    lots = st.number_input("Lots (1 lot=75)", min_value=1, max_value=100, value=2, step=1)
    price_per_unit = st.number_input("Option Price Multiplier", min_value=0.1, max_value=10.0, value=1.0, step=0.1)

    run_btn = st.button("Run Backtest", type="primary", use_container_width=True)


def filter_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """Filter a DataFrame by date range, handling tz-aware/naive safely.
    - If data timestamps are tz-aware and inputs are naive, localize inputs to the same tz.
    - End date is treated as inclusive (end of day) by filtering strictly before next day.
    """
    if 'timestamp' not in df.columns:
        return df
    ts = df['timestamp']
    tz = getattr(ts.dt, 'tz', None)
    # Start date
    if start_date:
        start_dt = pd.to_datetime(start_date)
        if tz is not None and start_dt.tzinfo is None:
            start_dt = start_dt.tz_localize(tz)
        df = df[ts >= start_dt]
        ts = df['timestamp']
    # End date (inclusive end-of-day)
    if end_date:
        end_dt = pd.to_datetime(end_date)
        if tz is not None and end_dt.tzinfo is None:
            end_dt = end_dt.tz_localize(tz)
        end_dt_next = end_dt + pd.Timedelta(days=1)
        df = df[ts < end_dt_next]
    return df


def render_metrics(equity_curve: pd.DataFrame, trade_log: pd.DataFrame):
    start_amount = float(equity_curve['equity'].iloc[0])
    final_amount = float(equity_curve['equity'].iloc[-1])

    kpis = {
        "Start Amount": start_amount,
        "Final Amount": final_amount,
        "Total Return (%)": total_return(equity_curve) * 100,
        "Sharpe Ratio": sharpe_ratio(equity_curve),
        "Max Drawdown (%)": max_drawdown(equity_curve) * 100,
        "Win Rate (%)": win_rate(trade_log) * 100,
        "Total Trades": len(trade_log),
        "Profit Factor": profit_factor(trade_log),
        "Largest Win": largest_winning_trade(trade_log),
        "Largest Loss": largest_losing_trade(trade_log),
        "Avg Holding (min)": average_holding_time(trade_log) if len(trade_log) else 0,
        "Max Consec Wins": max_consecutive_wins(trade_log),
        "Max Consec Losses": max_consecutive_losses(trade_log),
    }

    cols = st.columns(4)
    items = list(kpis.items())
    for i, (k, v) in enumerate(items):
        with cols[i % 4]:
            st.metric(k, f"{v:.2f}" if isinstance(v, float) else str(v))


if run_btn:
    if selected_file_path is None and uploaded_bytes is None:
        st.error("Please choose a CSV from data/ or upload one.")
    else:
        data = load_data_from_source(selected_file_path, timeframe, uploaded_bytes)
        if data is None or data.empty:
            st.error("Failed to load data or data is empty.")
        else:
            data = filter_by_date(data, start_date, end_date)
            # Instantiate strategy
            strategy = strat_cls(params=strat_params)

            engine = BacktestEngine(
                data,
                strategy,
                option_delta=option_delta,
                lots=lots,
                option_price_per_unit=price_per_unit,
            )
            results = engine.run()

            equity_curve = results['equity_curve']
            trade_log = results['trade_log']
            indicators = results['indicators'] if 'indicators' in results else None

            # KPIs
            st.subheader("Performance Metrics")
            render_metrics(equity_curve, trade_log)

            # Plots
            st.subheader("Charts")
            c1, c2 = st.columns([2, 1])
            with c1:
                # Enrich trade log with ids for hover
                tlog = trade_log.reset_index(drop=True).copy()
                tlog['trade_id'] = tlog.index
                indicator_cfg = strategy.indicator_config() if hasattr(strategy, 'indicator_config') else []
                fig_trades = plot_trades_on_candlestick_plotly(
                    data,
                    tlog,
                    indicators=indicators,
                    indicator_cfg=indicator_cfg,
                    title="Trades on Candlestick Chart",
                    show=False,
                )
                st.plotly_chart(fig_trades, use_container_width=True)
            with c2:
                fig_eq = None
                try:
                    # Use the interactive path
                    fig_eq = plot_equity_curve(equity_curve, interactive=True)
                except Exception:
                    pass
                if fig_eq is None:
                    import plotly.graph_objs as go
                    fig_eq = go.Figure()
                    fig_eq.add_scatter(x=equity_curve['timestamp'], y=equity_curve['equity'], mode='lines', name='Equity')
                st.plotly_chart(fig_eq, use_container_width=True)

            # Tables
            st.subheader("Trades")
            st.dataframe(trade_log)

            # Downloads
            st.subheader("Export")
            # Trades CSV
            csv_bytes = trade_log.to_csv(index=False).encode('utf-8')
            st.download_button("Download Trades CSV", data=csv_bytes, file_name=f"{strategy.__class__.__name__}_trades.csv", mime="text/csv")

            # HTML Report (generate on demand)
            if st.button("Generate HTML Report"):
                with st.spinner("Generating report..."):
                    tmpdir = tempfile.mkdtemp()
                    report_path = os.path.join(tmpdir, "report.html")
                    metrics_dict = {
                        'Start Amount': float(equity_curve['equity'].iloc[0]),
                        'Final Amount': float(equity_curve['equity'].iloc[-1]),
                        'Total Return (%)': total_return(equity_curve)*100,
                        'Sharpe Ratio': sharpe_ratio(equity_curve),
                        'Max Drawdown (%)': max_drawdown(equity_curve)*100,
                        'Win Rate (%)': win_rate(trade_log)*100,
                        'Total Trades': len(trade_log),
                        'Profit Factor': profit_factor(trade_log),
                        'Largest Winning Trade': largest_winning_trade(trade_log),
                        'Largest Losing Trade': largest_losing_trade(trade_log),
                        'Average Holding Time (min)': average_holding_time(trade_log),
                        'Max Consecutive Wins': max_consecutive_wins(trade_log),
                        'Max Consecutive Losses': max_consecutive_losses(trade_log),
                        'indicator_cfg': strategy.indicator_config() if hasattr(strategy, 'indicator_config') else [],
                    }
                    generate_html_report(equity_curve, data, trade_log, indicators, metrics_dict, report_path)
                    with open(report_path, 'rb') as f:
                        html_bytes = f.read()
                st.download_button("Download HTML Report", data=html_bytes, file_name="report.html", mime="text/html")
