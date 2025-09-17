"""Helpers for building the analytics performance summary payload."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Iterable, Optional, Set

import pandas as pd
from sqlalchemy.orm import Session

from backtester.metrics import daily_profit_target_stats


class PerformanceSummaryService:
    """Encapsulates the logic behind ``AnalyticsService.get_performance_summary``."""

    _ALLOWED_SECTIONS: Set[str] = {
        'basic_metrics',
        'advanced_analytics',
        'risk_metrics',
        'trade_analysis',
        'daily_target_stats',
        'drawdown_analysis',
    }

    def __init__(self, performance_calc, trade_analyzer, risk_calc, formatter) -> None:
        self._performance_calc = performance_calc
        self._trade_analyzer = trade_analyzer
        self._risk_calc = risk_calc
        self._formatter = formatter

    def build(
        self,
        db: Session,
        backtest,
        *,
        sections: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Return sanitized summary payload (mutating cached fields when needed)."""

        results: Dict[str, Any] = backtest.results

        equity_curve = pd.DataFrame(results.get('equity_curve', []))
        trades_list = results.get('trades') or results.get('trade_log') or []
        trades = pd.DataFrame(trades_list)
        metrics = results.get('metrics', {})
        engine_config = results.get('engine_config', {})

        requested_sections: Optional[Set[str]]
        if sections is None:
            requested_sections = None
        else:
            requested_sections = {s for s in sections if s in self._ALLOWED_SECTIONS}

        cached_summary = results.get('analytics_summary') if isinstance(results, dict) else None

        performance_payload: Dict[str, Any] = {}

        def need(section: str) -> bool:
            return requested_sections is None or section in requested_sections

        if need('basic_metrics'):
            performance_payload['basic_metrics'] = metrics

        if cached_summary and isinstance(cached_summary, dict):
            for key in self._ALLOWED_SECTIONS - {'basic_metrics'}:
                if need(key) and key in cached_summary:
                    performance_payload[key] = cached_summary[key]

        missing_sections = [
            section for section in (requested_sections or self._ALLOWED_SECTIONS)
            if section not in performance_payload and section in self._ALLOWED_SECTIONS
        ]

        if 'daily_target_stats' in missing_sections:
            try:
                daily_target = float(engine_config.get('daily_target', 30.0))
            except Exception:
                daily_target = 30.0
            performance_payload['daily_target_stats'] = daily_profit_target_stats(trades, daily_target)

        if 'drawdown_analysis' in missing_sections:
            performance_payload['drawdown_analysis'] = self._risk_calc.compute_drawdown_analysis(equity_curve)

        if 'advanced_analytics' in missing_sections:
            performance_payload['advanced_analytics'] = self._performance_calc.compute_basic_analytics(
                equity_curve,
                trades,
            )

        if 'risk_metrics' in missing_sections:
            performance_payload['risk_metrics'] = self._risk_calc.compute_risk_metrics(equity_curve)

        if 'trade_analysis' in missing_sections:
            performance_payload['trade_analysis'] = self._trade_analyzer.analyze_trades_comprehensive(trades)

        self._update_cache(db, backtest, results, performance_payload)

        response = {
            'success': True,
            'backtest_id': backtest.id,
            'performance': performance_payload,
        }
        return self._formatter.sanitize_json(response)

    def _update_cache(
        self,
        db: Session,
        backtest,
        results: Dict[str, Any],
        performance_payload: Dict[str, Any],
    ) -> None:
        """Persist computed sections to analytics cache if necessary."""

        cached_summary = results.get('analytics_summary') if isinstance(results, dict) else None
        cache_dirty = False

        if not cached_summary or not isinstance(cached_summary, dict):
            results['analytics_summary'] = {}
            cached_summary = results['analytics_summary']
            cache_dirty = True

        for key, value in performance_payload.items():
            if key in self._ALLOWED_SECTIONS and key not in cached_summary:
                cached_summary[key] = value
                cache_dirty = True

        if 'basic_metrics' not in cached_summary and 'basic_metrics' in performance_payload:
            cached_summary['basic_metrics'] = performance_payload['basic_metrics']
            cache_dirty = True

        if not cache_dirty:
            return

        results['analytics_cache'] = {
            'cached_at': datetime.utcnow().isoformat() + 'Z',
            'cache_version': 1,
            'sections': sorted(list(cached_summary.keys())),
            'backtest_completed_at': (
                backtest.completed_at.isoformat() + 'Z' if backtest.completed_at else None
            ),
        }
        backtest.results = results
        db.add(backtest)
        db.commit()
