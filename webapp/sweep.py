"""
Parameter sweep logic for Streamlit app.
"""
# This module will contain sweep logic split from app.py

import pandas as pd
import plotly.express as px
from backtester.engine import BacktestEngine
from backtester.metrics import total_return, sharpe_ratio, max_drawdown, win_rate, profit_factor
import streamlit as st

def run_sweep(data, strat_cls, strat_params, option_delta, lots, price_per_unit, sweep_params, max_runs):
    grids = []
    for k, rng in sweep_params.items():
        if rng is None:
            continue
        a,b,c = rng
        grids.append((k, list(range(int(a), int(b)+1, int(c)))) )
    combos = [{}]
    for k, vals in grids:
        combos = [dict(x, **{k:v}) for x in combos for v in vals]
    if len(combos) > max_runs:
        combos = combos[:int(max_runs)]
    rows = []
    prog = st.progress(0.0)
    for i,params_ in enumerate(combos):
        p = dict(strat_params)
        p.update(params_)
        s = strat_cls(params=p)
        engine2 = BacktestEngine(data, s, option_delta=option_delta, lots=lots, option_price_per_unit=price_per_unit)
        r2 = engine2.run()
        eq2 = r2['equity_curve']
        t2 = r2['trade_log']
        rows.append({
            **params_,
            'Total Return %': total_return(eq2)*100,
            'Sharpe': sharpe_ratio(eq2),
            'MaxDD %': max_drawdown(eq2)*100,
            'WinRate %': win_rate(t2)*100,
            'PF': profit_factor(t2),
            'Trades': len(t2),
        })
        prog.progress((i+1)/len(combos))
    resdf = pd.DataFrame(rows)
    st.dataframe(resdf.sort_values(['Total Return %','Sharpe'], ascending=[False, False]), use_container_width=True)
    if len(grids) == 2:
        (k1, v1), (k2, v2) = grids[0], grids[1]
        piv = resdf.pivot(index=k1, columns=k2, values='Total Return %')
        fig_heat = px.imshow(piv, text_auto=True, color_continuous_scale='RdYlGn', origin='lower', title='Sweep Heatmap (Total Return %)')
        st.plotly_chart(fig_heat, use_container_width=True)
