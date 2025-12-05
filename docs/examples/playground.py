"""
!!! Run this file with `python -i playground.py` !!!
It allows you to enter python code to test the api without restarting the whole program.
"""

import logging
import sys
import subprocess
import os
from dotenv import load_dotenv
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

client = schwabdev.Client(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'))
streamer = client.stream
print("Client and Streamer created as 'client' and 'stream' variables, use quit() to exit.")
