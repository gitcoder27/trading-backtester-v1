from backend.app.database.models import get_session_factory, Backtest
import pandas as pd

def check_equity_curve_structure():
    db = get_session_factory()()
    try:
        bt = db.query(Backtest).filter(Backtest.id == 1).first()
        if bt and bt.results:
            results = bt.results
            print("Results structure:")
            for key, value in results.items():
                print(f"  {key}: {type(value)}")
                if isinstance(value, list) and value:
                    print(f"    Sample item: {value[0] if value else 'Empty'}")
                    if isinstance(value[0], dict):
                        print(f"    Keys: {list(value[0].keys())}")
            
            # Check equity curve specifically
            equity_curve = results.get('equity_curve', [])
            print(f"\nEquity curve: {len(equity_curve)} items")
            if equity_curve:
                print(f"First item: {equity_curve[0]}")
                df = pd.DataFrame(equity_curve)
                print(f"DataFrame columns: {list(df.columns)}")
                print(f"DataFrame shape: {df.shape}")
                print(f"Sample data:\n{df.head()}")
                
    finally:
        db.close()

if __name__ == "__main__":
    check_equity_curve_structure()
