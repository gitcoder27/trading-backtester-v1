import requests
import json
import csv
import time
from datetime import datetime, timedelta
import pytz
import os

# URL of the API you want to call
url = 'https://ticks.dhan.co/getData'

# Headers you want to send with the request
headers = {
    'Auth': 'myAuthCode',  # TODO: Replace with your actual Auth code
    'Authorization': 'myAuthorizeCode',  # TODO: Replace with your actual Authorization code
    'Bid': 'DHN7897',
    'Cid': '9999999999',
    'Content-Type': 'application/json'
}

# Start and end dates (modify as needed)
start_date = datetime(2025, 1, 18, tzinfo=pytz.timezone('Asia/Kolkata'))
end_date = datetime(2025, 4, 13, tzinfo=pytz.timezone('Asia/Kolkata'))

# File location to save the CSV (local 'data' folder)
file_name = f"nifty_2025_1min_{start_date.strftime('%d%b')}_{end_date.strftime('%d%b')}.csv"
file_path = os.path.join(os.path.dirname(__file__), file_name)

# Initialize empty list to store all data
all_data = []

# Fetch data for 5 days at a time
fetch_days = 5
sleep_seconds = 2  # Use a shorter sleep for local, increase if rate-limited

while start_date < end_date:
    print('Fetching data for:', start_date.strftime("%Y-%m-%d %H:%M:%S"))
    end_of_period = min(start_date + timedelta(days=fetch_days), end_date)
    data = {
        'EXCH': 'IDX',
        'SEG': 'I',
        'INST': 'IDX',
        'SEC_ID': 13,  # 25 for bank nifty and 13 for nifty
        'START': int(start_date.timestamp()),
        'END': int(end_of_period.timestamp()),
        'INTERVAL': '1'
    }
    data_json = json.dumps(data)
    try:
        response = requests.post(url, data=data_json, headers=headers)
        if response.status_code != 200:
            print(f"Error: Received status code {response.status_code}")
            print("Response text:", response.text)
            break
        response = response.json()
        if response and 'data' in response and all(
            key in response['data'] for key in ['Time', 'o', 'h', 'l', 'c', 'v', 't', 'oi']
        ):
            zipped = zip(
                response['data']['Time'],
                response['data']['o'],
                response['data']['h'],
                response['data']['l'],
                response['data']['c'],
                response['data']['v'],
                response['data']['t'],
                response['data']['oi']
            )
            all_data.extend(zipped)
        else:
            print("Incomplete or missing data in response. Skipping this iteration.")
    except json.JSONDecodeError as e:
        print("JSON decoding failed:", str(e))
        print("Raw response text:", response.text)
        break
    except Exception as e:
        print("An error occurred:", str(e))
        break
    print('Fetched data till:', end_of_period.strftime("%Y-%m-%d %H:%M:%S"))
    time.sleep(sleep_seconds)
    start_date = end_of_period

# Write all_data to CSV file (only if data was fetched)
if all_data:
    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['timestamp', 'open', 'high', 'low', 'close', 'volume', 't', 'oi'])
        writer.writerows(all_data)
    print(f"Data saved to {file_path}")
else:
    print("No data fetched. CSV not written.")
