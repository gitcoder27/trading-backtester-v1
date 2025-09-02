from backend.app.database.models import get_session_factory, Backtest

def check_backtest_data():
    db = get_session_factory()()
    try:
        bt = db.query(Backtest).filter(Backtest.id == 1).first()
        if bt:
            print(f'Backtest 1 found: {bt.strategy_name}, status: {bt.status}')
            print(f'Results available: {bt.results is not None}')
            if bt.results:
                print(f'Results type: {type(bt.results)}')
                if isinstance(bt.results, dict):
                    print(f'Results keys: {list(bt.results.keys())}')
                else:
                    print(f'Results content: {str(bt.results)[:200]}...')
        else:
            print('Backtest 1 not found')
            # Show available backtests
            backtests = db.query(Backtest).limit(5).all()
            print(f'Available backtests: {[(bt.id, bt.strategy_name) for bt in backtests]}')
    finally:
        db.close()

if __name__ == "__main__":
    check_backtest_data()
