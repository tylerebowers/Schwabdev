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
* Shortcut function commands can be changed by setting the `command` parameter, e.g. `command="ADD"`. The default is the `"ADD"` command, except for `account_activity` which defaults to `"SUBS"`.
* Each command is explained below:
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

    * `LEVELONE_EQUITIES`, `LEVELONE_OPTIONS`, `LEVELONE_FUTURES`, `LEVELONE_FUTURES_OPTIONS`, and `LEVELONE_FOREX` all stream **changes**, meaning that the data you receive overwrites the previous fields. Example:
        * First you receive: `{"1": 20, "2": 25, "3": 997}`
        * Then you receive: `{"2": 28}`
        * The current data will be: `{"1": 20, "2": 28, "3": 997}`
  * `NYSE_BOOK`, `NASDAQ_BOOK`, `OPTIONS_BOOK`, `SCREENER_EQUITY`, and `SCREENER_OPTION` all stream **whole** data, meaning all fields.
  * `CHART_EQUITY`, `CHART_FUTURES`, and `ACCT_ACTIVITY` stream **all-sequence** data, meaning you are given a sequence number for each response.

Listed below are the shortcut functions for all streamable assets.

---

### Level one equities

`streamer.send(streamer.level_one_equities(keys, fields))`

* Key examples: `"AMD"`, `"INTC"`, `"$SPX"`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.level_one_equities("AMD,INTC", "0,1,2,3,4,5,6,7,8"))
{
  "data": [
    {
      "service": "LEVELONE_EQUITIES",
      "timestamp": 1765081984668,
      "command": "SUBS",
      "content": [
        {
          "1": 217.86,
          "2": 217.95,
          "3": 217.93,
          "4": 200,
          "5": 100,
          "6": "P",
          "7": "P",
          "8": 33292396,
          "key": "AMD",
          "delayed": false,
          "assetMainType": "EQUITY",
          "assetSubType": "COE",
          "cusip": "007903107"
        },
        {
          "1": 41.43,
          "2": 41.44,
          "3": 41.44,
          "4": 200,
          "5": 400,
          "6": "P",
          "7": "U",
          "8": 103042015,
          "key": "INTC",
          "delayed": false,
          "assetMainType": "EQUITY",
          "assetSubType": "COE",
          "cusip": "458140100"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  
0: "Symbol"<br>
1: "Bid Price"<br>
2: "Ask Price"<br>
3: "Last Price"<br>
4: "Bid Size"<br>
5: "Ask Size"<br>
6: "Ask ID"<br>
7: "Bid ID"<br>
8: "Total Volume"<br>
9: "Last Size"<br>
10: "High Price"<br>
11: "Low Price"<br>
12: "Close Price"<br>
13: "Exchange ID"<br>
14: "Marginable"<br>
15: "Description"<br>
16: "Last ID"<br>
17: "Open Price"<br>
18: "Net Change"<br>
19: "52 Week High"<br>
20: "52 Week Low"<br>
21: "PE Ratio"<br>
22: "Annual Dividend Amount"<br>
23: "Dividend Yield"<br>
24: "NAV"<br>
25: "Exchange Name"<br>
26: "Dividend Date"<br>
27: "Regular Market Quote"<br>
28: "Regular Market Trade"<br>
29: "Regular Market Last Price"<br>
30: "Regular Market Last Size"<br>
31: "Regular Market Net Change"<br>
32: "Security Status"<br>
33: "Mark Price"<br>
34: "Quote Time in Long"<br>
35: "Trade Time in Long"<br>
36: "Regular Market Trade Time in Long"<br>
37: "Bid Time"<br>
38: "Ask Time"<br>
39: "Ask MIC ID"<br>
40: "Bid MIC ID"<br>
41: "Last MIC ID"<br>
42: "Net Percent Change"<br>
43: "Regular Market Percent Change"<br>
44: "Mark Price Net Change"<br>
45: "Mark Price Percent Change"<br>
46: "Hard to Borrow Quantity"<br>
47: "Hard To Borrow Rate"<br>
48: "Hard to Borrow"<br>
49: "shortable"<br>
50: "Post-Market Net Change"<br>
51: "Post-Market Percent Change"<br>
</details>
---

### Level one options

> `streamer.send(streamer.level_one_options(keys, fields))`
> Key examples: `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`

> **Key format:**
> `Underlying Symbol (6 chars including spaces)` + `Expiration (6 chars)` + `Call/Put (1 char)` + `Strike Price (5+3 = 8 chars)`
> Expiration is in `YYMMDD` format.

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.level_one_options("SPXW  251208C06880000", "0,1,2,3,4,5,6,7,8"))
{
  "data": [
    {
      "service": "LEVELONE_OPTIONS",
      "timestamp": 1765082498588,
      "command": "SUBS",
      "content": [
        {
          "1": "SPXW 12/08/2025 6880.00 C",
          "2": 10.2,
          "3": 10.6,
          "4": 10.6,
          "5": 28.9,
          "6": 6.9,
          "7": 9.15,
          "8": 7961,
          "key": "SPXW  251208C06880000",
          "delayed": false,
          "assetMainType": "OPTION"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  
0: "Symbol"<br>
1: "Description"<br>
2: "Bid Price"<br>
3: "Ask Price"<br>
4: "Last Price"<br>
5: "High Price"<br>
6: "Low Price"<br>
7: "Close Price"<br>
8: "Total Volume"<br>
9: "Open Interest"<br>
10: "Volatility"<br>
11: "Money Intrinsic Value"<br>
12: "Expiration Year"<br>
13: "Multiplier"<br>
14: "Digits"<br>
15: "Open Price"<br>
16: "Bid Size"<br>
17: "Ask Size"<br>
18: "Last Size"<br>
19: "Net Change"<br>
20: "Strike Price"<br>
21: "Contract Type"<br>
22: "Underlying"<br>
23: "Expiration Month"<br>
24: "Deliverables"<br>
25: "Time Value"<br>
26: "Expiration Day"<br>
27: "Days to Expiration"<br>
28: "Delta"<br>
29: "Gamma"<br>
30: "Theta"<br>
31: "Vega"<br>
32: "Rho"<br>
33: "Security Status"<br>
34: "Theoretical Option Value"<br>
35: "Underlying Price"<br>
36: "UV Expiration Type"<br>
37: "Mark Price"<br>
38: "Quote Time in Long"<br>
39: "Trade Time in Long"<br>
40: "Exchange"<br>
41: "Exchange Name"<br>
42: "Last Trading Day"<br>
43: "Settlement Type"<br>
44: "Net Percent Change"<br>
45: "Mark Price Net Change"<br>
46: "Mark Price Percent Change"<br>
47: "Implied Yield"<br>
48: "isPennyPilot"<br>
49: "Option Root"<br>
50: "52 Week High"<br>
51: "52 Week Low"<br>
52: "Indicative Ask Price"<br>
53: "Indicative Bid Price"<br>
54: "Indicative Quote Time"<br>
55: "Exercise Type"<br>
</details>
---

### Level one futures

> `streamer.send(streamer.level_one_futures(keys, fields))`
> Key examples: `"/ESF24"`, `"/GCG24"`, `"/ES"`

> **Key format:**
> `'/' + 'root symbol' + 'month code' + 'year code'`
> Month code is 1 character:
> `F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec`
> Year code is 2 characters (i.e. 2024 → `24`).

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.level_one_futures("/ES", "0,1,2,3,4,5,6"))
{
  "data": [
    {
      "service": "LEVELONE_FUTURES",
      "timestamp": 1765083430060,
      "command": "SUBS",
      "content": [
        {
          "1": 6879.25,
          "2": 6879.75,
          "3": 6879.5,
          "4": 11,
          "5": 4,
          "6": "?",
          "key": "/ES",
          "delayed": false,
          "assetMainType": "FUTURE"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  
0: "Symbol"<br>
1: "Bid Price"<br>
2: "Ask Price"<br>
3: "Last Price"<br>
4: "Bid Size"<br>
5: "Ask Size"<br>
6: "Bid ID"<br>
7: "Ask ID"<br>
8: "Total Volume"<br>
9: "Last Size"<br>
10: "Quote Time "<br>
11: "Trade Time "<br>
12: "High Price"<br>
13: "Low Price"<br>
14: "Close Price"<br>
15: "Exchange ID"<br>
16: "Description"<br>
17: "Last ID"<br>
18: "Open Price"<br>
19: "Net Change"<br>
20: "Future Percent Change"<br>
21: "Exchange Name"<br>
22: "Security Status"<br>
23: "Open Interest"<br>
24: "Mark"<br>
25: "Tick"<br>
26: "Tick Amount"<br>
27: "Product"<br>
28: "Future Price Format"<br>
29: "Future Trading Hours"<br>
30: "Future Is Tradable"<br>
31: "Future Multiplier"<br>
32: "Future Is Active"<br>
33: "Future Settlement Price"<br>
34: "Future Active Symbol"<br>
35: "Future Expiration Date"<br>
36: "Expiration Style"<br>
37: "Ask Time"<br>
38: "Bid Time"<br>
39: "Quoted In Session"<br>
40: "Settlement Date"<br>
</details>
---

### Level one futures options

> `streamer.send(streamer.level_one_futures_options(keys, fields))`
> Key examples: `"./OZCZ23C565"`

> **Key format:**
> `'.' + '/' + 'root symbol' + 'month code' + 'year code' + 'Call/Put (1 char)' + 'Strike Price'`
> Month code is 1 character (same mapping as futures).
> Year code is 2 characters (i.e. 2024 → `24`).

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.level_one_futures_options("./OGG26C4240", "0,1,2,3,4,5"))
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  
0: "Symbol"<br>
1: "Bid Price"<br>
2: "Ask Price"<br>
3: "Last Price"<br>
4: "Bid Size"<br>
5: "Ask Size"<br>
6: "Bid ID"<br>
7: "Ask ID"<br>
8: "Total Volume"<br>
9: "Last Size"<br>
10: "Quote Time"<br>
11: "Trade Time"<br>
12: "High Price"<br>
13: "Low Price"<br>
14: "Close Price"<br>
15: "Last ID"<br>
16: "Description"<br>
17: "Open Price"<br>
18: "Open Interest"<br>
19: "Mark"<br>
20: "Tick"<br>
21: "Tick Amount"<br>
22: "Future Multiplier"<br>
23: "Future Settlement Price"<br>
24: "Underlying Symbol"<br>
25: "Strike Price"<br>
26: "Future Expiration Date"<br>
27: "Expiration Style"<br>
28: "Contract Type"<br>
29: "Security Status"<br>
30: "Exchange"<br>
31: "Exchange Name"<br>
</details>
---

### Level one forex

> `streamer.send(streamer.level_one_forex(keys, fields))`
> Key examples: `"EUR/USD"`, `"GBP/USD"`, `"EUR/JPY"`, `"EUR/GBP"`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.level_one_forex("EUR/USD", "0,1,2,3,4,5,6,7,8"))
{
  "data": [
    {
      "service": "LEVELONE_FOREX",
      "timestamp": 1765084326675,
      "command": "SUBS",
      "content": [
        {
          "1": 1.1643,
          "2": 1.16443,
          "3": 1.164365,
          "4": 100000,
          "5": 100000,
          "6": 0,
          "7": 0,
          "8": 1764971942013,
          "key": "EUR/USD",
          "delayed": false,
          "assetMainType": "FOREX"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  
0: "Symbol"<br>
1: "Bid Price"<br>
2: "Ask Price"<br>
3: "Last Price"<br>
4: "Bid Size"<br>
5: "Ask Size"<br>
6: "Total Volume"<br>
7: "Last Size"<br>
8: "Quote Time"<br>
9: "Trade Time"<br>
10: "High Price"<br>
11: "Low Price"<br>
12: "Close Price"<br>
13: "Exchange"<br>
14: "Description"<br>
15: "Open Price"<br>
16: "Net Change"<br>
17: "Percent Change"<br>
18: "Exchange Name"<br>
19: "Digits"<br>
20: "Security Status"<br>
21: "Tick"<br>
22: "Tick Amount"<br>
23: "Product"<br>
24: "Trading Hours"<br>
25: "Is Tradable"<br>
26: "Market Maker"<br>
27: "52 Week High"<br>
28: "52 Week Low"<br>
29: "Mark"<br>
</details>
---

### NYSE book orders

> `streamer.send(streamer.nyse_book(keys, fields))`
> Key examples: `"F"`, `"NIO"`, `"ACU"`

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
---

### NASDAQ book orders

> `streamer.send(streamer.nasdaq_book(keys, fields))`
> Key examples: `"AMD"`, `"INTC"`

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
---

### Options book orders

> `streamer.send(streamer.options_book(keys, fields))`
> Key examples: `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`

> **Key format:**
> Same as level one options:
> `Underlying Symbol (6 chars including spaces)` + `Expiration (6 chars)` + `Call/Put (1 char)` + `Strike Price (5+3 = 8 chars)`
> Expiration is in `YYMMDD` format.

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
---

### Chart equity

> `streamer.send(streamer.chart_equity(keys, fields))`
> Key examples: `"AMD"`, `"INTC"`

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
---

### Chart futures

> `streamer.send(streamer.chart_futures(keys, fields))`
> Key examples: `"/ESF24"`, `"/GCG24"`

> **Key format:**
> `'/' + 'root symbol' + 'month code' + 'year code'`
> Month code is 1 character (same mapping as futures).
> Year code is 2 characters (i.e. 2024 → `24`).

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
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

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
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

<details><summary><u>Data Example</u></summary>

```python
> 

```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
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

<details><summary><u>Key Translations</u></summary>
Schwabdev has a translator for fields, see above.<br>  

</details>
<details><summary><u>Data Example</u></summary>

```python
# No example
```
</details>