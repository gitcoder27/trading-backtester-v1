#!/usr/bin/env python3
"""
Quick script to check the database for backtest records
"""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.app.database.models import get_session_factory, Backtest, BacktestJob

def check_database():
    SessionLocal = get_session_factory()
    db = SessionLocal()
    
    try:
        # Check backtest records
        backtests = db.query(Backtest).all()
        print(f"Total backtest records: {len(backtests)}")
        
        for bt in backtests:
            print(f"  - Backtest ID: {bt.id}, Strategy: {bt.strategy_name}, Status: {bt.status}")
        
        # Check job records
        jobs = db.query(BacktestJob).all()
        print(f"\nTotal job records: {len(jobs)}")
        
        for job in jobs[-5:]:  # Show last 5 jobs
            print(f"  - Job ID: {job.id}, Status: {job.status}, Strategy: {job.strategy}")
    
    except Exception as e:
        print(f"Error checking database: {e}")
    
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
