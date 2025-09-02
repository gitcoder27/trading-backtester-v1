import requests
import json

def test_job_submission():
    # Test job submission with string strategy and dataset IDs
    data = {
        'strategy': '1',  # String instead of number
        'dataset': '1',   # String instead of number
        'initial_capital': 100000,
        'commission': 0.0001,
        'slippage': 0.0001,
        'start_date': '2024-01-01',
        'end_date': '2024-12-31',
        'parameters': {}
    }
    
    try:
        print("Testing job submission with string parameters...")
        response = requests.post('http://localhost:8000/api/v1/jobs/', json=data)
        print(f'Status Code: {response.status_code}')
        print(f'Response: {response.text}')
        
        if response.status_code == 200:
            print("✅ Job submission successful!")
        else:
            print("❌ Job submission failed")
            
    except Exception as e:
        print(f'Error: {str(e)}')

if __name__ == "__main__":
    test_job_submission()
