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
# headers = {
#     # 'Auth': 'myAuthCode',  # TODO: Replace with your actual Auth code
#     # 'Authorization': 'myAuthorizeCode',  # TODO: Replace with your actual Authorization code
#     # 'Bid': 'DHN7897',
#     # 'Cid': '9999999999',
#     'Content-Type': 'application/json'
# }
headers = {
    'accept': '*/*',
    'accept-language': 'en-US,en;q=0.9',
    'access-control-allow-origin': 'true',
    'auth': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiJ9.eyJpc3MiOiJkaGFuIiwiZXhwIjoxNzYwMzQzMTk2LCJjbGllbnRfaWQiOiIxMTAwNjAyNDQ4In0.zfmhiZGK-Q07rjwMpYJ2MJjPQWpJqDl-BUcuG8pRBOLNSz57x_TxazZyhDUmROxKyCtzkF7YCeVMeJzK8rE_pQ',
    'authorization': 'gxWP6ogdO1N7uw0Dh3IEKqgKB3Dxz1EH7pOT4Qek7Os+of4poHtMyVpdCQ2zguDHbZx/ZpcbRf27wXWTqCTjGA==',
    'bid': 'DHN1804',
    'cid': '1231231231',
    'content-type': 'application/json',
    'origin': 'https://tv.dhan.co',
    'priority': 'u=1, i',
    'referer': 'https://tv.dhan.co/',
    'sec-ch-ua': '"Chromium";v="140", "Not=A?Brand";v="24", "Google Chrome";v="140"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-site',
    'src': 'T',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36',
}

# Start and end dates (modify as needed)
# format will be yyyy, mm, dd
start_date = datetime(2025, 1, 1, tzinfo=pytz.timezone('Asia/Kolkata'))
end_date = datetime(2025, 12, 31, tzinfo=pytz.timezone('Asia/Kolkata'))
# end_date = datetime.now(pytz.timezone('Asia/Kolkata')) # fetch todays date

# File location to save the CSV (local 'data' folder)
file_name = f"nifty_2025_1min_{start_date.strftime('%d%b')}_{end_date.strftime('%d%b')}.csv"
file_path = os.path.join(os.path.dirname(__file__), file_name)

# Initialize empty list to store all data
all_data = []

# Fetch data for 5 days at a time
# fetch_days = 5
fetch_days = 365 # max allowed by API
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
        # Check for valid data structure and non-None, non-empty lists
        required_keys = ['Time', 'o', 'h', 'l', 'c', 'v', 't', 'oi']
        if response and 'data' in response:
            data_dict = response['data']
            if all(key in data_dict and isinstance(data_dict[key], list) and data_dict[key] for key in required_keys):
                zipped = zip(
                    data_dict['Time'],
                    data_dict['o'],
                    data_dict['h'],
                    data_dict['l'],
                    data_dict['c'],
                    data_dict['v'],
                    data_dict['t'],
                    data_dict['oi']
                )
                all_data.extend(zipped)
            else:
                print("Incomplete, empty, or missing data in response. Skipping this iteration.")
                print({k: data_dict.get(k) for k in required_keys})
        else:
            print("No 'data' field in response. Skipping this iteration.")
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
    print("No valid data fetched. CSV not written.")
