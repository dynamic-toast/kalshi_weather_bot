import requests
import pandas as pd
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
import base64

def load_private_key():
    with open("secret.key", "rb") as key_file:
        return serialization.load_pem_private_key(
            key_file.read(),
            password=None,
        )

def rsa_signature(private_key, message: str) -> str:
    signature = private_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.DIGEST_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("utf-8")

def get_orderbook(contract, id, key):

    url = f"https://api.elections.kalshi.com/trade-api/v2/markets/{contract}/orderbook"
    timestamp = str(int(datetime.now().timestamp() * 1000))
    message_to_sign = f"{timestamp}GET/markets/{contract}/orderbook"
    signature = rsa_signature(key, message_to_sign)
    header = {
        "Content-Type": "application/json",
        "KALSHI-ACCESS-KEY": id,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature
    }
    params = {
        "ticker": contract
    }

    res = requests.get(url, headers=header, params=params)
    orderbook = res.json()
    orderbook = orderbook["orderbook"]
    #yes_bids = orderbook["yes"]
    no_bids = orderbook["no"]

    #best_yes_bid_price, best_yes_bid_qty = max(yes_bids, key=lambda x: x[0])
    best_no_bid_price, best_no_bid_qty = max(no_bids, key=lambda x: x[0])

    best_yes_ask_price = 100 - best_no_bid_price
    best_yes_ask_qty = best_no_bid_qty

    if best_yes_ask_price <= 40 and best_yes_ask_qty >= 3:
        return best_yes_ask_price

    if best_yes_ask_price > 40:
        return "HOLD"

def execute_trade(contract, price, id, key):
    import requests
    from datetime import datetime

    url = "https://api.elections.kalshi.com/trade-api/v2/portfolio/orders"
    timestamp = str(int(datetime.now().timestamp() * 1000))
    message_to_sign = f"{timestamp}POST/trade-api/v2/portfolio/orders"
    signature = rsa_signature(key, message_to_sign)

    headers = {
        "Content-Type": "application/json",
        "KALSHI-ACCESS-KEY": id,
        "KALSHI-ACCESS-TIMESTAMP": timestamp,
        "KALSHI-ACCESS-SIGNATURE": signature
    }

    quantity = 1
    payload = {
        "ticker": contract,
        "side": "yes",
        "action": "buy",
        "count": quantity,
        "type": "limit",
        "yes_price": int(price),
        "time_in_force": "GTC",
    }

    res = requests.post(url, headers=headers, json=payload)

    # Debugging info
    print(f"→ Attempting to place order: {payload}")
    print(f"→ Status: {res.status_code}")
    print(f"→ Response: {res.text}")

    if res.status_code == 201:
        print(f"Order Placed [Limit: {price}¢][Quantity: {quantity}]")
    else:
        print("Order failed...")

def get_new_contract_ticker(city_code, high_temp):

    url = f"https://api.elections.kalshi.com/trade-api/v2/markets"
    params = {
        "series_ticker": city_code,
        "status": "open"
    }
    res = requests.get(url, params=params)
    data = res.json()
    markets = data["markets"]
    df = pd.DataFrame(markets)
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%y%b%d").upper()
    df["close_date"] = pd.to_datetime(df["close_time"]).dt.date
    df = df[df["ticker"].str.contains(tomorrow)]

    temp_str = str(high_temp)
    matches = df[df["ticker"].str.contains(temp_str)]
                 
    if matches.empty:
        lower = str(round(high_temp - 0.5, 1))
        upper = str(round(high_temp + 0.5, 1))
        matches = df[
            df["ticker"].str.contains(lower) | df["ticker"].str.contains(upper)
        ]
    match = matches.iloc[0]

    return match["ticker"]

def get_contract_los_angeles():

    #Ping weather api
    grid_id = "LOX"
    grid_x = "148"
    grid_y = "41"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]

    ticker = get_new_contract_ticker(city_code="KXHIGHLAX", high_temp=tomorrow_high)
    return ticker


def get_contract_miami():
    #Ping weather api
    grid_id = "MFL"
    grid_x = "106"
    grid_y = "51"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]

    ticker = get_new_contract_ticker(city_code="KXHIGHMIA", high_temp=tomorrow_high)
    return ticker

def get_contract_austin():
    #Ping weather api
    grid_id = "EWX"
    grid_x = "159"
    grid_y = "88"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]

    ticker = get_new_contract_ticker(city_code="KXHIGHAUS", high_temp=tomorrow_high)
    return ticker

def get_contract_new_york_city():
    #Ping weather api
    grid_id = "OKX"
    grid_x = "34"
    grid_y = "38"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]
    
    ticker = get_new_contract_ticker(city_code="KXHIGHNY", high_temp=tomorrow_high)
    return ticker

def get_contract_chicago():
    #Ping weather api
    grid_id = "LOT"
    grid_x = "66"
    grid_y = "77"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]

    ticker = get_new_contract_ticker(city_code="KXHIGHCHI", high_temp=tomorrow_high)
    return ticker

def get_contract_denver():
    #Ping weather api
    grid_id = "BOU"
    grid_x = "74"
    grid_y = "66"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]

        ticker = get_new_contract_ticker(city_code="KXHIGHDEN", high_temp=tomorrow_high)
    return ticker

def get_contract_philadelphia():
    #Ping weather api
    grid_id = "PHI"
    grid_x = "48"
    grid_y = "72"

    forecast_url = f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}/forecast"
    forecast_data = requests.get(forecast_url).json()

    periods = forecast_data["properties"]["periods"]
    df = pd.DataFrame(periods)
    df["startTime"] = pd.to_datetime(df["startTime"], errors="coerce", utc=True)
    now = datetime.now()
    tomorrow = (now + timedelta(days=1)).date()
    tomorrow_df = df[df["startTime"].dt.date == tomorrow]

    daytime_forecast = tomorrow_df[tomorrow_df["isDaytime"] == True]

    if not daytime_forecast.empty:
        tomorrow_high = daytime_forecast.iloc[0]["temperature"]

    ticker = get_new_contract_ticker(city_code="KXHIGHPHIL", high_temp=tomorrow_high)
    return ticker
