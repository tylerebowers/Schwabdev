"""
This file functions as a "terminal emulator".
It allows you to enter python code to test the api without restarting th whole program.
"""

import logging
import os

from dotenv import load_dotenv

import schwabdev


def main():
    # place your app key and app secret in the .env file
    load_dotenv()  # load environment variables from .env file

    # set logging level
    logging.basicConfig(level=logging.INFO)

    client = schwabdev.Client(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'))
    streamer = client.stream

    # a "terminal emulator" to play with the API
    print("\nTerminal emulator - enter python code to execute.")
    while True:
        try:
            entered = input(">")
            exec(entered.lstrip(">")) # remove leading ">" just in case user copy-pasted it.
        except Exception as error:
            print(error)


if __name__ == '__main__':
    print("Welcome to The Unofficial Schwab Python Wrapper!")
    print("Github: https://github.com/tylerebowers/Schwab-API-Python")
    main()  # call the user code above
