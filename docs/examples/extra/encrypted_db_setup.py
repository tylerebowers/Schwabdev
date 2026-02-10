"""
This example demonstrates how to set up an encrypted database for storing tokens using Schwabdev.
"""

import logging
import os
from dotenv import load_dotenv
import schwabdev
from cryptography.fernet import Fernet
import time

# place your app key and app secret in the .env file
load_dotenv()  # load environment variables from .env file

# warn user if they have not added their keys to the .env
if not len(os.getenv('app_key')) > 0 or not len(os.getenv('app_secret')) > 0:
    raise Exception("Add you app key and app secret to the .env file.")

# set logging level
logging.basicConfig(level=logging.INFO)

print("This script helps setup an encrypted tokens database for Schwabdev.")
time.sleep(3)
print("First, we need to generate an encryption key.")
time.sleep(3)
print("!!!! Save this key, you will need it each time you make a Client !!!!")
key = Fernet.generate_key()
print("Encryption key:", key.decode())
time.sleep(5)
input("Next, we will redo the authentication process to save the encrypted tokens. Press Enter to continue, or Ctrl+C to exit.")
os.environ['encryption'] = key.decode() # store the key in an environment variable
client = schwabdev.Client(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'), encryption=os.getenv('encryption'))
print("Now that you are authenticated, the encrypted tokens are saved in the database.")
print("You can now create new Client instances using the same encryption key to access the tokens.")
print("If you want to remove encryption, create a new Client without the encryption parameter and redo the authentication process.")
