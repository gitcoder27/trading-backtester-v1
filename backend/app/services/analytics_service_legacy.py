"""Legacy analytics service shim.

Historically the analytics service lived in this module and contained more
than a thousand lines of mixed responsibilities.  The modern analytics package
(`backend.app.services.analytics`) now provides the full implementation.  This
module is kept solely for backward compatibility so imports from the legacy
path continue to function without code changes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from backend.app.database.models import get_session_factory


class AnalyticsService:
    """Thin wrapper that forwards operations to the modular analytics service."""

    def __init__(self) -> None:
        # Maintain attribute compatibility with the historical implementation.
        self.SessionLocal = get_session_factory()
        self._modular_service = self._build_modular_service()

    def get_chart_data(
        self,
        backtest_id: int,
        include_trades: bool = True,
        include_indicators: bool = True,
        max_candles: Optional[int] = None,
        start: Optional[str] = None,
        end: Optional[str] = None,
        tz: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Delegate TradingView chart generation to the modular service."""

        return self._modular_service.get_chart_data(
            backtest_id,
            include_trades=include_trades,
            include_indicators=include_indicators,
            max_candles=max_candles,
            start=start,
            end=end,
            tz=tz,
        )

    # ------------------------------------------------------------------
    # Delegation helpers
    # ------------------------------------------------------------------
    def _build_modular_service(self):
        from backend.app.services.analytics.analytics_service import AnalyticsService as ModularAnalyticsService

        return ModularAnalyticsService()

    def __getattr__(self, name: str):
        """Fallback to the modular service for all other attributes."""

        modular = self._modular_service
        if hasattr(modular, name):
            return getattr(modular, name)

        raise AttributeError(f"'AnalyticsService' object has no attribute '{name}'")

    def __dir__(self) -> List[str]:
        """Expose attributes from both the shim and the modular implementation."""

        return sorted(set(super().__dir__()) | set(dir(self._modular_service)))
