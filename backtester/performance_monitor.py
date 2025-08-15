"""
performance_monitor.py
Performance monitoring and profiling utilities for the backtesting system.
"""

import time
import psutil
import pandas as pd
from functools import wraps
from typing import Dict, Any
import streamlit as st

class PerformanceMonitor:
    """Monitor performance metrics during backtesting."""
    
    def __init__(self):
        self.metrics = {}
        self.start_time = None
        self.start_memory = None
    
    def start_monitoring(self):
        """Start performance monitoring."""
        self.start_time = time.time()
        self.start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
    
    def stop_monitoring(self, data_rows: int = 0):
        """Stop monitoring and calculate final metrics."""
        if self.start_time is None:
            return {}
        
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        self.metrics = {
            'total_time': end_time - self.start_time,
            'memory_used': end_memory - self.start_memory,
            'peak_memory': end_memory,
            'data_rows': data_rows,
            'rows_per_second': data_rows / (end_time - self.start_time) if end_time > self.start_time else 0
        }
        
        return self.metrics
    
    def display_metrics(self):
        """Display performance metrics in Streamlit."""
        if not self.metrics:
            return
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Execution Time", f"{self.metrics['total_time']:.2f}s")
        
        with col2:
            st.metric("Memory Used", f"{self.metrics['memory_used']:.1f}MB")
        
        with col3:
            st.metric("Data Rows", f"{self.metrics['data_rows']:,}")
        
        with col4:
            st.metric("Processing Speed", f"{self.metrics['rows_per_second']:,.0f} rows/s")

def performance_timer(func):
    """Decorator to time function execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        # Store timing in session state if available
        if 'performance_times' not in st.session_state:
            st.session_state['performance_times'] = {}
        
        st.session_state['performance_times'][func.__name__] = end_time - start_time
        
        return result
    return wrapper

def get_memory_usage():
    """Get current memory usage in MB."""
    return psutil.Process().memory_info().rss / 1024 / 1024

def optimize_pandas_performance():
    """Set pandas options for better performance."""
    pd.set_option('mode.chained_assignment', None)  # Disable warnings for performance
    pd.set_option('compute.use_bottleneck', True)   # Use bottleneck for faster operations
    pd.set_option('compute.use_numexpr', True)      # Use numexpr for faster operations
