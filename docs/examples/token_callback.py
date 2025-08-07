"""
This file contains example of connecting to remote token storage callback.
pip install redis
"""

import datetime
import logging
import json
import os
import redis
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

    # Create Redis Connection
    r = redis.Redis(host='localhost', port=6379, decode_responses=True, db=1)

    r.ping()
    print("Connected to Redis!")

    def get_token_callback(): return json.loads(r.get('schwab:token'))
    def set_token_callback(token): return r.set('schwab:token', json.dumps(token))

    # create client
    client = schwabdev.Client(
        os.getenv('app_key'),
        os.getenv('app_secret'),
        os.getenv('callback_url'),
        get_token_callback=get_token_callback,
        set_token_callback=set_token_callback
    )

    print("\nGet account number and hashes for linked accounts")
    linked_accounts = client.account_linked().json()
    print(linked_accounts)
    sleep(3)

    print("\nGet details for all linked accounts")
    print(client.account_details_all().json())
    sleep(3)


if __name__ == '__main__':
    print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
    print("Documentation: https://tylerebowers.github.io/Schwabdev/")
    main()  # call the user code above
