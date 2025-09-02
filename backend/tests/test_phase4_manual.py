#!/usr/bin/env python3
"""
Manual test for Phase 4 - Analytics & Optimization API endpoints
"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def test_phase4_analytics_api():
    """Test all Phase 4 endpoints"""
    
    base_url = "http://localhost:8000"
    
    # First, create a mock backtest so we have data to analyze
    print("🧪 Creating mock backtest for analytics...")
    
    # Create sample data
    dates = pd.date_range(start='2024-01-01', end='2024-01-10', freq='h')
    equity_data = []
    initial_equity = 100000
    
    # Generate cumulative returns
    returns = np.random.normal(0, 100, len(dates))
    equity_values = initial_equity + np.cumsum(returns)
    
    for i, (date, equity) in enumerate(zip(dates, equity_values)):
        equity_data.append({
            'timestamp': date.isoformat(),
            'equity': float(equity)
        })
    
    # Create sample trades
    trades_data = []
    for i in range(10):
        entry_time = dates[i * 10] if i * 10 < len(dates) else dates[-1]
        pnl = np.random.normal(100, 200)
        trades_data.append({
            'entry_time': entry_time.isoformat(),
            'exit_time': (entry_time + timedelta(hours=2)).isoformat(),
            'pnl': float(pnl),
            'direction': 'long' if np.random.random() > 0.5 else 'short',
            'entry_price': 50000 + np.random.normal(0, 100),
            'exit_price': 50000 + np.random.normal(0, 100)
        })
    
    # Sample metrics
    metrics = {
        'total_return_pct': 15.5,
        'sharpe_ratio': 1.2,
        'max_drawdown_pct': -8.5,
        'win_rate': 0.6,
        'profit_factor': 1.8,
        'total_trades': 10
    }
    
    # Create backtest result
    backtest_result = {
        'equity_curve': equity_data,
        'trades': trades_data,
        'metrics': metrics
    }
    
    # Submit backtest to create data
    backtest_payload = {
        'strategy': 'strategies.ema10_scalper_1.EMA10ScalperStrategyV1',
        'strategy_params': {},
        'dataset_path': 'data/nifty_2024_1min_22Dec_14Jan.csv',
        'engine_options': {
            'initial_cash': 100000,
            'lots': 1,
            'fee_per_trade': 20
        }
    }
    
    print("📊 Submitting backtest...")
    backtest_response = requests.post(f"{base_url}/api/v1/backtests", json=backtest_payload)
    print(f"Backtest submission status: {backtest_response.status_code}")
    
    if backtest_response.status_code != 200:
        print(f"❌ Failed to submit backtest: {backtest_response.text}")
        return False
    
    backtest_data = backtest_response.json()
    
    if 'job_id' in backtest_data:
        # Wait for job completion (simplified for test)
        import time
        job_id = backtest_data['job_id']
        print(f"⏳ Waiting for backtest job {job_id} to complete...")
        
        # Poll for completion
        for _ in range(30):  # Wait up to 30 seconds
            status_response = requests.get(f"{base_url}/api/v1/backtests/{job_id}/status")
            if status_response.status_code == 200:
                status_data = status_response.json()
                if status_data.get('status') == 'completed':
                    print("✅ Backtest completed")
                    break
                elif status_data.get('status') == 'failed':
                    print(f"❌ Backtest failed: {status_data.get('error')}")
                    return False
            time.sleep(1)
        
        # Get backtest results
        results_response = requests.get(f"{base_url}/api/v1/backtests/{job_id}/results")
        if results_response.status_code != 200:
            print(f"❌ Failed to get results: {results_response.text}")
            return False
        
        backtest_id = job_id
    else:
        # Direct result - get the backtest ID from the response
        backtest_id = 1  # Assume first backtest
    
    print(f"📈 Testing Analytics API with backtest ID: {backtest_id}")
    
    # Test 1: Performance Summary
    print("\n🔍 Testing Performance Summary...")
    perf_response = requests.get(f"{base_url}/api/v1/analytics/performance?backtest_id={backtest_id}")
    print(f"Performance summary status: {perf_response.status_code}")
    
    if perf_response.status_code == 200:
        perf_data = perf_response.json()
        print("✅ Performance summary retrieved successfully")
        print(f"Basic metrics: {list(perf_data.get('performance', {}).get('basic_metrics', {}).keys())}")
        print(f"Advanced analytics: {list(perf_data.get('performance', {}).get('advanced_analytics', {}).keys())}")
    else:
        print(f"❌ Performance summary failed: {perf_response.text}")
        return False
    
    # Test 2: Charts Generation
    print("\n📊 Testing Charts Generation...")
    charts_response = requests.get(f"{base_url}/api/v1/analytics/charts/{backtest_id}")
    print(f"Charts generation status: {charts_response.status_code}")
    
    if charts_response.status_code == 200:
        charts_data = charts_response.json()
        print("✅ Charts generated successfully")
        print(f"Available charts: {list(charts_data.get('charts', {}).keys())}")
    else:
        print(f"❌ Charts generation failed: {charts_response.text}")
        return False
    
    # Test 3: Specific Chart Types
    print("\n🎨 Testing Specific Chart Types...")
    specific_charts_response = requests.get(f"{base_url}/api/v1/analytics/charts/{backtest_id}?chart_types=equity,drawdown")
    print(f"Specific charts status: {specific_charts_response.status_code}")
    
    if specific_charts_response.status_code == 200:
        specific_charts_data = specific_charts_response.json()
        print("✅ Specific charts generated successfully")
        print(f"Requested charts: {list(specific_charts_data.get('charts', {}).keys())}")
    else:
        print(f"❌ Specific charts failed: {specific_charts_response.text}")
        return False
    
    # Test 4: Strategy Comparison (if we have multiple backtests)
    print("\n🔄 Testing Strategy Comparison...")
    comparison_response = requests.post(f"{base_url}/api/v1/analytics/compare", 
                                        json={'backtest_ids': [backtest_id]})
    print(f"Strategy comparison status: {comparison_response.status_code}")
    
    if comparison_response.status_code == 200:
        comparison_data = comparison_response.json()
        print("✅ Strategy comparison completed successfully")
        print(f"Comparison data length: {len(comparison_data.get('comparison_data', []))}")
    else:
        print(f"❌ Strategy comparison failed: {comparison_response.text}")
        return False
    
    # Test 5: Optimization API
    print("\n⚡ Testing Optimization API...")
    optimization_payload = {
        'strategy': 'strategies.ema10_scalper_1.EMA10ScalperStrategyV1',
        'dataset_path': 'data/nifty_2024_1min_22Dec_14Jan.csv',
        'parameter_ranges': {
            'ema_period': [8, 10, 12],
            'profit_target': [15, 20, 25]
        },
        'optimization_metric': 'sharpe_ratio',
        'engine_options': {
            'initial_cash': 100000,
            'lots': 1,
            'fee_per_trade': 20
        }
    }
    
    optimization_response = requests.post(f"{base_url}/api/v1/optimize", json=optimization_payload)
    print(f"Optimization submission status: {optimization_response.status_code}")
    
    if optimization_response.status_code == 200:
        opt_data = optimization_response.json()
        print("✅ Optimization submitted successfully")
        
        if 'job_id' in opt_data:
            opt_job_id = opt_data['job_id']
            print(f"⏳ Optimization job {opt_job_id} started")
            
            # Wait a bit for optimization to process
            import time
            time.sleep(2)
            
            # Check optimization status
            opt_status_response = requests.get(f"{base_url}/api/v1/backtests/{opt_job_id}/status")
            if opt_status_response.status_code == 200:
                opt_status = opt_status_response.json()
                print(f"📊 Optimization status: {opt_status.get('status')}")
                if opt_status.get('progress'):
                    print(f"Progress: {opt_status.get('progress')}%")
    else:
        print(f"❌ Optimization submission failed: {optimization_response.text}")
        return False
    
    print("\n🎉 All Phase 4 tests completed successfully!")
    return True

if __name__ == "__main__":
    print("🚀 Starting Phase 4 - Analytics & Optimization API Tests")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/health")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server health check failed")
            exit(1)
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Please start the server first:")
        print("   uvicorn backend.app.main:app --host localhost --port 8000")
        exit(1)
    
    success = test_phase4_analytics_api()
    
    if success:
        print("\n🎊 Phase 4 Analytics & Optimization API is working correctly!")
    else:
        print("\n💥 Phase 4 tests failed!")
        exit(1)
