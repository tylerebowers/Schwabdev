import os
import asyncio
import dotenv
import schwabdev

dotenv.load_dotenv()

# get concurrent quotes for multiple tickers

async def main():
    tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "AMD", "NVDA", "META", "INTC", "CSCO"]
    
    async with schwabdev.ClientAsync(os.getenv("app_key"), os.getenv("app_secret"), os.getenv("callback_url")) as client:

        print((await (await client.linked_accounts()).json()))

        async with asyncio.TaskGroup() as tg:
            results = [tg.create_task((await client.quotes(t)).json()) for t in tickers]

        print([result.result() for result in results])



if __name__ == "__main__":
    asyncio.run(main())