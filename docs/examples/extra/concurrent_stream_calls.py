import os
import asyncio
import dotenv
import logging
import schwabdev

dotenv.load_dotenv()

STOP_AT = 10 # number of messages to receive before stopping

logging.basicConfig(level=logging.INFO)

tickers = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "AMD", "NVDA", "META", "INTC", "CSCO"]

async def main():

    data = []
    def response_handler(message):
        data.append(message)
    
    async with schwabdev.ClientAsync(os.getenv("app_key"), os.getenv("app_secret"), os.getenv("callback_url")) as client:
        streamer = client.stream
        #streamer.start(response_handler) # start async in another thread
        streamer.start(response_handler) # start async in current event loop
        async with asyncio.TaskGroup() as tg:
            for t in tickers:
                tg.create_task(streamer.send_async(streamer.level_one_equities(t, fields="0,1,2,3,4,5,6,7,8,9")))

        counter = 0
        while True:
            if data:
                counter += 1
                print(data.pop(0))
            if counter == STOP_AT:
                streamer.stop()
                break
            await asyncio.sleep(0.1)
            

if __name__ == "__main__":
    asyncio.run(main())