# Using the Streamer

Examples can be found in <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/">`docs/examples/`</a>.

To first use the streamer, initialize the client as normal (e.g. `client = schwabdev.Client(...)`). Then create a streamer object by passing in the client. The synchronous or asynchronous streamer can be used interchangeably with the synchronous and asynchronous client.

```python
import schwabdev

client = schwabdev.Client(...)
# client = schwabdev.ClientAsync(...) # For an asynchronous client
streamer = schwabdev.Stream(client)
# streamer = schwabdev.StreamAsync(client) # For an asynchronous streamer
```

Since websockets are asynchronous `schwabdev.Stream` runs an async event loop in a separate thread, allowing you to use the streamer in synchronous code. `schwabdev.StreamAsync` runs on the current async event loop (the one that it was called from). 

---

## Starting the stream

To start the streamer you simply call `streamer.start()`. However, you will need a response handler to do something useful (see below).

The stream will close after ~30 seconds if there are no subscriptions.

By default the stream starts as a daemon thread, meaning that if the main thread terminates then the stream will too. If you want the stream to continue despite the main thread terminating, add `daemon=False` to the `.start(...)` parameters — this is useful if you are only using the response handler for processing. If you are using `daemon=False` and your main thread is fairly empty you may need to add a sleep so the stream thread has time to start.

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

