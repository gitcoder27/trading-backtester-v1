import sys
sys.path.append('d:/Programming/trading/trading-backtester-v1')

from backend.app.services.analytics_service import AnalyticsService

def debug_analytics():
    try:
        service = AnalyticsService()
        result = service.get_performance_summary(1)
        print("Analytics result:", result)
    except Exception as e:
        import traceback
        print(f"Error: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")

if __name__ == "__main__":
    debug_analytics()
