import time
from datetime import datetime
import cities

activate = str(input("\n Activate algorithm? [y/n]: ")).lower()
if activate=="y":

    ID = "PASTE_KALSHI_ID_HERE"
    KEY = cities.load_private_key()
    HIGHEST_CONTRACT_PRICE = 40

    # Resets scans on rerun
    scans = {
        "la": None,
        "mia": None,
        "aust": None,
        "nyc": None,
        "chi": None,
        "den": None,
        "phil": None
    }

    while True:
        CONTRACT_OPEN_TIME = "14:00"
        now = datetime.now().strftime("%H:%M")

        # New contracts open
        if now == CONTRACT_OPEN_TIME:
            print(f"[{now}] Refreshing contracts...")

            # Fetch new contracts
            city_contracts = {
                "la": cities.get_contract_los_angeles(),
                "mia": cities.get_contract_miami(),
                "aust": cities.get_contract_austin(),
                "nyc": cities.get_contract_new_york_city(),
                "chi": cities.get_contract_chicago(),
                "den": cities.get_contract_denver(),
                "phil": cities.get_contract_philadelphia()
            }

            # Evaluate signals for each city
            for key, contract in city_contracts.items():
                signal = cities.get_orderbook(contract, ID, KEY)

                if signal == "HOLD":
                    print(f"Contract: {contract} OVERVALUED")
                    scans[key] = "OVERVALUED"
                else:
                    signal = int(signal)
                    if signal <= HIGHEST_CONTRACT_PRICE:
                        print(f"Contract: {contract} EXECUTING TRADE")
                        cities.execute_trade(contract=contract, price=signal, id=ID, key=KEY)
                        scans[key] = None

            # Wait 1 minute after refreshing contracts
            time.sleep(60)

        #Loop scans contracts until order filled
        if 'city_contracts' in locals():
            for key, contract in city_contracts.items():
                if scans[key] == "OVERVALUED" and contract is not None:
                    signal = cities.get_orderbook(contract, ID, KEY)

                    if signal == "HOLD":
                        print(f"Contract: {contract} OVERVALUED")
                        scans[key] = "OVERVALUED"
                    else:
                        signal = int(signal)
                        if signal <= HIGHEST_CONTRACT_PRICE:
                            print(f"Contract: {contract} EXECUTING TRADE")
                            cities.execute_trade(contract=contract, price=signal, id=ID, key=KEY)
                            scans[key] = None

        #Refresh every 10 seconds
        print(f"Refresh: {now}")
        time.sleep(10)