# With await for asynchronous streamer:
await streamer.send(...)
```

If you are using `schwabdev.Stream` (not `StreamAsync`) then sending requests can also be done asynchronously using the `streamer.send_async(message)` function:

```python
# Asynchronous subscription request for fields 0,1,2,3 of equities "AMD" and "INTC"
await streamer.send_async(streamer.level_one_equities("AMD,INTC", "0,1,2,3"))
```

---

## Translating field keys

Schwabdev contains a translator map for all streamable asset fields. You can access the translator map using `schwabdev.stream_fields`. It is best to look at the <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/tree/main/schwabdev/translate.py">Source</a> and <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/tree/main/docs/examples/extra/translating_stream.py">Examples</a>.

---

## Streamable assets

**Notes:**

* `"0"` must always be included in the fields.
* The maximum number of keys that can be subscribed to at once is **500**.
* Shortcut function commands can be changed by setting the `command` parameter, e.g. `command="ADD"`. The default is the `"ADD"` command, except for `account_activity` which defaults to `"SUBS"`.
* Each command is explained below:
    * `"ADD"` → the list of symbols will be added/appended to current subscriptions for a particular service.
    * `"SUBS"` → overwrites **all** current subscriptions (in a particular service) with the list of symbols passed in.
    * `"UNSUBS"` → removes the list of symbols from current subscriptions for a particular service.
    * `"VIEW"` → change the list of subscribed fields for the passed-in symbols.

* Different products have different methods of sending data:

    * `LEVELONE_EQUITIES`, `LEVELONE_OPTIONS`, `LEVELONE_FUTURES`, `LEVELONE_FUTURES_OPTIONS`, and `LEVELONE_FOREX` all stream **changes**, meaning that the data you receive overwrites the previous fields. Example:
      * First you receive: `{"1": 20, "2": 25, "3": 997}`
      * Then you receive: `{"2": 28}`
      * The current data will be: `{"1": 20, "2": 28, "3": 997}`
  * `NYSE_BOOK`, `NASDAQ_BOOK`, `OPTIONS_BOOK`, `SCREENER_EQUITY`, and `SCREENER_OPTION` all stream **whole** data, meaning all fields.
  * `CHART_EQUITY`, `CHART_FUTURES`, and `ACCT_ACTIVITY` stream **all-sequence** data, meaning you are given a sequence number for each response. 
      * The i'th sequence number is the i'th candle during that day since pre-market hours for charting.

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
Schwabdev has a translation map for fields, see above.<br>  
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

`streamer.send(streamer.level_one_options(keys, fields))`
Key examples: `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`

**Key format:**
`Underlying Symbol (6 chars including spaces)` + `Expiration (6 chars)` + `Call/Put (1 char)` + `Strike Price (5+3 = 8 chars)`
Expiration is in `YYMMDD` format.

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
Schwabdev has a translation map for fields, see above.<br>  
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

`streamer.send(streamer.level_one_futures(keys, fields))`
Key examples: `"/ESF24"`, `"/GCG24"`, `"/ES"`

**Key format:**
`'/' + 'root symbol' + 'month code' + 'year code'`
Month code is 1 character:
`F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec`
Year code is 2 characters (i.e. 2024 → `24`).

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
Schwabdev has a translation map for fields, see above.<br>  
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

`streamer.send(streamer.level_one_futures_options(keys, fields))`
Key examples: `"./OZCZ23C565"`

**Key format:**
`'.' + '/' + 'root symbol' + 'month code' + 'year code' + 'Call/Put (1 char)' + 'Strike Price'`
Month code is 1 character (same mapping as futures).
Year code is 2 characters (i.e. 2024 → `24`).

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.level_one_futures_options("./OGG26C4240", "0,1,2,3,4,5"))
{
  "data": [
    {
      "service": "LEVELONE_FUTURES_OPTIONS",
      "timestamp": 1765306046616,
      "command": "SUBS",
      "content": [
        {
          "1": 110.5,
          "2": 111.5,
          "3": 101.7,
          "4": 25,
          "5": 39,
          "key": "./OGG26C4240",
          "delayed": false,
          "assetMainType": "FUTURE_OPTION"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
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

`streamer.send(streamer.level_one_forex(keys, fields))`
Key examples: `"EUR/USD"`, `"GBP/USD"`, `"EUR/JPY"`, `"EUR/GBP"`

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
Schwabdev has a translation map for fields, see above.<br>  
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

`streamer.send(streamer.nyse_book(keys, fields))`
Key examples: `"F"`, `"NIO"`, `"ACU"`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.nyse_book(["F"], "0,1,2,3,4,5,6,7,8"))
{
  "data": [
    {
      "service": "NYSE_BOOK",
      "timestamp": 1765306323315,
      "command": "SUBS",
      "content": [
        {
          "1": 1765306322349,
          "2": [
            {
              "0": 13.12,
              "1": 31600,
              "2": 9,
              "3": [
                {
                  "0": "NYSE",
                  "1": 8800,
                  "2": 49786299
                },
                {
                  "0": "IEXG",
                  "1": 7900,
                  "2": 49904606
                },
                {
                  "0": "ARCX",
                  "1": 4200,
                  "2": 49904606
                },
                {
                  "0": "NSDQ",
                  "1": 3600,
                  "2": 49904602
                },
                {
                  "0": "MWSE",
                  "1": 3200,
                  "2": 49904653
                },
                {
                  "0": "BATX",
                  "1": 2000,
                  "2": 49786299
                },
                {
                  "0": "MEMX",
                  "1": 1000,
                  "2": 49904603
                },
                {
                  "0": "EDGX",
                  "1": 800,
                  "2": 49904606
                },
                {
                  "0": "G",
                  "1": 100,
                  "2": 49904603
                }
              ]
            },
            {
              "0": 13.11,
              "1": 900,
              "2": 2,
              "3": [
                {
                  "0": "MIAX",
                  "1": 800,
                  "2": 49902308
                },
                {
                  "0": "EDGA",
                  "1": 100,
                  "2": 49902308
                }
              ]
            },
            {
              "0": 13.1,
              "1": 800,
              "2": 2,
              "3": [
                {
                  "0": "BATY",
                  "1": 500,
                  "2": 49902311
                },
                {
                  "0": "CINN",
                  "1": 300,
                  "2": 49902308
                }
              ]
            },
            {
              "0": 12.86,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "AMEX",
                  "1": 100,
                  "2": 49904647
                }
              ]
            },
            {
              "0": 12.46,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "BOSX",
                  "1": 100,
                  "2": 49533394
                }
              ]
            }
          ],
          "3": [
            {
              "0": 13.13,
              "1": 76300,
              "2": 14,
              "3": [
                {
                  "0": "NYSE",
                  "1": 34100,
                  "2": 49786298
                },
                {
                  "0": "IEXG",
                  "1": 13400,
                  "2": 49786299
                },
                {
                  "0": "NSDQ",
                  "1": 8000,
                  "2": 49786299
                },
                {
                  "0": "ARCX",
                  "1": 7600,
                  "2": 49786298
                },
                {
                  "0": "BATX",
                  "1": 3600,
                  "2": 49786298
                },
                {
                  "0": "EDGX",
                  "1": 2800,
                  "2": 49786298
                },
                {
                  "0": "MIAX",
                  "1": 2400,
                  "2": 49788199
                },
                {
                  "0": "MEMX",
                  "1": 2200,
                  "2": 49786299
                },
                {
                  "0": "BATY",
                  "1": 800,
                  "2": 49902308
                },
                {
                  "0": "CINN",
                  "1": 800,
                  "2": 49902308
                },
                {
                  "0": "AMEX",
                  "1": 200,
                  "2": 49798053
                },
                {
                  "0": "MWSE",
                  "1": 200,
                  "2": 49902308
                },
                {
                  "0": "G",
                  "1": 100,
                  "2": 49786299
                },
                {
                  "0": "EDGA",
                  "1": 100,
                  "2": 49788235
                }
              ]
            },
            {
              "0": 13.26,
              "1": 27600,
              "2": 1,
              "3": [
                {
                  "0": "PHLX",
                  "1": 27600,
                  "2": 49904602
                }
              ]
            }
          ],
          "key": "F"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
0: "Symbol"<br>
1: "Market Snapshot Time"<br>
2: "Bid Side Levels"<br>
3: "Ask Side Levels"<br>
Price Levels: "['Price', 'Aggregate Size', 'Market Maker CountArray of Market Makers']"<br>
Market Makers: "['Market Maker ID', 'Size', 'Quote Time']"<br>
</details>
---

### NASDAQ book orders

`streamer.send(streamer.nasdaq_book(keys, fields))`
Key examples: `"AMD"`, `"INTC"`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.nasdaq_book("AMD", "0,1,2,3,4,5,6,7,8"))
{
  "data": [
    {
      "service": "NASDAQ_BOOK",
      "timestamp": 1765306382737,
      "command": "SUBS",
      "content": [
        {
          "1": 1765306382549,
          "2": [
            {
              "0": 221.38,
              "1": 640,
              "2": 4,
              "3": [
                {
                  "0": "iexg",
                  "1": 200,
                  "2": 49980045
                },
                {
                  "0": "edgx",
                  "1": 200,
                  "2": 49980852
                },
                {
                  "0": "NSDQ",
                  "1": 140,
                  "2": 49978628
                },
                {
                  "0": "G",
                  "1": 100,
                  "2": 49980039
                }
              ]
            },
            {
              "0": 221.31,
              "1": 200,
              "2": 1,
              "3": [
                {
                  "0": "batx",
                  "1": 200,
                  "2": 49978628
                }
              ]
            },
            {
              "0": 221.3,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "arcx",
                  "1": 100,
                  "2": 49981932
                }
              ]
            },
            {
              "0": 221.24,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "memx",
                  "1": 100,
                  "2": 49980042
                }
              ]
            },
            {
              "0": 221.13,
              "1": 200,
              "2": 1,
              "3": [
                {
                  "0": "nyse",
                  "1": 200,
                  "2": 49980488
                }
              ]
            },
            {
              "0": 221,
              "1": 300,
              "2": 2,
              "3": [
                {
                  "0": "mwse",
                  "1": 200,
                  "2": 49909023
                },
                {
                  "0": "edga",
                  "1": 100,
                  "2": 49980050
                }
              ]
            },
            {
              "0": 220.88,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "ETMM",
                  "1": 100,
                  "2": 49752758
                }
              ]
            },
            {
              "0": 220.5,
              "1": 300,
              "2": 1,
              "3": [
                {
                  "0": "miax",
                  "1": 300,
                  "2": 49980039
                }
              ]
            },
            {
              "0": 219.39,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "JPMS",
                  "1": 100,
                  "2": 49980045
                }
              ]
            },
            {
              "0": 219.17,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "MAXM",
                  "1": 100,
                  "2": 49980045
                }
              ]
            },
            {
              "0": 218.3,
              "1": 200,
              "2": 1,
              "3": [
                {
                  "0": "baty",
                  "1": 200,
                  "2": 48791798
                }
              ]
            }
          ],
          "3": [
            {
              "0": 221.44,
              "1": 250,
              "2": 2,
              "3": [
                {
                  "0": "NSDQ",
                  "1": 150,
                  "2": 49794602
                },
                {
                  "0": "iexg",
                  "1": 100,
                  "2": 49981361
                }
              ]
            },
            {
              "0": 221.49,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "arcx",
                  "1": 100,
                  "2": 49980039
                }
              ]
            },
            {
              "0": 221.5,
              "1": 1000,
              "2": 1,
              "3": [
                {
                  "0": "edgx",
                  "1": 1000,
                  "2": 49980038
                }
              ]
            },
            {
              "0": 221.51,
              "1": 500,
              "2": 1,
              "3": [
                {
                  "0": "memx",
                  "1": 500,
                  "2": 49930772
                }
              ]
            },
            {
              "0": 221.56,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "batx",
                  "1": 100,
                  "2": 49980486
                }
              ]
            },
            {
              "0": 221.61,
              "1": 200,
              "2": 1,
              "3": [
                {
                  "0": "nyse",
                  "1": 200,
                  "2": 49961758
                }
              ]
            },
            {
              "0": 221.8,
              "1": 200,
              "2": 1,
              "3": [
                {
                  "0": "mwse",
                  "1": 200,
                  "2": 49954654
                }
              ]
            },
            {
              "0": 221.81,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "edga",
                  "1": 100,
                  "2": 49980051
                }
              ]
            },
            {
              "0": 221.83,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "ETMM",
                  "1": 100,
                  "2": 49861460
                }
              ]
            },
            {
              "0": 221.86,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "miax",
                  "1": 100,
                  "2": 49975610
                }
              ]
            },
            {
              "0": 223.43,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "JPMS",
                  "1": 100,
                  "2": 49981361
                }
              ]
            },
            {
              "0": 223.66,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "MAXM",
                  "1": 100,
                  "2": 49981361
                }
              ]
            },
            {
              "0": 225.5,
              "1": 400,
              "2": 1,
              "3": [
                {
                  "0": "baty",
                  "1": 400,
                  "2": 49964541
                }
              ]
            },
            {
              "0": 225.87,
              "1": 100,
              "2": 1,
              "3": [
                {
                  "0": "cinn",
                  "1": 100,
                  "2": 44337496
                }
              ]
            }
          ],
          "key": "AMD"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
0: "Symbol"<br>
1: "Market Snapshot Time"<br>
2: "Bid Side Levels"<br>
3: "Ask Side Levels"<br>
Price Levels: "['Price', 'Aggregate Size', 'Market Maker CountArray of Market Makers']"<br>
Market Makers: "['Market Maker ID', 'Size', 'Quote Time']"<br>
</details>
---

### Options book orders

`streamer.send(streamer.options_book(keys, fields))`
Key examples: `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`

**Key format:**
Same as level one options:
`Underlying Symbol (6 chars including spaces)` + `Expiration (6 chars)` + `Call/Put (1 char)` + `Strike Price (5+3 = 8 chars)`
Expiration is in `YYMMDD` format.

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.options_book("GOOGL 251212C00315000", "0,1,2,3"))
{
  "data": [
    {
      "service": "OPTIONS_BOOK",
      "timestamp": 1765307114646,
      "command": "SUBS",
      "content": [
        {
          "1": 1765307114236,
          "2": [
            {
              "0": 5.45,
              "1": 146,
              "2": 16,
              "3": [
                {
                  "0": "S",
                  "1": 24,
                  "2": 50714236
                },
                {
                  "0": "PACX",
                  "1": 21,
                  "2": 50714140
                },
                {
                  "0": "MEMX",
                  "1": 16,
                  "2": 50713823
                },
                {
                  "0": "MIAX",
                  "1": 14,
                  "2": 50713922
                },
                {
                  "0": "AMEX",
                  "1": 10,
                  "2": 50714017
                },
                {
                  "0": "BATS",
                  "1": 9,
                  "2": 50713807
                },
                {
                  "0": "PHLX",
                  "1": 9,
                  "2": 50714079
                },
                {
                  "0": "BOSX",
                  "1": 9,
                  "2": 50713802
                },
                {
                  "0": "EDGX",
                  "1": 7,
                  "2": 50714029
                },
                {
                  "0": "ISEX",
                  "1": 7,
                  "2": 50713814
                },
                {
                  "0": "XBXO",
                  "1": 5,
                  "2": 50713819
                },
                {
                  "0": "MERC",
                  "1": 5,
                  "2": 50713823
                },
                {
                  "0": "CBOE",
                  "1": 4,
                  "2": 50713922
                },
                {
                  "0": "NYSE",
                  "1": 3,
                  "2": 50713521
                },
                {
                  "0": "GMNI",
                  "1": 2,
                  "2": 50713801
                },
                {
                  "0": "NSDQ",
                  "1": 1,
                  "2": 50713806
                }
              ]
            }
          ],
          "3": [
            {
              "0": 5.55,
              "1": 2029,
              "2": 16,
              "3": [
                {
                  "0": "AMEX",
                  "1": 362,
                  "2": 50714236
                },
                {
                  "0": "CBOE",
                  "1": 291,
                  "2": 50713922
                },
                {
                  "0": "EDGX",
                  "1": 279,
                  "2": 50714029
                },
                {
                  "0": "PHLX",
                  "1": 232,
                  "2": 50714079
                },
                {
                  "0": "BOSX",
                  "1": 156,
                  "2": 50713802
                },
                {
                  "0": "S",
                  "1": 152,
                  "2": 50713806
                },
                {
                  "0": "ISEX",
                  "1": 112,
                  "2": 50713814
                },
                {
                  "0": "MIAX",
                  "1": 99,
                  "2": 50713922
                },
                {
                  "0": "MERC",
                  "1": 76,
                  "2": 50713823
                },
                {
                  "0": "BATS",
                  "1": 70,
                  "2": 50713807
                },
                {
                  "0": "NSDQ",
                  "1": 47,
                  "2": 50713806
                },
                {
                  "0": "GMNI",
                  "1": 39,
                  "2": 50713801
                },
                {
                  "0": "PACX",
                  "1": 37,
                  "2": 50713527
                },
                {
                  "0": "NYSE",
                  "1": 29,
                  "2": 50713521
                },
                {
                  "0": "XBXO",
                  "1": 26,
                  "2": 50713819
                },
                {
                  "0": "MEMX",
                  "1": 22,
                  "2": 50713823
                }
              ]
            }
          ],
          "key": "GOOGL 251212C00315000"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
0: "Symbol"<br>
1: "Market Snapshot Time"<br>
2: "Bid Side Levels"<br>
3: "Ask Side Levels"<br>
Price Levels: "['Price', 'Aggregate Size', 'Market Maker CountArray of Market Makers']"<br>
Market Makers: "['Market Maker ID', 'Size', 'Quote Time']"<br>
</details>
---

### Chart equity

`streamer.send(streamer.chart_equity(keys, fields))`
Key examples: `"AMD"`, `"INTC"`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.chart_equity("AMD", "0,1,2,3,4,5,6,7,8"))
{
  "data": [
    {
      "service": "CHART_EQUITY",
      "timestamp": 1765307221991,
      "command": "SUBS",
      "content": [
        {
          "1": 425, # seqence number since pre-market hours start (e.g. 7am est)
          "2": 221.133,
          "3": 221.18,
          "4": 221.02,
          "5": 221.02,
          "6": 11730,
          "7": 1765307100000,
          "8": 20431,
          "seq": 202,
          "key": "AMD"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
Note that Schwab's official docs are wrong, these are the correct fields: <br>
0: "key"<br>
1: "Sequence"<br>
2: "Open Price"<br>
3: "High Price"<br>
4: "Low Price"<br>
5: "Close Price"<br>
6: "Volume"<br>
7: "Chart Time"<br>
8: "Chart Day"<br>
</details>
---

### Chart futures

`streamer.send(streamer.chart_futures(keys, fields))`
Key examples: `"/ESF24"`, `"/GCG24"`

**Key format:**
`'/' + 'root symbol' + 'month code' + 'year code'`
Month code is 1 character (same mapping as futures).
Year code is 2 characters (i.e. 2024 → `24`).

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.chart_futures("/ES", "0,1,2,3,4,5,6"))
{
  "data": [
    {
      "service": "CHART_FUTURES",
      "timestamp": 1765307265036,
      "command": "SUBS",
      "content": [
        {
          "1": 1765307160000,
          "2": 6858.25,
          "3": 6858.75,
          "4": 6857.75,
          "5": 6858.5,
          "6": 897,
          "seq": 2224,
          "key": "/ES"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
0: "key"<br>
1: "Chart Time"<br>
2: "Open Price"<br>
3: "High Price"<br>
4: "Low Price"<br>
5: "Close Price"<br>
6: "Volume"<br>
</details>
---

### Screener equity

`streamer.send(streamer.screener_equity(keys, fields))`
Key examples: `"$DJI_PERCENT_CHANGE_UP_60"`, `"NASDAQ_VOLUME_30"`

**Key format:**
`(PREFIX)_(SORTFIELD)_(FREQUENCY)`

**Prefix:**
`$COMPX`, `$DJI`, `$SPX.X`, `INDEX_AL`, `NYSE`, `NASDAQ`, `OTCBB`, `EQUITY_ALL`

**Sortfield:**
`VOLUME`, `TRADES`, `PERCENT_CHANGE_UP`, `PERCENT_CHANGE_DOWN`, `AVERAGE_PERCENT_VOLUME`

**Frequency:**
`0` (all day), `1`, `5`, `10`, `30`, `60`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.screener_equity("NASDAQ_VOLUME_30", "0,1,2,3,4"))
{
  "data": [
    {
      "service": "SCREENER_EQUITY",
      "timestamp": 1765307304646,
      "command": "SUBS",
      "content": [
        {
          "1": 1765307297706,
          "2": "VOLUME",
          "3": 30,
          "4": [
            {
              "symbol": "WBD",
              "description": "WARNER BROS DISCOVER Series A",
              "lastPrice": 28.095,
              "netChange": 0.865,
              "netPercentChange": 0.03176643,
              "marketShare": 3.93926404,
              "totalVolume": 345149877,
              "volume": 13596365,
              "trades": 21302
            },
            {
              "symbol": "ASST",
              "description": "STRIVE INC A",
              "lastPrice": 1,
              "netChange": 0.0152,
              "netPercentChange": 0.01543461,
              "marketShare": 2.45609098,
              "totalVolume": 345149877,
              "volume": 8477195,
              "trades": 6351
            },
            {
              "symbol": "PAVS",
              "description": "PARANOVUS ENTERTAINM Class A",
              "lastPrice": 0.0428,
              "netChange": -0.0061,
              "netPercentChange": -0.12474438,
              "marketShare": 2.35480223,
              "totalVolume": 345149877,
              "volume": 8127597,
              "trades": 4031
            },
            {
              "symbol": "NCPL",
              "description": "NETCAPITAL INC EQUIT Equity",
              "lastPrice": 1.2997,
              "netChange": 0.6408,
              "netPercentChange": 0.97252997,
              "marketShare": 2.20918636,
              "totalVolume": 345149877,
              "volume": 7625004,
              "trades": 16488
            },
            {
              "symbol": "PLUG",
              "description": "PLUG PWR INC",
              "lastPrice": 2.2601,
              "netChange": 0.1001,
              "netPercentChange": 0.04634259,
              "marketShare": 2.08706376,
              "totalVolume": 345149877,
              "volume": 7203498,
              "trades": 11949
            },
            {
              "symbol": "OCG",
              "description": "ORIENTAL CULTURE HLD",
              "lastPrice": 7.9,
              "netChange": 5.28,
              "netPercentChange": 2.01526718,
              "marketShare": 1.64665769,
              "totalVolume": 345149877,
              "volume": 5683437,
              "trades": 68181
            },
            {
              "symbol": "NVDA",
              "description": "NVIDIA CORP",
              "lastPrice": 184.59,
              "netChange": -0.96,
              "netPercentChange": -0.00517381,
              "marketShare": 1.52208891,
              "totalVolume": 345149877,
              "volume": 5253488,
              "trades": 67812
            },
            {
              "symbol": "OPEN",
              "description": "OPENDOOR TECHNOLOGIE Class A",
              "lastPrice": 7.11,
              "netChange": 0.06,
              "netPercentChange": 0.00851064,
              "marketShare": 1.45892591,
              "totalVolume": 345149877,
              "volume": 5035481,
              "trades": 8315
            },
            {
              "symbol": "TSLS",
              "description": "DIREXION DAILY TSLA BEAR 1X ETF",
              "lastPrice": 5.16,
              "netChange": -0.1,
              "netPercentChange": -0.01901141,
              "marketShare": 1.45537441,
              "totalVolume": 345149877,
              "volume": 5023223,
              "trades": 1399
            },
            {
              "symbol": "POM",
              "description": "POMDOCTOR LTD ADR",
              "lastPrice": 5.26,
              "netChange": -0.31,
              "netPercentChange": -0.0556553,
              "marketShare": 1.33459674,
              "totalVolume": 345149877,
              "volume": 4606359,
              "trades": 6679
            }
          ],
          "key": "NASDAQ_VOLUME_30"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
0: "symbol"<br>
1: "timestamp"<br>
2: "sortField"<br>
3: "frequency"<br>
4: "Items"<br>
</details>
---

### Screener options

`streamer.send(streamer.screener_options(keys, fields))`
Key examples: `"OPTION_PUT_PERCENT_CHANGE_UP_60"`, `"OPTION_CALL_TRADES_30"`

**Key format:**
`(PREFIX)_(SORTFIELD)_(FREQUENCY)`

**Prefix:**
`OPTION_PUT`, `OPTION_CALL`, `OPTION_ALL`

**Sortfield:**
`VOLUME`, `TRADES`, `PERCENT_CHANGE_UP`, `PERCENT_CHANGE_DOWN`, `AVERAGE_PERCENT_VOLUME`

**Frequency:**
`0` (all day), `1`, `5`, `10`, `30`, `60`

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.screener_options("OPTION_CALL_TRADES_30", "0,1,2,3,4"))
{
  "data": [
    {
      "service": "SCREENER_OPTION",
      "timestamp": 1765307361611,
      "command": "SUBS",
      "content": [
        {
          "1": 1765307359566,
          "2": "TRADES",
          "3": 30,
          "4": [
            {
              "symbol": "SPXW  251209C06855000",
              "description": "SPXW   Dec 9 2025 6855.0 Call",
              "lastPrice": 2.75,
              "netChange": -8.891,
              "netPercentChange": -0.763766,
              "marketShare": 3.47850842,
              "totalVolume": 1761266,
              "volume": 21020,
              "trades": 7820
            },
            {
              "symbol": "SPY   251209C00684000",
              "description": "SPY    Dec 9 2025 684.0 Call",
              "lastPrice": 0.46,
              "netChange": -0.91,
              "netPercentChange": -0.66423358,
              "marketShare": 2.98297666,
              "totalVolume": 1761266,
              "volume": 75572,
              "trades": 6706
            },
            {
              "symbol": "SPXW  251209C06860000",
              "description": "SPXW   Dec 9 2025 6860.0 Call",
              "lastPrice": 1.27,
              "netChange": -8.2092,
              "netPercentChange": -0.86602245,
              "marketShare": 2.45230396,
              "totalVolume": 1761266,
              "volume": 16323,
              "trades": 5513
            },
            {
              "symbol": "SPXW  251209C06850000",
              "description": "SPXW   Dec 9 2025 6850.0 Call",
              "lastPrice": 5.2,
              "netChange": -8.6028,
              "netPercentChange": -0.62326484,
              "marketShare": 2.32641932,
              "totalVolume": 1761266,
              "volume": 14262,
              "trades": 5230
            },
            {
              "symbol": "SPY   251209C00685000",
              "description": "SPY    Dec 9 2025 685.0 Call",
              "lastPrice": 0.11,
              "netChange": -0.795,
              "netPercentChange": -0.87845304,
              "marketShare": 2.25213403,
              "totalVolume": 1761266,
              "volume": 66332,
              "trades": 5063
            },
            {
              "symbol": "QQQ   251209C00625000",
              "description": "QQQ    Dec 9 2025 625.0 Call",
              "lastPrice": 0.75,
              "netChange": -0.7296,
              "netPercentChange": -0.49310624,
              "marketShare": 1.51773283,
              "totalVolume": 1761266,
              "volume": 27545,
              "trades": 3412
            },
            {
              "symbol": "QQQ   251209C00626000",
              "description": "QQQ    Dec 9 2025 626.0 Call",
              "lastPrice": 0.27,
              "netChange": -0.77,
              "netPercentChange": -0.74038462,
              "marketShare": 1.45634739,
              "totalVolume": 1761266,
              "volume": 33176,
              "trades": 3274
            },
            {
              "symbol": "SPY   251209C00683000",
              "description": "SPY    Dec 9 2025 683.0 Call",
              "lastPrice": 1.15,
              "netChange": -0.8338,
              "netPercentChange": -0.42030447,
              "marketShare": 1.2730807,
              "totalVolume": 1761266,
              "volume": 30149,
              "trades": 2862
            },
            {
              "symbol": "SPXW  251209C06865000",
              "description": "SPXW   Dec 9 2025 6865.0 Call",
              "lastPrice": 0.57,
              "netChange": -6.7474,
              "netPercentChange": -0.92210348,
              "marketShare": 1.1156137,
              "totalVolume": 1761266,
              "volume": 7895,
              "trades": 2508
            },
            {
              "symbol": "SPXW  251209C06845000",
              "description": "SPXW   Dec 9 2025 6845.0 Call",
              "lastPrice": 8.6,
              "netChange": -7.3646,
              "netPercentChange": -0.46130814,
              "marketShare": 0.76109053,
              "totalVolume": 1761266,
              "volume": 4362,
              "trades": 1711
            }
          ],
          "key": "OPTION_CALL_TRADES_30"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
0: "symbol"<br>
1: "timestamp"<br>
2: "sortField"<br>
3: "frequency"<br>
4: "Items"<br>
</details>
---

### Account activity

`streamer.send(streamer.account_activity("Account Activity", "0,1,2,3"))`

There is only one key: `"Account Activity"` and the fields should be `"0,1,2,3"`.
Only `"SUBS"` (default) and `"UNSUBS"` are supported for `command`.

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

<details><summary><u>Data Example</u></summary>

```python
> streamer.send(streamer.account_activity("Account Activity", "0,1,2,3")) #Then a limit order for 1x "AMD" was placed...
#Order placed:
{
  "data": [
    {
      "service": "ACCT_ACTIVITY",
      "timestamp": 0000000000000,
      "command": "SUBS",
      "content": [
        {
          "1": "########",
          "2": "OrderCreated",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"OrderCreated\",\"OrderCreatedEventEquityOrder\":{\"EventType\":\"OrderCreated\",\"Order\":{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"Order\":{\"AccountInfo\":{\"AccountNumber\":\"########\",\"AccountBranch\":\"GR\",\"CustomerOrFirmCode\":\"CustomerOrFirmCode_Customer\",\"OrderPlacementCustomerID\":\"#########\",\"AccountState\":\"MI\",\"AccountTypeCode\":\"Customer\"},\"ClientChannelInfo\":{\"ClientProductCode\":\"MO\",\"EventUserID\":\"MYXX\",\"EventUserType\":\"Client\"},\"LifecycleCreatedTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"LifecycleSchwabOrderID\":\"#############\",\"EntryTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"ExpiryTimeStamp\":{\"DateTimeString\":\"2025-12-09\"},\"AutoConfirm\":true,\"PlanSubmitDate\":{\"DateTimeString\":\"2025-12-09\"},\"SourceOMS\":\"ngOMS\",\"FirmID\":\"CHAS\",\"OrderAccount\":\"TDAAccount\",\"AssetOrderEquityOrderLeg\":{\"OrderInstruction\":{\"HandlingInstructionCode\":\"AutomatedExecutionNoIntervention\",\"ExecutionStrategy\":{\"Type\":\"ES_Limit\",\"LimitExecutionStrategy\":{\"Type\":\"ES_Limit\",\"LimitPrice\":{\"lo\":\"220470000\",\"signScale\":12},\"LimitPriceUnitCode\":\"Units\"}},\"PreferredRoute\":{},\"EquityOrderInstruction\":{}},\"CommissionInfo\":{\"EstimatedOrderQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"EstimatedPrincipalAmount\":{\"lo\":\"220470000\",\"signScale\":13},\"EstimatedCommissionAmount\":{\"signScale\":12}},\"AssetType\":\"MajorAssetType_Equity\",\"TimeInForce\":\"Day\",\"OrderTypeCode\":\"Limit\",\"OrderLegs\":[{\"LegID\":\"#############\",\"LegParentSchwabOrderID\":\"#############\",\"Quantity\":{\"lo\":\"1000000\",\"signScale\":12},\"QuantityUnitCodeType\":\"SharesOrUnits\",\"LeavesQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"BuySellCode\":\"Buy\",\"Security\":{\"SchwabSecurityID\":\"###########\",\"Symbol\":\"AMD\",\"UnderlyingSymbol\":\"AMD\",\"PrimaryExchangeCode\":\"Q\",\"MajorAssetType\":\"MajorAssetType_Equity\",\"PrimaryMarketSymbol\":\"AMD\",\"ShortDescriptionText\":\"ADVANCED MICRO DEVIC\",\"ShortName\":\"ADVANCED MICRO DEVIC\",\"CUSIP\":\"007903107\",\"SEDOL\":\"2007849\",\"ISIN\":\"US0079031078\",\"OptionsSecurityInfo\":{}},\"QuoteOnOrderAcceptance\":{\"Ask\":{\"lo\":\"221230000\",\"signScale\":12},\"AskSize\":{\"lo\":\"200\"},\"Bid\":{\"lo\":\"221180000\",\"signScale\":12},\"BidSize\":{\"lo\":\"200\"},\"QuoteTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"Symbol\":\"AMD\",\"QuoteTypeCode\":\"Mark\",\"Mid\":{\"lo\":\"221205000\",\"signScale\":12},\"SchwabOrderID\":\"#############\"},\"LegClientRequestInfo\":{\"SecurityId\":\"AMD\",\"SecurityIdTypeCd\":\"Symbol\"},\"AccountingRuleCode\":\"Margin\",\"EstimatedNetAmount\":{\"lo\":\"220470000\",\"signScale\":13},\"EstimatedPrincipalAmnt\":{\"lo\":\"220470000\",\"signScale\":13},\"EquityOrderLeg\":{}}],\"OrderCapacityCode\":\"OC_Agency\",\"SettlementType\":\"SettlementType_Regular\",\"Rule80ACode\":73,\"SolicitedCode\":\"Unsolicited\",\"EquityOrder\":{\"TradingSessionCodeOnOrder\":\"REG\"}}}}}}}",
          "seq": 1,
          "key": "Account Activity"
        },
        {
          "1": "########",
          "2": "OrderAccepted",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"OrderAccepted\",\"OrderAcceptedEvent\":{\"EventType\":\"OrderAccepted\",\"CreatedTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"ExpiryTimeStamp\":{\"DateTimeString\":\"2025-12-09\"},\"Status\":\"Open\",\"TradingSessionCodeOnOrderEntry\":\"REG\",\"QuoteOnOrderEntry\":[{\"Ask\":{\"lo\":\"221230000\",\"signScale\":12},\"AskSize\":{\"lo\":\"200\"},\"Bid\":{\"lo\":\"221180000\",\"signScale\":12},\"BidSize\":{\"lo\":\"200\"},\"QuoteTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"Symbol\":\"AMD\",\"QuoteTypeCode\":\"Mark\",\"Mid\":{\"lo\":\"221205000\",\"signScale\":12},\"SchwabOrderID\":\"#############\"}]}}}",
          "seq": 2,
          "key": "Account Activity"
        },
        {
          "1": "########",
          "2": "ExecutionRequested",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"ExecutionRequested\",\"ExecutionRequestedEventRoutedInfo\":{\"EventType\":\"ExecutionRequested\",\"RouteSequenceNumber\":1,\"RouteInfo\":{\"RouteName\":\"HRT_NMS_EQ_F1_z1\",\"RouteSequenceNumber\":1,\"RoutedExecutionTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"Quote\":{\"Ask\":{\"lo\":\"221230000\",\"signScale\":12},\"AskSize\":{\"lo\":\"200\"},\"Bid\":{\"lo\":\"221180000\",\"signScale\":12},\"BidSize\":{\"lo\":\"200\"},\"QuoteTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"Symbol\":\"AMD\",\"QuoteTypeCode\":\"Mark\",\"Mid\":{\"lo\":\"221205000\",\"signScale\":12},\"SchwabOrderID\":\"#############\"},\"RouteRequestedType\":\"New\",\"RoutedQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"RoutedPrice\":{\"lo\":\"220470000\",\"signScale\":12},\"RouteStatus\":\"RouteCreated\",\"ClientOrderID\":\"#############.1\",\"RoutedTime\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"RouteTimeInForce\":\"Day\",\"RouteAcknowledgmentTimeStamp\":{}},\"RouteRequestedBy\":\"RR_Broker\",\"LegId\":\"#############\"}}}",
          "seq": 3,
          "key": "Account Activity"
        }
      ]
    }
  ]
}
# Order Routed
{
  "service": "ACCT_ACTIVITY",
  "timestamp": 0000000000000,
  "command": "SUBS",
  "content": [
    {
      "1": "########",
      "2": "ExecutionRequestCreated",
      "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"ExecutionRequestCreated\",\"ExecutionRequestCreatedEvent\":{\"EventType\":\"ExecutionRequestCreated\",\"LegId\":\"#############\",\"RouteName\":\"HRT_NMS_EQ_F1_Z1\",\"RouteRequestType\":\"New\",\"RouteSequenceNumber\":1,\"RouteRequestedBy\":\"RR_Broker\",\"RouteStatus\":\"RouteFixAcknowledged\",\"SenderCompID\":\"CHASBL01\",\"RoutedTime\":{\"DateTimeString\":\"2025-12-09 14:11:00.00\"},\"ClientOrderID\":\"#############.1\"}}}",
      "seq": 4,
      "key": "Account Activity"
    },
    {
      "1": "########",
      "2": "ExecutionRequestCompleted",
      "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"ExecutionRequestCompleted\",\"ExecutionRequestCompletedEvent\":{\"EventType\":\"ExecutionRequestCompleted\",\"LegId\":\"#############\",\"ResponseType\":\"Accepted\",\"ExchangeOrderID\":\"###################\",\"ExecutionTime\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"RouteSequenceNumber\":1,\"RouteStatus\":\"RouteVenueAccepted\",\"RouteAcknowledgmentTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"ClientOrderID\":\"#############.1\"}}}",
      "seq": 5,
      "key": "Account Activity"
    }
  ]
}

