# Using the Streamer

Examples can be found in [`docs/examples/stream_demo.py`](https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/stream_demo.py); there is also a streamer guide for more details.

To first use the streamer, initialize the client as normal (`client = schwabdev.Client(...)`). The initialization of the client object also initializes a streamer which can be accessed via `client.stream`.

It is recommended to set a streamer variable such as `streamer = client.stream` for shorter code and readability; documentation will also reference this variable name.

```python
import schwabdev

client = schwabdev.Client(...)
streamer = client.stream
```

---

## Starting the stream

To start the streamer you simply call `streamer.start()`. However, you will need a response handler to do something useful (see below).

The stream will close after ~30 seconds if there are no subscriptions.

By default the stream starts as a daemon thread, meaning that if the main thread terminates then the stream will too. If you want the stream to continue despite the main thread terminating, add `daemon=False` to the `.start(...)` parameters — this is useful if you are only using the response handler for processing.

---

## Using your own response handler

In typical applications you will want to use a separate response handler that parses received data from the stream. The default method just prints to the terminal.

```python
data = []
def my_handler(message):
    data.append("TEST" + message)

streamer.start(my_handler)

while True:
    if data:
        print(data.pop(0))
```

In the above example, the `my_handler(...)` function is called whenever a response is received from the stream. It appends the response to a list `data` with `"TEST"` prefixed.

It is important to code this function such that it is not too taxing on the system as you don’t want the response handler to fall behind the streamer.

You can also pass in variables (`args` and/or `kwargs`) into the `start` function which will be passed to the `my_handler` function.

---

## Starting the stream automatically

If you want to start the streamer automatically when the market opens, then instead of `streamer.start()` use the call `streamer.start_auto(...)`.

The default values will start & stop the streamer during normal market hours (9:30am–4:00pm EST). Starting the stream automatically will preserve the previous subscriptions.

`streamer.start_auto(receiver=print, start_time=datetime.time(9, 29, 0), stop_time=datetime.time(16, 0, 0), on_days=(0,1,2,3,4), now_timezone=zoneinfo.ZoneInfo("America/New_York"), daemon=True)`

* `start_time (datetime.time)`: When to start the streamer
* `stop_time (datetime.time)`: When to stop the streamer
* `on_days (list | tuple)`: Which days to start and stop the streamer. The default (Mon–Fri) is `on_days=(0,1,2,3,4)`.
* `now_timezone (zoneinfo.ZoneInfo)`: Custom timezone, default is `"America/New_York"` (Eastern Time)

---

## Stopping the stream

To stop the streamer use `streamer.stop()`.

Pass the parameter `clear_subscriptions=False` (default: `True`) if you want to keep the recorded subscriptions — this means that the next time you start the stream it will resubscribe to the previous subscriptions (except if the program is restarted).

---

## Sending stream requests

Sending requests to the streamer can be done using the `streamer.send(message)` function.

Schwabdev offers shortcut functions for **all** streamable assets (covered below). For example, to subscribe to an equity, pass `streamer.level_one_equities(...)` to the `send` function.

> **Important:** `"0"` must always be included in the fields.

Shown here is every way to use the shortcut functions:

```python
# Every way to subscribe to the fields 0,1,2,3 for equities "AMD" and "INTC"
streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3"))
streamer.send(streamer.level_one_equities(["AMD", "INTC"], ["0", "1", "2", "3"]))
streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3", command="ADD"))
streamer.send(
    streamer.basic_request(
        "LEVELONE_EQUITIES",
        "ADD",
        parameters={"keys": "AMD,INTC", "fields": "0,1,2,3"},
    )
)
```

If you are using an async function, then sending asynchronous requests to the streamer can be done using the `streamer.send_async(message)` function:

```python
# Asynchronous subscription request for fields 0,1,2,3 of equities "AMD" and "INTC"
await streamer.send_async(streamer.level_one_equities("AMD,INTC", "0,1,2,3"))
```

