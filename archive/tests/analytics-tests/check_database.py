"""
Check the database content to see if backtests are stored
"""
import sqlite3
import json

# Connect to the database
db_path = 'backend/database/backtester.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=== BACKTESTS TABLE ===")
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Available tables:", tables)

# Check if backtests table exists and get its structure
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='backtests';")
schema = cursor.fetchone()
if schema:
    print("\nBacktests table schema:")
    print(schema[0])
else:
    print("No backtests table found")

# Check for any backtest data
try:
    cursor.execute("SELECT id, strategy_name, status, created_at FROM backtests LIMIT 10;")
    backtests = cursor.fetchall()
    print(f"\nFound {len(backtests)} backtests:")
    for bt in backtests:
        print(f"  ID: {bt[0]}, Strategy: {bt[1]}, Status: {bt[2]}, Created: {bt[3]}")
except Exception as e:
    print(f"Error querying backtests: {e}")

print("\n=== JOBS TABLE ===")
try:
    cursor.execute("SELECT id, status, strategy, created_at FROM jobs ORDER BY created_at DESC LIMIT 5;")
    jobs = cursor.fetchall()
    print(f"Found {len(jobs)} recent jobs:")
    for job in jobs:
        print(f"  ID: {job[0]}, Status: {job[1]}, Strategy: {job[2]}, Created: {job[3]}")
except Exception as e:
    print(f"Error querying jobs: {e}")

conn.close()