# Order Filled (seperate from AMD order above/below):
{
  "data": [
    {
      "service": "ACCT_ACTIVITY",
      "timestamp": 0000000000000,
      "command": "SUBS",
      "content": [
        {
          "1": "########", 
          "2": "OrderFillCompleted", 
          "3": "{\"SchwabOrderID\":\"########\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"OrderFillCompleted\",\"OrderFillCompletedEventOrderLegQuantityInfo\":{\"EventType\":\"OrderFillCompleted\",\"LegId\":\"########\",\"LegStatus\":\"LegClosed\",\"QuantityInfo\":{\"ExecutionID\":\"20250320-EST-ngOMS-#######\",\"CumulativeQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"LeavesQuantity\":{\"signScale\":12},\"AveragePrice\":{\"lo\":\"213409100\",\"signScale\":12}},\"PriceImprovement\":{\"lo\":\"10900\",\"signScale\":12},\"LegSubStatus\":\"LegSubStatusFilled\",\"ExecutionInfo\":{\"ExecutionSequenceNumber\":1,\"ExecutionId\":\"20250320-EST-ngOMS-########\",\"VenueExecutionID\":\"########\",\"ExecutionQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"ExecutionPrice\":{\"lo\":\"213409100\",\"signScale\":12},\"ExecutionTimeStamp\":{\"DateTimeString\":\"2025-03-20 13:43:45.620\"},\"ExecutionTransType\":\"Fill\",\"ExecutionBroker\":\"CDRG\",\"ExecutionCapacityCode\":\"Agency\",\"RouteName\":\"CES_NMS_F3_J2\",\"RouteSequenceNumber\":1,\"VenuExecutionTimeStamp\":{\"DateTimeString\":\"2025-03-20 13:43:45.576\"},\"ReportingCapacityCode\":\"RC_Agency\",\"PrincipalAmmount\":{\"lo\":\"213410000\",\"signScale\":12},\"ActualChargedCommissionAmount\":{\"signScale\":12},\"AsOfTimeStamp\":{},\"ActualChargedFeesCommissionAndTax\":{\"StateTaxWithholding\":{\"signScale\":12},\"FederalTaxWithholding\":{\"signScale\":12},\"SECFees\":{\"signScale\":12},\"ORF\":{\"signScale\":12},\"FTT\":{\"signScale\":12},\"TaxWithholding1446\":{\"signScale\":12},\"GoodsAndServicesTax\":{\"signScale\":12},\"IOF\":{\"signScale\":12},\"TAF\":{\"signScale\":12},\"CommissionAmount\":{\"signScale\":12}},\"ClientOrderID\":\"#######.#\"},\"OrderInfoForTransactionPosting\":{\"LimitPrice\":{\"lo\":\"213500000\",\"signScale\":12},\"OrderTypeCode\":\"Limit\",\"BuySellCode\":\"Buy\",\"Quantity\":{\"lo\":\"1000000\",\"signScale\":12},\"StopPrice\":{},\"Symbol\":\"AAPL\",\"SchwabSecurityID\":\"1973757747\",\"SolicitedCode\":\"Unsolicited\",\"AccountingRuleCode\":\"Cash\",\"SettlementType\":\"SettlementType_Regular\",\"OrderCreatedUserID\":\"####\",\"OrderCreatedUserType\":\"Venue\",\"ClientProductCode\":\"##\"}}}}"
          "seq": 6, 
          "key": "Account Activity"
        }
      ]
    }
  ]
}

