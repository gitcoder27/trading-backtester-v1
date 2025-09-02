"""
TradingView Lightweight Charts renderer (v5 API) embedded via HTML in Streamlit.

This renderer uses a npm-managed local library approach for optimal version control,
offline capability, and automatic updates.

Library management:
- Version managed via npm (see package.json)
- Auto-updated via `npm run update-charts`
- Latest version automatically downloaded to local storage
- Offline-capable with no external dependencies

Current library: v5.0.8 (standalone production build)
Library location: webapp/static/js/lightweight-charts.standalone.production.js

For library updates: Run `npm run update-charts` from project root.
"""

from __future__ import annotations
import json
import math
import streamlit as st
import streamlit.components.v1 as components
from typing import List, Dict, Any

from .models import ChartData, TradeData, ChartOptions, PerformanceSettings, RenderingError


class TVLwRenderer:
    """Render charts using TradingView Lightweight Charts (via local files + HTML)."""

    # Path to the local chart library file
    LOCAL_CHART_LIB = "webapp/static/js/lightweight-charts.standalone.production.js"

    def __init__(self, options: ChartOptions, performance: PerformanceSettings | None = None):
        self.options = options
        self.performance = performance or PerformanceSettings()
        # Load the chart library content
        self._load_chart_library()

    def _load_chart_library(self) -> None:
        """Load the chart library JavaScript content from local file."""
        try:
            with open(self.LOCAL_CHART_LIB, 'r', encoding='utf-8') as f:
                self.chart_lib_content = f.read()
        except FileNotFoundError:
            raise RenderingError(f"Chart library file not found: {self.LOCAL_CHART_LIB}")
        except Exception as e:
            raise RenderingError(f"Failed to load chart library: {e}")

    def render_chart(
        self,
        chart_data: ChartData,
        trade_data: TradeData,
        overlays_enabled: bool = True,
        show_trade_lines_threshold: int = 80,
    ) -> None:
        """Render the chart into Streamlit via st.components HTML.

        Args:
            chart_data: Prepared OHLC + overlays/oscillators
            trade_data: Processed trade visualization data
            overlays_enabled: Whether to render overlays as line series
            show_trade_lines_threshold: Max trades to render as line segments (avoid perf issues)
        """
        try:
            # Ensure the iframe and all containers expand to full width
            st.markdown(
                """
                <style>
                /* Target all possible iframe containers for TV chart */
                iframe[title="streamlit.components.v1.html"] { 
                    width: 100% !important; 
                    min-width: 100% !important;
                }
                
                /* Ensure Streamlit component containers don't constrain width */
                .element-container:has(iframe[title="streamlit.components.v1.html"]) {
                    width: 100% !important;
                    max-width: none !important;
                    padding-left: 0 !important;
                    padding-right: 0 !important;
                }
                
                /* Target the parent container */
                div[data-testid="stVerticalBlock"] > div:has(iframe[title="streamlit.components.v1.html"]) {
                    width: 100% !important;
                    max-width: none !important;
                }
                </style>
                """,
                unsafe_allow_html=True,
            )

            candles_js = self._candles_to_js(chart_data.candles)
            overlay_series_js = self._overlays_to_js(chart_data.overlays) if overlays_enabled else []
            markers_js = self._trades_to_markers_js(trade_data)
            trade_lines_js = self._trade_lines_to_js(trade_data, max_lines=show_trade_lines_threshold)

            bg_color = self.options.background_color or "#0e1117"
            text_color = self.options.text_color or "#d1d5db"
            up_color = self.options.up_color or "#26a69a"
            down_color = self.options.down_color or "#ef5350"

            height_px = self._parse_height_px(self.options.height)

            html = self._build_html(
                candles_js=candles_js,
                overlay_series_js=overlay_series_js,
                markers_js=markers_js,
                trade_lines_js=trade_lines_js,
                bg_color=bg_color,
                text_color=text_color,
                up_color=up_color,
                down_color=down_color,
                height_px=height_px,
            )

            # Render with full width and proper height
            components.html(html, width=None, height=height_px + 40, scrolling=False)

        except Exception as e:
            raise RenderingError(f"TV Lightweight chart rendering failed: {e}")

    def _parse_height_px(self, height: str | int) -> int:
        if isinstance(height, int):
            return height
        try:
            if isinstance(height, str) and height.endswith("px"):
                return int(height[:-2])
            return int(height)
        except Exception:
            return 600

    def _candles_to_js(self, candles: List[Dict[str, Any]]) -> str:
        data = [
            {
                "time": int(c["time"]),
                "open": float(c["open"]),
                "high": float(c["high"]),
                "low": float(c["low"]),
                "close": float(c["close"]),
            }
            for c in candles
        ]
        return json.dumps(data)

    def _overlays_to_js(self, overlays: List[Dict[str, Any]]) -> str:
        series_list = []
        for ov in overlays or []:
            color = (ov.get("options", {}) or {}).get("color", "#cccccc")
            name = ov.get("name", "Overlay")
            data = ov.get("data", [])
            js_data = [
                {"time": int(p["time"]), "value": float(p["value"])}
                for p in data
                if p is not None and "time" in p and "value" in p
            ]
            series_list.append({
                "name": name,
                "color": color,
                "data": js_data,
            })
        return json.dumps(series_list)

    def _trades_to_markers_js(self, trade_data: TradeData) -> str:
        markers = []
        # Entries
        for tp in trade_data.entries or []:
            v = tp.get("value", None)
            if not v or len(v) < 2:
                continue
            t_ms, price = v[0], v[1]
            markers.append({
                "time": int(math.floor(int(t_ms) / 1000)),
                "position": "belowBar",
                "color": "#22c55e",
                "shape": "arrowUp",
                "text": "Entry",
            })
        # Exits
        for tp in trade_data.exits or []:
            v = tp.get("value", None)
            if not v or len(v) < 2:
                continue
            t_ms, price = v[0], v[1]
            markers.append({
                "time": int(math.floor(int(t_ms) / 1000)),
                "position": "aboveBar",
                "color": "#f59e0b",
                "shape": "arrowDown",
                "text": "Exit",
            })
        return json.dumps(markers)

    def _trade_lines_to_js(self, trade_data: TradeData, max_lines: int = 80) -> str:
        # Create an array of series specs, each with 2 points [entry, exit]
        lines = []
        # We can approximate by pairing entries and exits by index
        num_pairs = min(len(trade_data.entries or []), len(trade_data.exits or []), max_lines)
        for i in range(num_pairs):
            e = trade_data.entries[i]["value"]
            x = trade_data.exits[i]["value"]
            series = {
                "color": "#34d399",  # default win color; actual PnL not available here
                "data": [
                    {"time": int(e[0] // 1000), "value": float(e[1])},
                    {"time": int(x[0] // 1000), "value": float(x[1])},
                ],
            }
            lines.append(series)
        return json.dumps(lines)

    def _build_html(
        self,
        candles_js: str,
        overlay_series_js: str,
        markers_js: str,
        trade_lines_js: str,
        bg_color: str,
        text_color: str,
        up_color: str,
        down_color: str,
        height_px: int,
    ) -> str:
        # Note: Using v5 API style with IIFE build variant
        return f"""
<!DOCTYPE html>
<html>
  <head>
    <meta charset=\"UTF-8\" />
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
    <script>
{self.chart_lib_content}
    </script>
    <style>
      html, body {{ 
        margin: 0; 
        padding: 0; 
        background: {bg_color}; 
        width: 100% !important; 
        max-width: none !important;
        box-sizing: border-box;
      }}
      #tv-wrapper {{ 
        width: 100% !important; 
        max-width: none !important;
        box-sizing: border-box;
      }}
      #tv-container {{ 
        width: 100% !important; 
        height: {height_px}px !important; 
        max-width: none !important;
        box-sizing: border-box;
      }}
      .tv-attrib {{ 
        color: {text_color}; 
        font: 12px/1.4 sans-serif; 
        opacity: 0.7; 
        margin-top: 4px; 
        text-align: center;
      }}
    </style>
  </head>
  <body>
    <div id=\"tv-wrapper\"><div id=\"tv-container\"></div></div>
    <div class=\"tv-attrib\">Charting by <a href=\"https://www.tradingview.com/\" target=\"_blank\" style=\"color:{text_color}\">TradingView</a></div>
    <script>
      (function() {{
        const {{ createChart, CandlestickSeries, LineSeries }} = window.LightweightCharts;
        const container = document.getElementById('tv-container');

        const chart = createChart(container, {{
          layout: {{
            background: {{ type: 'solid', color: '{bg_color}' }},
            textColor: '{text_color}',
          }},
          grid: {{
            vertLines: {{ color: '#1f2937' }},
            horzLines: {{ color: '#1f2937' }},
          }},
          rightPriceScale: {{ borderColor: '#374151' }},
          timeScale: {{ borderColor: '#374151' }},
        }});

        const candleSeries = chart.addSeries(CandlestickSeries, {{
          upColor: '{up_color}',
          downColor: '{down_color}',
          borderVisible: false,
          wickUpColor: '{up_color}',
          wickDownColor: '{down_color}',
        }});

        const candles = {candles_js};
        candleSeries.setData(candles);

        // Markers for trades
        const markers = {markers_js};
        if (markers && markers.length) {{
          candleSeries.setMarkers(markers);
        }}

        // Overlay indicator line series
        const overlays = {overlay_series_js};
        if (overlays && overlays.length) {{
          overlays.forEach((ov) => {{
            const s = chart.addSeries(LineSeries, {{
              color: ov.color || '#cccccc',
              lineWidth: 1,
              priceLineVisible: false,
              lastValueVisible: false,
            }});
            s.setData(ov.data || []);
          }});
        }}

        // Optional trade lines (limited count for performance)
        const tradeLines = {trade_lines_js};
        if (tradeLines && tradeLines.length) {{
          tradeLines.forEach((tl) => {{
            const s = chart.addSeries(LineSeries, {{
              color: tl.color || '#34d399',
              lineWidth: 1,
              priceLineVisible: false,
              lastValueVisible: false,
            }});
            s.setData(tl.data || []);
          }});
        }}

        const resizeToContainer = () => {{
          const rect = container.getBoundingClientRect();
          const w = Math.max(0, Math.floor(rect.width));
          const h = Math.max(0, Math.floor(rect.height));
          chart.resize(w, h);
          chart.timeScale().fitContent();
        }};

        // Initial sizing and subsequent adjustments
        resizeToContainer();
        const ro = new ResizeObserver(resizeToContainer);
        ro.observe(container);
        window.addEventListener('load', resizeToContainer);
        setTimeout(resizeToContainer, 50);
        setTimeout(resizeToContainer, 200);

      }})();
    </script>
  </body>
</html>
"""


