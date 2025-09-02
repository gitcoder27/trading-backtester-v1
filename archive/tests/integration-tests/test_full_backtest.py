#!/usr/bin/env python3
"""Final comprehensive test of backtesting functionality"""

import requests
import json
import time

def test_full_backtest_workflow():
    """Test the complete backtest workflow end-to-end"""
    print("🚀 Testing Complete Backtest Workflow")
    
    # 1. Get latest dataset
    print("📊 Getting latest dataset...")
    response = requests.get("http://localhost:8000/api/v1/datasets/")
    if response.status_code != 200:
        print(f"❌ Failed to get datasets: {response.status_code}")
        return
    
    datasets = response.json()['datasets']
    if not datasets:
        print("❌ No datasets found")
        return
    
    # Use the latest dataset
    latest_dataset = datasets[0]
    dataset_id = latest_dataset['id']
    
    print(f"✅ Using dataset ID: {dataset_id}")
    print(f"📁 Dataset name: {latest_dataset['name']}")
    print(f"📂 File path: {latest_dataset['file_path']}")
    print(f"📈 Rows: {latest_dataset['rows_count']}")
    
    # 2. Submit backtest job
    print("\n🎯 Submitting backtest job...")
    
    backtest_request = {
        "strategy": "1",  # AwesomeScalperStrategy
        "dataset": str(dataset_id),  # Use latest dataset
        "strategy_params": {},
        "engine_options": {
            "initial_cash": 100000,
            "lots": 2,
            "commission": 0.0001,
            "slippage": 0.0001
        }
    }
    
    print(f"📋 Request: {json.dumps(backtest_request, indent=2)}")
    
    response = requests.post("http://localhost:8000/api/v1/jobs/", json=backtest_request)
    
    if response.status_code != 200:
        print(f"❌ Failed to submit job: {response.status_code} - {response.text}")
        return
    
    result = response.json()
    job_id = result['job_id']
    
    print(f"✅ Job submitted successfully!")
    print(f"🆔 Job ID: {job_id}")
    
    # 3. Monitor job progress
    print("\n⏳ Monitoring job progress...")
    
    for i in range(30):  # Wait up to 30 seconds
        time.sleep(1)
        
        response = requests.get(f"http://localhost:8000/api/v1/jobs/{job_id}")
        if response.status_code != 200:
            print(f"❌ Failed to get job status: {response.status_code}")
            continue
        
        job = response.json()
        status = job['status']
        progress = job.get('progress', 0)
        
        print(f"📊 Status: {status}, Progress: {progress:.1%}")
        
        if status == 'completed':
            print("🎉 Job completed successfully!")
            
            # 4. Check if backtest was created
            print("\n🔍 Checking backtest results...")
            
            response = requests.get("http://localhost:8000/api/v1/backtests/")
            if response.status_code == 200:
                backtests = response.json()['backtests']
                if backtests:
                    latest_backtest = backtests[0]
                    print(f"✅ Backtest created!")
                    print(f"🆔 Backtest ID: {latest_backtest['id']}")
                    print(f"📈 Total Return: {latest_backtest.get('total_return', 'N/A')}")
                    print(f"📊 Total Trades: {latest_backtest.get('total_trades', 'N/A')}")
                    return True
                else:
                    print("❌ No backtests found")
                    return False
            break
        elif status == 'failed':
            print(f"❌ Job failed: {job.get('error_message', 'Unknown error')}")
            return False
    
    print("⏰ Job monitoring timed out")
    return False

if __name__ == "__main__":
    success = test_full_backtest_workflow()
    if success:
        print("\n🎉 BACKTEST WORKFLOW TEST PASSED! 🎉")
        print("✅ The core backtesting functionality is now working!")
    else:
        print("\n❌ BACKTEST WORKFLOW TEST FAILED")
        print("🔧 Additional debugging may be needed")
