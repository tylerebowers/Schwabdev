"""
Example of translating field numbers to field names in a streaming response.
"""

import logging
import os
from dotenv import load_dotenv
import schwabdev
import json
import datetime



def translate_data(response) -> list[str]:
    """
    Translate field numbers to field names

    Returns:
        list[str]: list of field names
    """
    for item in response.get("data", []):
        if isinstance(item, dict):
            service = item.get("service", None)
            timestamp = item.get("timestamp", None)
            content = item.get("content", None)
            if timestamp:
                item["timestamp"] = datetime.datetime.fromtimestamp(timestamp / 1000)

            if service and content and service.startswith("LEVELONE_"):
                if isinstance(content, list):
                    for quote in content:
                        for field, value in quote.copy().items():
                            if field.isdigit():
                                new_field = translate_field(service, field)
                                quote[new_field] = quote.pop(field)                           
                                      
    return response
    
    
def translate_field(service: str, field: str|int) -> str:
    """
    Translate field number to field name

    Args:
        field (str|int): field number
    Returns:
        str: field name
    """
    mapping = schwabdev.stream_fields.get(service.upper(), None)
    if mapping is None:
        return str(field)
    try:
        if isinstance(mapping, dict):
            return mapping.get(field, str(field))
        elif isinstance(mapping, list):
            index = int(field)
            if 0 <= index < len(mapping):
                return mapping[index]
            else:
                return str(field)
        else:
            return str(field)
    except Exception:
        return str(field)

if __name__ == "__main__":
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

    def response_handler(msg):
        translated = translate_data(json.loads(msg))
        print(translated)


    streamer.start(response_handler)

    streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3,4,5,6,7,8"))
    # streamer.send(streamer.nyse_book(["F"], "0,1,2,3,4,5,6,7,8"))

    import time
    time.sleep(30)
    streamer.stop()