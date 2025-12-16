"""
Schwabdev Template Example
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
#account_hash = client.linked_accounts().json()[0].get('hashValue')
streamer = schwabdev.Stream(client)
