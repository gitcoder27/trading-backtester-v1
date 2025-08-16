from backtester.performance_monitor import PerformanceMonitor, get_memory_usage
import time


def test_performance_monitor_basic():
    pm = PerformanceMonitor()
    pm.start_monitoring()
    time.sleep(0.01)
    metrics = pm.stop_monitoring(data_rows=100)
    assert metrics['data_rows'] == 100
    assert metrics['total_time'] >= 0
    assert 'rows_per_second' in metrics


def test_get_memory_usage():
    mem = get_memory_usage()
    assert mem > 0
