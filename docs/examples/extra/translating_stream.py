"""
!!! Run this file with `python -i playground.py` !!!
It allows you to enter python code to test the api without restarting the whole program.
"""

import logging
import os
from dotenv import load_dotenv
import schwabdev


print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
print("Documentation: https://tylerebowers.github.io/Schwabdev/")

# place your app key and app secret in the .env file
load_dotenv()  # load environment variables from .env file

# warn user if they have not added their keys to the .env
if not len(os.getenv('app_key')) > 0 or not len(os.getenv('app_secret')) > 0:
    raise Exception("Add you app key and app secret to the .env file.")

# set logging level
logging.basicConfig(level=logging.INFO)

client = schwabdev.Client(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'))
streamer = schwabdev.Stream(client)



streamer.start(lambda msg: print(schwabdev.translate(msg.get("data"))), daemon=False)

streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3,4,5,6,7,8"))

import time
time.sleep(5)