#!/usr/bin/env python3
"""Upload a test dataset for backtesting"""

import requests
import io
import pandas as pd
from datetime import datetime, timedelta

def create_sample_data():
    """Create sample OHLCV data"""
    start_date = datetime(2024, 1, 1, 9, 15)
    data = []
    
    price = 1000.0
    for i in range(100):
        timestamp = start_date + timedelta(minutes=i)
        # Simple random walk
        change = (i % 3 - 1) * 2  # -2, 0, 2
        price += change
        
        high = price + abs(change)
        low = price - abs(change) 
        open_price = price - change
        close = price
        volume = 1000 + (i % 50) * 10
        
        data.append({
            'timestamp': timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    return pd.DataFrame(data)

def upload_dataset():
    """Upload dataset to backend"""
    print("🚀 Creating fresh test dataset...")
    
    # Create sample data
    df = create_sample_data()
    
    # Convert to CSV bytes
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_bytes = csv_buffer.getvalue().encode('utf-8')
    
    # Upload to backend
    url = "http://localhost:8000/api/v1/datasets/upload"
    
    files = {
        'file': ('fresh_test_data.csv', io.BytesIO(csv_bytes), 'text/csv')
    }
    
    data = {
        'name': 'Fresh Test Dataset',
        'symbol': 'TEST',
        'exchange': 'TEST_EXCHANGE'
    }
    
    print("📤 Uploading to backend...")
    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Dataset uploaded successfully!")
        print(f"📊 Dataset ID: {result['dataset']['id']}")
        print(f"📁 File path: {result['dataset']['file_path']}")
        print(f"📈 Rows: {result['dataset']['rows_count']}")
        return result['dataset']['id']
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None

if __name__ == "__main__":
    dataset_id = upload_dataset()
    if dataset_id:
        print(f"\n🎯 Use dataset ID: {dataset_id} for backtesting")
