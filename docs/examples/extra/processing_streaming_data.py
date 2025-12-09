"""
This file is an example of how to process streaming data.
While you can process completely in the response handler this could leave the stream with a backlog.
The preferred method is to use a shared list, shown here as "shared_list"
"""
import json
import logging
import os
import time
from datetime import datetime

import dotenv

import schwabdev

# load environment
dotenv.load_dotenv()

# warn user if they have not added their keys to the .env
if len(os.getenv('app_key')) != 32 or len(os.getenv('app_secret')) != 16:
    raise Exception("Add you app key and app secret to the .env file.")

# set logging level
logging.basicConfig(level=logging.INFO)

# make a client
client = schwabdev.Client(os.getenv('app_key'), os.getenv('app_secret'), os.getenv('callback_url'))
streamer = schwabdev.Stream(client)

# define a response handler
shared_list: list[str] = []


def response_handler(message):
    shared_list.append(message)

# start the stream and send in what symbols we want.
streamer.start(response_handler)
streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3,4,5,6,7,8"))


while True: # proccessing on list is done here
    # print the most recent message
    while len(shared_list) > 0: # while there is still data to consume from the list
        oldest_response = json.loads(shared_list.pop(0))  # get the oldest data from the list
        # print(oldest_response)
        for rtype, services in oldest_response.items():
            if rtype == "data":
                for service in services:
                    service_type = service.get("service", None)
                    service_timestamp = service.get("timestamp", 0)
                    contents = service.get("content", [])
                    for content in contents:
                        symbol = content.pop("key", "NO KEY")
                        fields = content
                        print(f"[{service_type} - {symbol}]({datetime.fromtimestamp(service_timestamp//1000)}): {fields}")
            elif rtype == "response":
                pass # this is a "login success" or "subscription success" or etc
            elif rtype == "notify":
                pass # this is a heartbeat (usually) which means that the stream is still alive
            else:
                # unidentified response type
                print(oldest_response)
    time.sleep(0.5) # slow down difference checking