---

## Streamable assets

**Notes:**

* `"0"` must always be included in the fields.

* The list of fields and their definitions can be found in the streamer guide PDF.

* The maximum number of keys that can be subscribed to at once is **500**.

* Shortcut function commands can be changed by setting the `command` parameter, e.g. `command="ADD"`.
  The default is the `"ADD"` command, except for `account_activity` which defaults to `"SUBS"`.

  Each command is explained below:

  * `"ADD"` → the list of symbols will be added/appended to current subscriptions for a particular service.
  * `"SUBS"` → overwrites **all** current subscriptions (in a particular service) with the list of symbols passed in.
  * `"UNSUBS"` → removes the list of symbols from current subscriptions for a particular service.
  * `"VIEW"` → change the list of subscribed fields for the passed-in symbols.
    *Might not be functional on Schwab’s end.*

* These shortcuts all send the same thing:

  ```python
  streamer.basic_request(
      "LEVELONE_EQUITIES",
      "ADD",
      parameters={"keys": "AMD,INTC", "fields": "0,1,2,3,4"},
  )

  streamer.level_one_equities("AMD,INTC", "0,1,2,3,4", command="ADD")

  streamer.level_one_equities(["AMD", "INTC"], "0,1,2,3,4")

  streamer.level_one_equities("AMD,INTC", ["0", "1", "2", "3", "4"])

  streamer.level_one_equities("AMD,INTC", "0,1,2,3,4")
  ```

* Different products have different methods of sending data:

  * `LEVELONE_EQUITIES`, `LEVELONE_OPTIONS`, `LEVELONE_FUTURES`, `LEVELONE_FUTURES_OPTIONS`, and `LEVELONE_FOREX` all stream **changes**, meaning that the data you receive overwrites the previous fields.
    Example:

    * First you receive: `{"1": 20, "2": 25, "3": 997}`
    * Then you receive: `{"2": 28}`
    * The current data will be: `{"1": 20, "2": 28, "3": 997}`

  * `NYSE_BOOK`, `NASDAQ_BOOK`, `OPTIONS_BOOK`, `SCREENER_EQUITY`, and `SCREENER_OPTION` all stream **whole** data, meaning all fields.

  * `CHART_EQUITY`, `CHART_FUTURES`, and `ACCT_ACTIVITY` stream **all-sequence** data, meaning you are given a sequence number for each response.

Listed below are the shortcut functions for all streamable assets.

---

### Level one equities

> `streamer.send(streamer.level_one_equities(keys, fields))`
> Key examples: `"AMD"`, `"INTC"`, `"$SPX"`

---

### Level one options

> `streamer.send(streamer.level_one_options(keys, fields))`
> Key examples: `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`

> **Key format:**
> `Underlying Symbol (6 chars including spaces)` + `Expiration (6 chars)` + `Call/Put (1 char)` + `Strike Price (5+3 = 8 chars)`
> Expiration is in `YYMMDD` format.

---

### Level one futures

> `streamer.send(streamer.level_one_futures(keys, fields))`
> Key examples: `"/ESF24"`, `"/GCG24"`, `"/ES"`

> **Key format:**
> `'/' + 'root symbol' + 'month code' + 'year code'`
> Month code is 1 character:
> `F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec`
> Year code is 2 characters (i.e. 2024 → `24`).

---

### Level one futures options

> `streamer.send(streamer.level_one_futures_options(keys, fields))`
> Key examples: `"./OZCZ23C565"`

> **Key format:**
> `'.' + '/' + 'root symbol' + 'month code' + 'year code' + 'Call/Put (1 char)' + 'Strike Price'`
> Month code is 1 character (same mapping as futures).
> Year code is 2 characters (i.e. 2024 → `24`).

---

### Level one forex

> `streamer.send(streamer.level_one_forex(keys, fields))`
> Key examples: `"EUR/USD"`, `"GBP/USD"`, `"EUR/JPY"`, `"EUR/GBP"`

