"""
!!! Run this file with `python -i playground.py` !!!
It allows you to enter python code to test the api without restarting the whole program.
"""

import logging
import sys
import os
from dotenv import load_dotenv
import asyncio
import threading
import schwabdev

if not sys.flags.interactive:
    print("This file is intended to be run in interactive mode, with \"python -i async_playground.py\"\n"*3)
    sys.exit(1)

print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
print("Documentation: https://tylerebowers.github.io/Schwabdev/")

# place your app key and app secret in the .env file
load_dotenv()  # load environment variables from .env file

# warn user if they have not added their keys to the .env
if len(os.getenv('app_key')) != 32 or len(os.getenv('app_secret')) != 16:
    raise Exception("Add you app key and app secret to the .env file.")

# set logging level
logging.basicConfig(level=logging.INFO)

_loop = asyncio.new_event_loop()


def _loop_worker(loop: asyncio.AbstractEventLoop) -> None:
    asyncio.set_event_loop(loop)
    loop.run_forever()


threading.Thread(target=_loop_worker, args=(_loop,), daemon=True).start()


def run(coro: asyncio.Future) -> object:
    """
    Run an async coroutine on the background loop from the REPL.

    Example in the interactive session:
        >>> run(client.some_async_method(...))
    """
    return asyncio.run_coroutine_threadsafe(coro, _loop).result()


async def _init_client() -> None:
    global client, streamer
    client = schwabdev.ClientAsync(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'), parsed=True)
    streamer = client.stream
    logging.info(
        "Async Schwabdev client initialized.\n"
        "Client and Streamer created as 'client' and 'stream' variables, use `run(...)` to call async methods, and use quit() to exit."
    )


# Schedule client initialization on the background loop
asyncio.run_coroutine_threadsafe(_init_client(), _loop)
