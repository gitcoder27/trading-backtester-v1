import sys
import traceback
from backend.app.services.analytics_service import AnalyticsService

def test_analytics_service():
    try:
        service = AnalyticsService()
        print("Analytics service initialized successfully")
        
        # Test the performance summary method
        result = service.get_performance_summary(1)
        print(f"Performance summary result: {result}")
        
    except Exception as e:
        print(f"Error: {e}")
        print(f"Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_analytics_service()
