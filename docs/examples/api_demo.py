"""
This file contains examples for every api call.
"""

import datetime
import logging
import os
from time import sleep
from dotenv import load_dotenv
import schwabdev

print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
print("Documentation: https://tylerebowers.github.io/Schwabdev/")

# place your app key and app secret in the .env file
load_dotenv()  # load environment variables from .env file

# set logging level
logging.basicConfig(level=logging.INFO)

# create client
client = schwabdev.Client(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'))

print("\nGet account number and hashes for linked accounts")
linked_accounts = client.account_linked().json()
print(linked_accounts)
account_hash = linked_accounts[0].get('hashValue') # this will get the first linked account
sleep(3)

print("\nGet details for all linked accounts")
print(client.account_details_all().json())
sleep(3)

print("\nGet specific account positions (uses default account, can be changed)")
print(client.account_details(account_hash, fields="positions").json())
sleep(3)

print("\nGet orders for a linked account")
print(client.account_orders(account_hash, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30), datetime.datetime.now(datetime.timezone.utc)).json())
sleep(3)


order = {"orderType": "LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "price": '10.00',
            "orderLegCollection": [
                {"instruction": "BUY",
                "quantity": 1,
                "instrument": {"symbol": "AMD",
                                "assetType": "EQUITY"
                                }
                }
            ]
        }

# Uncomment to enable order placing/details/cancelling demo
""" 
resp = client.place_order(account_hash, order)
print(f"\nPlace an order status: {resp}")
order_id = resp.headers.get('location', '/').split('/')[-1] # get the order ID - if order is immediately filled then the id might not be returned
print(f"Order id: {order_id}")
sleep(3)

print("\nGet specific order details")
print(client.order_details(account_hash, order_id).json())
sleep(3)

print("\nCancel a specific order")
print(client.cancel_order(account_hash, order_id).json())
sleep(3)
"""

print("\nReplace specific order")
#client.replace_order(account_hash, order_id, order)
print("No demo implemented")
sleep(3)


print("\nGet up to 3000 orders for all accounts for the past 30 days")
print(client.account_orders_all(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30),
                                datetime.datetime.now(datetime.timezone.utc)).json())
sleep(3)


print("\nPreview an order")
print(client.preview_order(account_hash, order).json())


print("\nGet all transactions for an account")
print(client.transactions(account_hash, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30), datetime.datetime.now(datetime.timezone.utc), "TRADE").json())
sleep(3)


print("\nGet details for a specific transaction")
#print(client.transaction_details(account_hash, transactionId).json())
print("No demo implemented")
sleep(3)


print("\nGet user preferences for an account")
print(client.preferences().json())
sleep(3)


print("\nGet a list of quotes")
print(client.quotes(["AAPL", "AMD"]).json())
sleep(3)

print("\nGet a single quote")
print(client.quote("INTC").json())
#print(client.quote("SPXW  241111P06000000").json()) # expired contract now, just an example
sleep(3)

print("\nGet an option chain")
print("Demo disabled to prevent flooding terminal.")
# print(client.option_chains("AAPL", contractType="CALL", range="OTM").json())
# Here is another example for SPX, note that if you call with just $SPX
# you will exceed the buffer on Schwab's end
# hence, the additional parameters to limit the size of return.
# print(client.option_chains("$SPX", contractType="CALL", range="ITM").json())
sleep(3)

print("\nGet an option expiration chain")
print(client.option_expiration_chain("AAPL").json())
sleep(3)

print("\nGet price history for a symbol")
print(client.price_history("AAPL", "year").json())
sleep(3)

print("\nGet movers for an index")
print(client.movers("$DJI").json())
sleep(3)

print("\nGet marketHours for a symbol")
print(client.market_hours(["equity", "option"]).json())
# print(client.market_hours("equity,option").json()) # also works
sleep(3)

print("\nGet marketHours for a market")
print(client.market_hour("equity").json())
sleep(3)

print("\nGet instruments for a symbol")
print(client.instruments("AAPL", "fundamental").json())
sleep(3)

print("\nGet instruments for a cusip")
print(client.instrument_cusip("037833100").json())  # 037833100 = AAPL
sleep(3)
