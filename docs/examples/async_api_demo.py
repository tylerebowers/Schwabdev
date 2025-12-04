# demo_async.py

import asyncio
import datetime
import logging
import os

from time import sleep  # only if you still want sleep somewhere else; otherwise remove
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
        linked_resp = await client.account_linked()
        linked_accounts = await linked_resp.json()
        print(linked_accounts)
        account_hash = linked_accounts[0].get("hashValue")  # first linked account
        await pause()

        print("\nGet details for all linked accounts")
        resp = await client.account_details_all()
        print(await resp.json())
        await pause()

        print("\nGet specific account positions (uses default account, can be changed)")
        resp = await client.account_details(account_hash, fields="positions")
        print(await resp.json())
        await pause()

        print("\nGet orders for a linked account")
        now = datetime.datetime.now(datetime.timezone.utc)
        thirty_days_ago = now - datetime.timedelta(days=30)
        resp = await client.account_orders(account_hash, thirty_days_ago, now)
        print(await resp.json())
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
                        "symbol": "AMD",
                        "assetType": "EQUITY",
                    },
                }
            ],
        }

        # Uncomment to enable order placing/details/cancelling demo
        """
        resp = await client.order_place(account_hash, order)
        print(f"\nPlace an order status: {resp.status}")
        order_location = resp.headers.get("Location", "/")
        order_id = order_location.split("/")[-1]  # might be missing if order fills immediately
        print(f"Order id: {order_id}")
        await pause()

        print("\nGet specific order details")
        resp = await client.order_details(account_hash, order_id)
        print(await resp.json())
        await pause()

        print("\nCancel a specific order")
        resp = await client.order_cancel(account_hash, order_id)
        print(resp.status)
        await pause()
        """

        print("\nReplace specific order")
        # await client.order_replace(account_hash, order_id, order)
        print("No demo implemented")
        await pause()

        print("\nGet up to 3000 orders for all accounts for the past 30 days")
        resp = await client.account_orders_all(thirty_days_ago, now)
        print(await resp.json())
        await pause()

        # NOTE: your async client currently does NOT have an async preview method
        # (order_preview is commented out), so we just show a placeholder here.
        print("\nPreview an order")
        print("No async preview_order demo implemented (method commented out in ClientAsync).")

        print("\nGet all transactions for an account")
        resp = await client.transactions(
            account_hash,
            thirty_days_ago,
            now,
            "TRADE",
        )
        print(await resp.json())
        await pause()

        print("\nGet details for a specific transaction")
        # resp = await client.transaction_details(account_hash, transactionId)
        # print(await resp.json())
        print("No demo implemented")
        await pause()

        print("\nGet user preferences for an account")
        resp = await client.preferences()
        print(await resp.json())
        await pause()

        print("\nGet a list of quotes")
        resp = await client.quotes(["AAPL", "AMD"])
        print(await resp.json())
        await pause()

        print("\nGet a single quote")
        resp = await client.quote("INTC")
        print(await resp.json())
        # resp = await client.quote("SPXW  241111P06000000")  # example of an expired contract
        # print(await resp.json())
        await pause()

        print("\nGet an option chain")
        print("Demo disabled to prevent flooding terminal.")
        # resp = await client.option_chains("AAPL", contractType="CALL", range="OTM")
        # print(await resp.json())
        await pause()

        print("\nGet an option expiration chain")
        resp = await client.option_expiration_chain("AAPL")
        print(await resp.json())
        await pause()

        print("\nGet price history for a symbol")
        resp = await client.price_history("AAPL", "year")
        print(await resp.json())
        await pause()

        print("\nGet movers for an index")
        resp = await client.movers("$DJI")
        print(await resp.json())
        await pause()

        print("\nGet marketHours for symbols")
        resp = await client.market_hours(["equity", "option"])
        print(await resp.json())
        # resp = await client.market_hours(["equity", "option"])  # already using list form
        await pause()

        print("\nGet marketHours for a market")
        resp = await client.market_hour("equity")
        print(await resp.json())
        await pause()

        print("\nGet instruments for a symbol")
        resp = await client.instruments("AAPL", "fundamental")
        print(await resp.json())
        await pause()

        print("\nGet instruments for a cusip")
        resp = await client.instrument_cusip("037833100")  # 037833100 = AAPL
        print(await resp.json())
        await pause()


if __name__ == "__main__":
    asyncio.run(main())