---

### NYSE book orders

> `streamer.send(streamer.nyse_book(keys, fields))`
> Key examples: `"F"`, `"NIO"`, `"ACU"`

---

### NASDAQ book orders

> `streamer.send(streamer.nasdaq_book(keys, fields))`
> Key examples: `"AMD"`, `"INTC"`

---

### Options book orders

> `streamer.send(streamer.options_book(keys, fields))`
> Key examples: `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`

> **Key format:**
> Same as level one options:
> `Underlying Symbol (6 chars including spaces)` + `Expiration (6 chars)` + `Call/Put (1 char)` + `Strike Price (5+3 = 8 chars)`
> Expiration is in `YYMMDD` format.

---

### Chart equity

> `streamer.send(streamer.chart_equity(keys, fields))`
> Key examples: `"AMD"`, `"INTC"`

---

### Chart futures

> `streamer.send(streamer.chart_futures(keys, fields))`
> Key examples: `"/ESF24"`, `"/GCG24"`

> **Key format:**
> `'/' + 'root symbol' + 'month code' + 'year code'`
> Month code is 1 character (same mapping as futures).
> Year code is 2 characters (i.e. 2024 → `24`).

---

### Screener equity

> `streamer.send(streamer.screener_equity(keys, fields))`
> Key examples: `"$DJI_PERCENT_CHANGE_UP_60"`, `"NASDAQ_VOLUME_30"`

> **Key format:**
> `(PREFIX)_(SORTFIELD)_(FREQUENCY)`
>
> **Prefix:**
> `$COMPX`, `$DJI`, `$SPX.X`, `INDEX_AL`, `NYSE`, `NASDAQ`, `OTCBB`, `EQUITY_ALL`
>
> **Sortfield:**
> `VOLUME`, `TRADES`, `PERCENT_CHANGE_UP`, `PERCENT_CHANGE_DOWN`, `AVERAGE_PERCENT_VOLUME`
>
> **Frequency:**
> `0` (all day), `1`, `5`, `10`, `30`, `60`

---

### Screener options

> `streamer.send(streamer.screener_options(keys, fields))`
> Key examples: `"OPTION_PUT_PERCENT_CHANGE_UP_60"`, `"OPTION_CALL_TRADES_30"`

> **Key format:**
> `(PREFIX)_(SORTFIELD)_(FREQUENCY)`
>
> **Prefix:**
> `OPTION_PUT`, `OPTION_CALL`, `OPTION_ALL`
>
> **Sortfield:**
> `VOLUME`, `TRADES`, `PERCENT_CHANGE_UP`, `PERCENT_CHANGE_DOWN`, `AVERAGE_PERCENT_VOLUME`
>
> **Frequency:**
> `0` (all day), `1`, `5`, `10`, `30`, `60`

---

### Account activity

> `streamer.send(streamer.account_activity("Account Activity", "0,1,2,3"))`
>
> There is only one key: `"Account Activity"` and the fields should be `"0,1,2,3"`.
> Only `"SUBS"` (default) and `"UNSUBS"` are supported for `command`.

#### Response Message Types

When using the account activity stream, the response message types (displayed in field `"2"`) are as follows:

* **OrderCreated** – Indicates an order has been successfully created.
* **OrderAccepted** – Confirms that the order has been accepted for processing.
* **OrderMonitorCreated** – A monitor is set up for tracking the order’s status.
* **ExecutionRequested** – Execution of the order has been requested.
* **ExecutionRequestCreated** – A request for execution is officially logged.
* **ExecutionRequestCompleted** – The requested execution has been completed successfully.
* **OrderFillCompleted** – The order is fully filled and finalized.
* **OrderMonitorCompleted** – The monitoring process for the order has concluded.
* **OrderMonitorUpdated** – The monitor tracking the order status is updated.

