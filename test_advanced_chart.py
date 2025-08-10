#!/usr/bin/env python3
"""
Quick test to verify the advanced chart component key generation logic.
This doesn't require running the full app.
"""

import pandas as pd
import hashlib

# Mock data to test the key generation logic
sample_data = pd.DataFrame({
    'timestamp': pd.date_range('2024-01-01', periods=100, freq='1T'),
    'open': [100 + i for i in range(100)],
    'high': [101 + i for i in range(100)],
    'low': [99 + i for i in range(100)],
    'close': [100.5 + i for i in range(100)],
})

sample_trades = pd.DataFrame({
    'entry_time': pd.date_range('2024-01-01 09:30', periods=5, freq='30T'),
    'exit_time': pd.date_range('2024-01-01 10:00', periods=5, freq='30T'),
    'entry_price': [100, 105, 110, 115, 120],
    'exit_price': [102, 107, 108, 118, 125],
    'pnl': [2, 2, -2, 3, 5],
    'direction': ['long', 'long', 'long', 'long', 'long']
})

def test_key_generation():
    # Simulate the key generation logic
    
    # Mock dataset (this would normally be generated from price data)
    dataset = [[i*1000, 100+i, 101+i, 99+i, 100.5+i] for i in range(100)]
    
    # Mock entries/exits (this would normally be generated from trades)
    entries = [{'value': [i*1000, 100+i]} for i in range(5)]
    exits = [{'value': [i*1000, 102+i]} for i in range(5)]
    
    # Mock session state values
    run_uid = 12345
    force_update = 1
    
    # Generate hashes (same logic as in advanced_chart.py)
    data_hash = hashlib.md5(str(dataset).encode()).hexdigest()[:8]
    trades_hash = hashlib.md5(str(len(entries + exits)).encode()).hexdigest()[:8]
    
    # Generate component key
    comp_key = f"adv_echart_{run_uid}_{force_update}_{data_hash}_{trades_hash}"
    
    print("Test Key Generation:")
    print(f"Run UID: {run_uid}")
    print(f"Force Update: {force_update}")
    print(f"Data Hash: {data_hash}")
    print(f"Trades Hash: {trades_hash}")
    print(f"Component Key: {comp_key}")
    
    # Test with different data to see if key changes
    dataset_2 = [[i*1000, 101+i, 102+i, 100+i, 101.5+i] for i in range(100)]
    data_hash_2 = hashlib.md5(str(dataset_2).encode()).hexdigest()[:8]
    comp_key_2 = f"adv_echart_{run_uid}_{force_update}_{data_hash_2}_{trades_hash}"
    
    print(f"\nWith different data:")
    print(f"Data Hash 2: {data_hash_2}")
    print(f"Component Key 2: {comp_key_2}")
    print(f"Keys are different: {comp_key != comp_key_2}")
    
    return comp_key != comp_key_2

if __name__ == "__main__":
    success = test_key_generation()
    print(f"\nKey generation test: {'PASSED' if success else 'FAILED'}")
