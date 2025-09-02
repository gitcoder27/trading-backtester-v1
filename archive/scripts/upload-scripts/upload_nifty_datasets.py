#!/usr/bin/env python3
"""
Simple script to upload NIFTY datasets from the data folder to the backend
"""
import os
import requests
from pathlib import Path

# Backend API endpoint
BACKEND_URL = "http://localhost:8000"
UPLOAD_ENDPOINT = f"{BACKEND_URL}/api/v1/datasets/upload"

# Data folder path
DATA_FOLDER = Path("data")

def upload_dataset(file_path: Path):
    """Upload a single dataset file to the backend"""
    print(f"Uploading {file_path.name}...")
    
    try:
        # Extract metadata from filename
        filename = file_path.name
        
        # Parse filename to extract symbol and timeframe
        if "nifty" in filename.lower():
            symbol = "NIFTY"
            timeframe = "1min"
            
            # Extract date range from filename
            if "2025" in filename:
                name = filename.replace('.csv', '') + ' (2025 Data)'
            elif "2024" in filename:
                name = filename.replace('.csv', '') + ' (2024 Data)'
            else:
                name = filename.replace('.csv', '')
        else:
            symbol = "UNKNOWN"
            timeframe = "1min"
            name = filename.replace('.csv', '')
        
        # Prepare form data
        with open(file_path, 'rb') as f:
            files = {
                'file': (filename, f, 'text/csv')
            }
            
            data = {
                'name': name,
                'symbol': symbol,
                'timeframe': timeframe,
                'description': f'NIFTY market data - {filename}'
            }
            
            # Upload to backend
            response = requests.post(UPLOAD_ENDPOINT, files=files, data=data)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Successfully uploaded {filename}")
                if 'dataset' in result:
                    dataset_id = result['dataset'].get('id', 'Unknown')
                    print(f"   Dataset ID: {dataset_id}")
            else:
                print(f"❌ Failed to upload {filename}: {response.status_code}")
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Error processing {filename}: {str(e)}")

def main():
    print("🚀 Starting NIFTY dataset upload process...")
    print(f"Data folder: {DATA_FOLDER.absolute()}")
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
