from backend.app.database.models import get_session_factory, Backtest
import json

SessionLocal = get_session_factory()
db = SessionLocal()
backtest = db.query(Backtest).filter(Backtest.id == 4).first()

if backtest and backtest.results:
    print('Available keys in results:')
    for key in backtest.results.keys():
        print(f'- {key}')
    
    if 'price_data' in backtest.results:
        print(f'Price data length: {len(backtest.results["price_data"])}')
        if backtest.results['price_data']:
            print('Sample price data:', backtest.results['price_data'][0])
    
    # Check for other data structures
    for key in ['market_data', 'ohlc_data', 'candles', 'dataset']:
        if key in backtest.results:
            print(f'Found {key}: {type(backtest.results[key])}, length: {len(backtest.results[key])}')

    # Check what dataset info is available
    print(f"\nDataset ID: {backtest.dataset_id}")
    print(f"Strategy name: {backtest.strategy_name}")
            
db.close()
