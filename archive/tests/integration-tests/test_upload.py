import requests

def test_upload():
    try:
        # Test the upload endpoint
        files = {
            'file': ('test.csv', 'timestamp,open,high,low,close,volume\n2025-01-01T09:15:00,100,101,99,100.5,1000', 'text/csv')
        }
        data = {
            'name': 'Test Upload',
            'symbol': 'TEST',
            'timeframe': '1min'
        }
        
        response = requests.post('http://localhost:8000/api/v1/datasets/upload', files=files, data=data)
        print('Status:', response.status_code)
        print('Response:', response.text)
        
    except Exception as e:
        print('Error:', str(e))

if __name__ == "__main__":
    test_upload()
