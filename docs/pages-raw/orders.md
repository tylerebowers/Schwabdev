# Placing Orders

After making a client object (e.g. `client = schwabdev.Client(...)`) you can place orders using the `client.order_place(...)` method.

### Notes

* Orders are currently only supported for equities and options.
* There is a limit of **120 orders per minute** and **4000 orders per day**.

---

### `client.order_place(account_hash, order)`

Places an order on the specified account.

* `account_hash (str)`: Account hash to place the order on.
* `order (dict)`: Order dict to place. Examples are shown below and in the Schwab documentation.

Returns a `requests.Response` object.

**Note**

Get the order ID by checking the headers:

```python
order_id = resp.headers.get('location', '/').split('/')[-1]
```

*If the order is immediately filled, the ID might not be returned.*

---

### `client.order_details(account_hash, order_id)`

Gets details for a specific order.

* `account_hash (str)`: Account hash the order was placed on.
* `order_id (int)`: Order ID to get details for.

Returns a `requests.Response` whose JSON body contains order details.

---

### `client.order_cancel(account_hash, order_id)`

Cancels a specific order.

* `account_hash (str)`: Account hash the order was placed on.
* `order_id (int)`: Order ID to cancel.

Returns a `requests.Response` that is empty if successful.

---

### `client.order_replace(account_hash, orderID, order)`

Replaces a specific order.

* `account_hash (str)`: Account hash the order was placed on.
* `orderID (int)`: Order ID to replace.
* `order (dict)`: Order dict to replace `orderID` with.

Returns a `requests.Response` that is empty if successful.

---

## Order Examples

*Please adjust for your usage.*

### Buy 10 shares of AMD at market price

```python
order = {
    "orderType": "MARKET",
    "session": "NORMAL",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 10,
            "instrument": {
                "symbol": "AMD",
                "assetType": "EQUITY",
            },
        }
    ],
}
```

---

### Buy 4 shares of INTC at limit price $10.00

```python
order = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "price": "10.00",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 4,
            "instrument": {
                "symbol": "INTC",
                "assetType": "EQUITY",
            },
        }
    ],
}
```

---

### Sell 3 options

*Symbol format:* Underlying Symbol (6 chars including spaces) + Expiration (YYMMDD, 6 chars) + Call/Put (1 char) + Strike Price (5+3 = 8 chars)

```python
order = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "price": 1.0,
    "duration": "GOOD_TILL_CANCEL",
    "orderStrategyType": "SINGLE",
    "complexOrderStrategyType": "NONE",
    "orderLegCollection": [
        {
            "instruction": "SELL_TO_OPEN",
            "quantity": 3,
            "instrument": {
                "symbol": "AAPL  240517P00190000",
                "assetType": "OPTION",
            },
        }
    ],
}
```

---

### Buy 3 options

*Symbol format:* Underlying Symbol (6 chars including spaces) + Expiration (YYMMDD, 6 chars) + Call/Put (1 char) + Strike Price (5+3 = 8 chars)

```python
order = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "price": 0.1,
    "duration": "GOOD_TILL_CANCEL",
    "orderStrategyType": "SINGLE",
    "complexOrderStrategyType": "NONE",
    "orderLegCollection": [
        {
            "instruction": "BUY_TO_OPEN",
            "quantity": 3,
            "instrument": {
                "symbol": "AAPL  240517P00190000",
                "assetType": "OPTION",
            },
        }
    ],
}
```

---

### Buy limited vertical put spread

```python
order = {
    "orderType": "NET_DEBIT",
    "session": "NORMAL",
    "price": "0.10",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "orderLegCollection": [
        {
            "instruction": "BUY_TO_OPEN",
            "quantity": 2,
            "instrument": {
                "symbol": "XYZ   240315P00045000",
                "assetType": "OPTION",
            },
        },
        {
            "instruction": "SELL_TO_OPEN",
            "quantity": 2,
            "instrument": {
                "symbol": "XYZ   240315P00043000",
                "assetType": "OPTION",
            },
        },
    ],
}
```

---

### Conditional Order: If 10 shares XYZ filled, then sell 10 shares ABC

