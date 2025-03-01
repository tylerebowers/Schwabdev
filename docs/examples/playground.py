"""
This file functions as a "terminal emulator" so you can enter python code to test the api without restarting th whole program.
"""

from dotenv import load_dotenv
import schwabdev
import logging
import os


def main():
    # place your app key and app secret in the .env file
    load_dotenv()  # load environment variables from .env file

    # warn user if they have not added their keys to the .env
    if len(os.getenv('app_key')) != 32 or len(os.getenv('app_secret')) != 16:
        raise Exception("Add you app key and app secret to the .env file.")

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
    print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
    print("Documentation: https://tylerebowers.github.io/Schwabdev/")
    main()  # call the user code above
