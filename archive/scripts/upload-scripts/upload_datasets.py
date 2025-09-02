#!/usr/bin/env python3
"""
Script to upload NIFTY datasets from the data folder to the backend
"""
import os
import requests
import pandas as pd
from pathlib import Path

# Backend API endpoint
BACKEND_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/v1/datasets/upload"

# Data folder path
DATA_FOLDER = Path("d:/Programming/trading/trading-backtester-v1/data")

def upload_dataset(file_path: Path):
    """Upload a single dataset file to the backend"""
    print(f"Uploading {file_path.name}...")
    
    # Read the CSV to get metadata
    try:
        df = pd.read_csv(file_path)
        
        # Extract metadata from filename and data
        filename = file_path.name
        
        # Parse filename to extract symbol and date range
        if "nifty" in filename.lower():
            symbol = "NIFTY"
            timeframe = "1min"  # Based on the data we saw
        else:
            symbol = "UNKNOWN"
            timeframe = "1min"
        
        # Get date range from data
        if 'timestamp' in df.columns:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            start_date = df['timestamp'].min().strftime('%Y-%m-%d')
            end_date = df['timestamp'].max().strftime('%Y-%m-%d')
        else:
            start_date = "2025-01-01"
            end_date = "2025-12-31"
        
        # Prepare form data
        files = {
            'file': (filename, open(file_path, 'rb'), 'text/csv')
        }
        
        data = {
            'name': filename.replace('.csv', ''),
            'symbol': symbol,
            'timeframe': timeframe,
            'description': f'NIFTY market data from {start_date} to {end_date}'
        }
        
        # Upload to backend
        response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully uploaded {filename}")
            print(f"   Dataset ID: {result.get('dataset', {}).get('id', 'Unknown')}")
        else:
            print(f"❌ Failed to upload {filename}: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")
    finally:
        # Close file if it was opened
        try:
            files['file'][1].close()
        except:
            pass

def main():
    print("🚀 Starting NIFTY dataset upload process...")
    print(f"Data folder: {DATA_FOLDER}")
    print(f"Backend URL: {BACKEND_URL}")
    print("-" * 50)
    
    # Find all CSV files in the data folder
    csv_files = list(DATA_FOLDER.glob("*.csv"))
    
    if not csv_files:
        print("❌ No CSV files found in the data folder")
        return
    
    print(f"Found {len(csv_files)} CSV files:")
    for file in csv_files:
        print(f"  - {file.name}")
    
    print("-" * 50)
    
    # Upload each file
    for file_path in csv_files:
        upload_dataset(file_path)
        print()
    
    print("✅ Upload process completed!")
    print("\nYou can now check the datasets in the frontend:")
    print("http://localhost:5173/datasets")

if __name__ == "__main__":
    main()