```python
order = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "price": "34.97",
    "duration": "DAY",
    "orderStrategyType": "TRIGGER",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 10,
            "instrument": {
                "symbol": "XYZ",
                "assetType": "EQUITY",
            },
        }
    ],
    "childOrderStrategies": [
        {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": "42.03",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": 10,
                    "instrument": {
                        "symbol": "ABC",
                        "assetType": "EQUITY",
                    },
                }
            ],
        }
    ],
}
```

---

### Conditional Order (OCO): If 2 shares XYZ filled, then cancel sell 2 shares ABC

```python
order = {
    "orderStrategyType": "OCO",
    "childOrderStrategies": [
        {
            "orderType": "LIMIT",
            "session": "NORMAL",
            "price": "45.97",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": 2,
                    "instrument": {
                        "symbol": "XYZ",
                        "assetType": "EQUITY",
                    },
                }
            ],
        },
        {
            "orderType": "STOP_LIMIT",
            "session": "NORMAL",
            "price": "37.00",
            "stopPrice": "37.03",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": "SELL",
                    "quantity": 2,
                    "instrument": {
                        "symbol": "ABC",
                        "assetType": "EQUITY",
                    },
                }
            ],
        },
    ],
}
```

---

### Conditional Order: If 5 shares XYZ filled, then sell 5 shares ABC and 5 shares IJK

```python
order = {
    "orderStrategyType": "TRIGGER",
    "session": "NORMAL",
    "duration": "DAY",
    "orderType": "LIMIT",
    "price": 14.97,
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 5,
            "instrument": {
                "assetType": "EQUITY",
                "symbol": "XYZ",
            },
        }
    ],
    "childOrderStrategies": [
        {
            "orderStrategyType": "OCO",
            "childOrderStrategies": [
                {
                    "orderStrategyType": "SINGLE",
                    "session": "NORMAL",
                    "duration": "GOOD_TILL_CANCEL",
                    "orderType": "LIMIT",
                    "price": 15.27,
                    "orderLegCollection": [
                        {
                            "instruction": "SELL",
                            "quantity": 5,
                            "instrument": {
                                "assetType": "EQUITY",
                                "symbol": "ABC",
                            },
                        }
                    ],
                },
                {
                    "orderStrategyType": "SINGLE",
                    "session": "NORMAL",
                    "duration": "GOOD_TILL_CANCEL",
                    "orderType": "STOP",
                    "stopPrice": 11.27,
                    "orderLegCollection": [
                        {
                            "instruction": "SELL",
                            "quantity": 5,
                            "instrument": {
                                "assetType": "EQUITY",
                                "symbol": "IJK",
                            },
                        }
                    ],
                },
            ],
        }
    ],
}
```

---

### Sell Trailing Stop: 10 shares XYZ with a trailing stop offset of 10

```python
order = {
    "complexOrderStrategyType": "NONE",
    "orderType": "TRAILING_STOP",
    "session": "NORMAL",
    "stopPriceLinkBasis": "BID",
    "stopPriceLinkType": "VALUE",
    "stopPriceOffset": 10,
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "orderLegCollection": [
        {
            "instruction": "SELL",
            "quantity": 10,
            "instrument": {
                "symbol": "XYZ",
                "assetType": "EQUITY",
            },
        }
    ],
}
```

---

### Iron Condor

```python
order = {
    "orderStrategyType": "SINGLE",
    "orderType": "NET_CREDIT",
    "price": price,
    "orderLegCollection": [
        {
            "instruction": "SELL_TO_OPEN",
            "quantity": quantity,
            "instrument": {
                "assetType": "OPTION",
                "symbol": short_call_symbol,
            },
        },
        {
            "instruction": "BUY_TO_OPEN",
            "quantity": quantity,
            "instrument": {
                "assetType": "OPTION",
                "symbol": long_call_symbol,
            },
        },
        {
            "instruction": "SELL_TO_OPEN",
            "quantity": quantity,
            "instrument": {
                "assetType": "OPTION",
                "symbol": short_put_symbol,
            },
        },
        {
            "instruction": "BUY_TO_OPEN",
            "quantity": quantity,
            "instrument": {
                "assetType": "OPTION",
                "symbol": long_put_symbol,
            },
        },
    ],
    "complexOrderStrategyType": "CUSTOM",
    "duration": "DAY",
    "session": "NORMAL",
}
```

