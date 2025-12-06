import json
import os
import threading
import time
import logging
from collections import deque
from datetime import datetime

import dotenv
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import schwabdev

SYMBOLS = ["AMD"]
MAX_POINTS = 300 
FIELD = "3"

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

client = schwabdev.Client(os.getenv('app_key'),
                          os.getenv('app_secret'),
                          os.getenv('callback_url'))
streamer = client.stream
shared_list: list[str] = []

# time and price buffers per symbol
time_data = {sym: deque(maxlen=MAX_POINTS) for sym in SYMBOLS}
price_data = {sym: deque(maxlen=MAX_POINTS) for sym in SYMBOLS}

def response_handler(message: str):
    shared_list.append(message)

streamer.start(response_handler)
streamer.send(streamer.level_one_equities(",".join(SYMBOLS), f"0,{FIELD}"))
#streamer.send(streamer.level_one_futures(",".join(SYMBOLS), f"0,{FIELD}"))


def consumer_loop():
    """Consume buffered messages, extract prices, and store them in time/price buffers."""
    while True:
        while shared_list:
            oldest_response = json.loads(shared_list.pop(0))

            for rtype, services in oldest_response.items():
                if rtype == "data":
                    for service in services:
                        service_type = service.get("service", None)
                        service_timestamp = service.get("timestamp", 0)
                        contents = service.get("content", [])

                        for content in contents:
                            symbol = content.pop("key", "NO KEY")
                            fields = content  # dict with "0","1","2"... keys

                            if symbol not in SYMBOLS:
                                continue

                            # convert ms -> datetime
                            ts = datetime.fromtimestamp(service_timestamp // 1000)

                            # get the chosen price field (e.g. last price)
                            price_raw = fields.get(FIELD, None)
                            if price_raw is None:
                                continue

                            try:
                                price = float(price_raw)
                            except (TypeError, ValueError):
                                continue

                            time_data[symbol].append(ts)
                            price_data[symbol].append(price)
                            print(f"[{service_type} - {symbol}]({ts}): price={price}")
        time.sleep(0.1)


# start consumer in a background thread
consumer_thread = threading.Thread(target=consumer_loop, daemon=True)
consumer_thread.start()

# -------------- MATPLOTLIB LIVE CHART -----------------

plt.ion()
fig, ax = plt.subplots()
lines = {}

for sym in SYMBOLS:
    (line,) = ax.plot([], [], label=sym)
    lines[sym] = line

ax.set_xlabel("Time")
ax.set_ylabel("Price")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%I:%M:%S %p"))
ax.ticklabel_format(axis="y", style="plain", useOffset=False)
fig.autofmt_xdate()

while True:
    updated = False

    for sym in SYMBOLS:
        if len(time_data[sym]) == 0:
            continue

        lines[sym].set_data(list(time_data[sym]), list(price_data[sym]))
        updated = True

    if updated:
        ax.relim()
        ax.autoscale_view()
        fig.canvas.draw()
        fig.canvas.flush_events()

    time.sleep(0.5)
