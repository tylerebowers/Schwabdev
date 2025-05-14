"""
This file contains examples for every api call.
"""

import datetime
import logging
import os
from time import sleep

from dotenv import load_dotenv

import schwabdev


def main():
    # place your app key and app secret in the .env file
    load_dotenv()  # load environment variables from .env file

    # warn user if they have not added their keys to the .env
    if len(os.getenv('app_key')) != 32 or len(os.getenv('app_secret')) != 16:
        raise Exception("Add you app key and app secret to the .env file.")

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

    # get orders for a linked account
    print("\nGet orders for a linked account")
    print(client.account_orders(account_hash, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30), datetime.datetime.now(datetime.timezone.utc)).json())
    sleep(3)

    # place an order, get the details, then cancel it (uncomment to test)
    """
    order = {"orderType": "LIMIT",
             "session": "NORMAL",
             "duration": "DAY",
             "orderStrategyType": "SINGLE",
             "price": '10.00',
             "orderLegCollection": [
                 {"instruction": "BUY",
                  "quantity": 1,
                  "instrument": {"symbol": "INTC",
                                 "assetType": "EQUITY"
                                 }
                  }
             ]
             }
    resp = client.order_place(account_hash, order)
    print("\nPlace an order:")
    print(f"Response code: {resp}")
    # get the order ID - if order is immediately filled then the id might not be returned
    order_id = resp.headers.get('location', '/').split('/')[-1]
    print(f"Order id: {order_id}")
    sleep(3)

    print("\nGet specific order details")
    print(client.order_details(account_hash, order_id).json())
    sleep(3)

    print("\nCancel a specific order")
    print(client.order_cancel(account_hash, order_id))
    sleep(3)

    # No demo implemented
    # print("\nReplace specific order")
    # client.order_replace(account_hash, order_id, order)
    """

    print("\nGet up to 3000 orders for all accounts for the past 30 days")
    print(client.account_orders_all(datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30),
                                    datetime.datetime.now(datetime.timezone.utc)).json())
    sleep(3)

    # preview order (not implemented by Schwab yet)
    # print("\nclient.order_preview(account_hash, orderObject)")
    # client.order_preview(account_hash, orderObject)


    print("\nGet all transactions for an account")
    print(client.transactions(account_hash, datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=30), datetime.datetime.now(datetime.timezone.utc), "TRADE").json())
    sleep(3)

    # get details for a specific transaction (no demo implemented)
    # print("\nclient.transaction_details(account_hash, transactionId).json()")
    # print(client.transaction_details(account_hash, transactionId).json())


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
    print("There is a lot to print so this is not shown, the demo code is commented out")
    # print(client.option_chains("AAPL").json())
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


if __name__ == '__main__':
    print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
    print("Documentation: https://tylerebowers.github.io/Schwabdev/")
    main()  # call the user code above
