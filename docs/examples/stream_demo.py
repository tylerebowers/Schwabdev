"""
This file contains examples for stream requests.
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

    # define a variable for the steamer:
    streamer = client.stream


    # example of using your own response handler, prints to main terminal.
    # the first parameter is used by the stream, additional parameters are passed to the handler
    def my_handler(message):
        print("test_handler:" + message)
    streamer.start(my_handler)


    # start steamer with default response handler (print):
    #streamer.start()


    # You can stream up to 500 keys.
    # By default all shortcut requests (below) will be "ADD" commands meaning the list of symbols will be added/appended
    # to current subscriptions for a particular service, however if you want to overwrite subscription (in a particular
    # service) you can use the "SUBS" command. Unsubscribing uses the "UNSUBS" command. To change the list of fields use
    # the "VIEW" command.


    # these three do the same thing
    # streamer.send(streamer.basic_request("LEVELONE_EQUITIES", "ADD", parameters={"keys": "AMD,INTC", "fields": "0,1,2,3,4,5,6,7,8"}))
    # streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3,4,5,6,7,8", command="ADD"))
    streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3,4,5,6,7,8"))


    # streamer.send(streamer.level_one_options("GOOGL 240712C00200000", "0,1,2,3,4,5,6,7,8")) # key must be from option chains api call.
    # streamer.send(streamer.level_one_options("SPY   241014C00580000", "0,1,2,3,4,5,6,7,8"))

    streamer.send(streamer.level_one_futures("/ES", "0,1,2,3,4,5,6"))

    # streamer.send(streamer.level_one_futures_options("./OZCZ23C565", "0,1,2,3,4,5"))

    # streamer.send(streamer.level_one_forex("EUR/USD", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.nyse_book(["F", "NIO"], "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.nasdaq_book("AMD", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.options_book("GOOGL 240712C00200000", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.chart_equity("AMD", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.chart_futures("/ES", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.screener_equity("NASDAQ_VOLUME_30", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.screener_options("OPTION_CALL_TRADES_30", "0,1,2,3,4,5,6,7,8"))

    # streamer.send(streamer.account_activity("Account Activity", "0,1,2,3"))


    # stop the stream after 60 seconds (since this is a demo)
    import time
    time.sleep(60)
    streamer.stop()
    # if you don't want to clear the subscriptions, set clear_subscriptions=False
    # streamer.stop(clear_subscriptions=False)
    # if True, then the next time you start the stream it will resubscribe to the previous subscriptions (except if program is restarted)


if __name__ == '__main__':
    print("Welcome to Schwabdev, The Unofficial Schwab API Python Wrapper!")
    print("Documentation: https://tylerebowers.github.io/Schwabdev/")
    main()  # call the user code above
