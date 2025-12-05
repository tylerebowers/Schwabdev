# demo_async.py

import asyncio
import datetime
import logging
import os
from dotenv import load_dotenv

import schwabdev


print("Welcome to Schwabdev (async demo), The Unofficial Schwab API Python Wrapper!")
print("Documentation: https://tylerebowers.github.io/Schwabdev/")

# place your app key and app secret in the .env file
load_dotenv()  # load environment variables from .env file

# set logging level
logging.basicConfig(level=logging.INFO)


async def main():
    # create async client (uses your ClientAsync)
    async with schwabdev.ClientAsync(
        os.getenv("app_key"),
        os.getenv("app_secret"),
        os.getenv("callback_url"),
    ) as client:

        # small helper instead of time.sleep
        async def pause():
            await asyncio.sleep(3)

        print("\nGet account number and hashes for linked accounts")
        linked_accounts = await client.linked_accounts(parsed=True)
        print(linked_accounts)
        account_hash = linked_accounts[0].get("hashValue")  # first linked account
        await pause()

        print("\nGet details for all linked accounts")
        print(await client.account_details_all(parsed=True))
        await pause()

        print("\nGet specific account positions (uses default account, can be changed)")
        print(await client.account_details(account_hash, fields="positions", parsed=True))
        await pause()

        print("\nGet orders for a linked account")
        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        print(await client.account_orders(account_hash, thirty_days_ago, now, parsed=True))
        await pause()

        order = {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "price": "10.00",
            "orderLegCollection": [
                {
                    "instruction": "BUY",
                    "quantity": 1,
                    "instrument": {
                        "symbol": "INTC",
                        "assetType": "EQUITY",
                    },
                }
            ],
        }

        # Uncomment to enable order placing/details/cancelling demo
        """
        resp = await client.place_order(account_hash, order)
        print(f"\nPlace an order status: {resp.status}")
        order_location = resp.headers.get("Location", "/")
        order_id = order_location.split("/")[-1]  # might be missing if order fills immediately
        print(f"Order id: {order_id}")
        await pause()

        print("\nGet specific order details")
        print(await client.order_details(account_hash, order_id, parsed=True))
        
        await pause()

        print("\nCancel a specific order")
        resp = await client.cancel_order(account_hash, order_id)
        print(resp.status)
        await pause()
        """

        print("\nReplace specific order")
        # await client.replace_order(account_hash, order_id, order)
        print("No demo implemented")
        await pause()

        print("\nGet up to 3000 orders for all accounts for the past 30 days")
        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        print(await client.account_orders_all(thirty_days_ago, now, parsed=True))
        
        await pause()

        print("\nPreview an order")
        print(await client.preview_order(account_hash, order, parsed=True))
        
        await pause()

        print("\nGet all transactions for an account")
        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        print(await client.transactions(
            account_hash,
            thirty_days_ago,
            now,
            "TRADE",
            parsed=True,
        ))
        await pause()

        print("\nGet details for a specific transaction")
        # print(await client.transaction_details(account_hash, transactionId)
        print("No demo implemented")
        await pause()

        print("\nGet user preferences for an account")
        print(await client.preferences(parsed=True))
        await pause()

        print("\nGet a list of quotes")
        print(await client.quotes(["AAPL", "AMD"], parsed=True))
        await pause()

        print("\nGet a single quote")
        print(await client.quote("INTC", parsed=True))
        
        # print(await client.quote("SPXW  241111P06000000")  # example of an expired contract
        # 
        await pause()

        print("\nGet an option chain")
        print("Demo disabled to prevent flooding terminal.")
        # print(await client.option_chains("AAPL", contractType="CALL", range="OTM")
        await pause()

        print("\nGet an option expiration chain")
        print(await client.option_expiration_chain("AAPL", parsed=True))
        await pause()

        print("\nGet price history for a symbol")
        print(await client.price_history("AAPL", "year", parsed=True))
        await pause()

        print("\nGet movers for an index")
        print(await client.movers("$DJI", parsed=True))
        await pause()

        print("\nGet marketHours for symbols")
        print(await client.market_hours(["equity", "option"], parsed=True))
        # print(await client.market_hours(["equity", "option"])  # already using list form
        await pause()

        print("\nGet marketHours for a market")
        print(await client.market_hour("equity", parsed=True))
        await pause()

        print("\nGet instruments for a symbol")
        print(await client.instruments("AAPL", "fundamental", parsed=True))
        await pause()

        print("\nGet instruments for a cusip")
        print(await client.instrument_cusip("037833100", parsed=True))  # 037833100 = AAPL
        await pause()


if __name__ == "__main__":
    asyncio.run(main())