# Cancel order:
{
  "data": [
    {
      "service": "ACCT_ACTIVITY",
      "timestamp": 0000000000000,
      "command": "SUBS",
      "content": [
        {
          "1": "########",
          "2": "CancelAccepted",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"CancelAccepted\",\"CancelAcceptedEvent\":{\"EventType\":\"CancelAccepted\",\"LifecycleSchwabOrderID\":\"#############\",\"PlanSubmitDate\":{\"DateTimeString\":\"2025-12-09\"},\"ClientProductCode\":\"MO\",\"AutoConfirm\":true,\"CancelTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"LegCancelRequestInfoList\":[{\"LegID\":\"#############\",\"IntendedOrderQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"RequestedAmount\":{\"lo\":\"1000000\",\"signScale\":12},\"LegStatus\":\"LegOpen\",\"LegSubStatus\":\"LegSubStatusCancelled\",\"CancelAcceptedTime\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"EventUserID\":\"MYXX\"}],\"CancelRequestType\":\"ClientCancel\"}}}",
          "seq": 6,
          "key": "Account Activity"
        }
      ]
    }
  ]
}
# Routing Cancel Request:
{
  "data": [
    {
      "service": "ACCT_ACTIVITY",
      "timestamp": 1765307505041,
      "command": "SUBS",
      "content": [
        {
          "1": "########",
          "2": "ExecutionRequested",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"ExecutionRequested\",\"ExecutionRequestedEventRoutedInfo\":{\"EventType\":\"ExecutionRequested\",\"RouteSequenceNumber\":2,\"RouteInfo\":{\"RouteName\":\"HRT_NMS_EQ_F1_Z1\",\"RouteSequenceNumber\":2,\"RoutedExecutionTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"Quote\":{\"Ask\":{\"lo\":\"221230000\",\"signScale\":12},\"AskSize\":{\"lo\":\"200\"},\"Bid\":{\"lo\":\"221180000\",\"signScale\":12},\"BidSize\":{\"lo\":\"200\"},\"QuoteTimestamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"Symbol\":\"AMD\",\"QuoteTypeCode\":\"Mark\",\"Mid\":{\"lo\":\"221205000\",\"signScale\":12},\"SchwabOrderID\":\"#############\"},\"RouteRequestedType\":\"Cancel\",\"RoutedQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"RoutedPrice\":{\"lo\":\"220470000\",\"signScale\":12},\"RouteStatus\":\"RouteCreated\",\"ClientOrderID\":\"#############.1\",\"RoutedTime\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"RouteTimeInForce\":\"Day\",\"RouteAcknowledgmentTimeStamp\":{}},\"RouteRequestedBy\":\"RR_Broker\",\"LegId\":\"#############\"}}}",
          "seq": 7,
          "key": "Account Activity"
        },
        {
          "1": "########",
          "2": "ExecutionRequestCompleted",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"ExecutionRequestCompleted\",\"ExecutionRequestCompletedEvent\":{\"EventType\":\"ExecutionRequestCompleted\",\"LegId\":\"#############\",\"ResponseType\":7,\"ExecutionTime\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"RouteSequenceNumber\":2,\"RouteStatus\":8,\"RouteAcknowledgmentTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"ClientOrderID\":\"#############.1\"}}}",
          "seq": 8,
          "key": "Account Activity"
        },
        {
          "1": "########",
          "2": "ExecutionCreated",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"ExecutionCreated\",\"ExecutionCreatedEventExecutionInfo\":{\"EventType\":\"ExecutionCreated\",\"LegId\":\"#############\",\"ExecutionInfo\":{\"ExecutionSequenceNumber\":1,\"ExecutionId\":\"20251209-EST-ngOMS-###########\",\"ExecutionQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"ExecutionTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"ExecutionTransType\":\"UROut\",\"ExecutionCapacityCode\":\"Agency\",\"RouteName\":\"HRT_NMS_EQ_F1_J1\",\"RouteSequenceNumber\":1,\"VenuExecutionTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"CancelType\":\"ClientCancel\",\"ReportingCapacityCode\":\"RC_Agency\",\"AsOfTimeStamp\":{},\"ClientOrderID\":\"#############.1\"},\"AsOfTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"RouteSequenceNumber\":1}}}",
          "seq": 9,
          "key": "Account Activity"
        },
        {
          "1": "########",
          "2": "OrderUROutCompleted",
          "3": "{\"SchwabOrderID\":\"#############\",\"AccountNumber\":\"########\",\"BaseEvent\":{\"EventType\":\"OrderUROutCompleted\",\"OrderUROutCompletedEvent\":{\"EventType\":\"OrderUROutCompleted\",\"LegId\":\"#############\",\"ExecutionId\":\"20251209-EST-ngOMS-###########\",\"LeavesQuantity\":{\"signScale\":12},\"CancelQuantity\":{\"lo\":\"1000000\",\"signScale\":12},\"LegStatus\":\"LegClosed\",\"LegSubStatus\":\"LegSubStatusCancelled\",\"OutCancelType\":\"ClientCancel\",\"VenueExecutionTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"ExecutionTimeStamp\":{\"DateTimeString\":\"2025-12-09 14:11:00.000\"},\"RouteName\":\"HRT_NMS_EQ_F1_Z1\"}}}",
          "seq": 10,
          "key": "Account Activity"
        }
      ]
    }
  ]
}
```
</details>
<details><summary><u>Key Translations</u></summary>
Schwabdev has a translation map for fields, see above.<br>  
"seq": "Sequence"<br>
"key": "Key"<br>
1: "Account"<br>
2: "Message Type"<br> 
3: "Message Data"<br>
</details>
