import requests
import json

def test_backtest_configuration():
    """Test backtest configuration with proper values matching Streamlit defaults"""
    
    # Test with proper backend parameter mapping
    data = {
        'strategy': '1',                    # AwesomeScalperStrategy
        'dataset': '1',                     # Any available dataset
        'initial_cash': 100000,             # Matches Streamlit default
        'lots': 2,                          # Matches Streamlit default  
        'commission': 0.0001,               # 0.01% as decimal
        'slippage': 0.0001,                 # 0.01% as decimal
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'parameters': {}
    }
    
    try:
        print("🧪 Testing backtest configuration with updated parameters...")
        print(f"📊 Request data: {json.dumps(data, indent=2)}")
        
        response = requests.post('http://localhost:8000/api/v1/jobs/', json=data)
        print(f'📡 Status Code: {response.status_code}')
        print(f'📝 Response: {response.text}')
        
        if response.status_code == 200:
            print("✅ Backtest job submission successful!")
            result = response.json()
            if 'job_id' in result:
                print(f"🎯 Job ID: {result['job_id']}")
        else:
            print("❌ Backtest job submission failed")
            
    except Exception as e:
        print(f'💥 Error: {str(e)}')

def test_parameter_validation():
    """Test various parameter combinations"""
    
    test_cases = [
        {
            'name': 'Standard Values',
            'data': {
                'strategy': '1',
                'dataset': '1',
                'initial_cash': 100000,      # Standard amount
                'lots': 2,                   # 2 lots
                'commission': 0.0001,        # 0.01%
                'slippage': 0.0001          # 0.01%
            }
        },
        {
            'name': 'High Capital',
            'data': {
                'strategy': '1', 
                'dataset': '1',
                'initial_cash': 500000,      # Higher amount
                'lots': 5,                   # More lots
                'commission': 0.0005,        # 0.05%
                'slippage': 0.0005          # 0.05%
            }
        },
        {
            'name': 'Conservative',
            'data': {
                'strategy': '1',
                'dataset': '1', 
                'initial_cash': 50000,       # Lower amount
                'lots': 1,                   # Single lot
                'commission': 0.0001,        # Minimal commission
                'slippage': 0.0001          # Minimal slippage
            }
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🔍 Testing: {test_case['name']}")
        try:
            response = requests.post('http://localhost:8000/api/v1/jobs/', json=test_case['data'])
            if response.status_code == 200:
                print(f"✅ {test_case['name']}: Success")
            else:
                print(f"❌ {test_case['name']}: Failed - {response.status_code}")
                print(f"   Error: {response.text}")
        except Exception as e:
            print(f"💥 {test_case['name']}: Exception - {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing Backtest Configuration Fixes\n")
    test_backtest_configuration()
    print("\n" + "="*50)
    test_parameter_validation()
    print("\n✅ Test completed!")
