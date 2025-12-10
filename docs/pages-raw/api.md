# Client API access

Examples can be found in <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/">`docs/examples/`</a>.

After making a client object i.e. `client = schwabdev.Client(...)` we are free to make api calls or start a stream. Below is a list of all possible calls that can be made with the api. You can also reference the <a target="_blank" href="https://developer.schwab.com/products/trader-api--individual">Schwab documentation</a>, each call is named similarly.

### Notes:

* In order to use all api calls you must have both "APIs" added to your app, both "Accounts and Trading Production" and "Market Data Production".
* After making a call you will receive a response object, to get the data you can call .json(), however it is best to check if the response is good by calling .ok which returns a boolean of True if the response code is in the 200 code range.
* In this documentation, parameters with ...=None are optional and can be left blank.
* All time/dates can either be strings or datetime objects.
* All lists can be passed as comma strings "a,b,c" or lists of strings ["a", "b", "c"].
* A maximum of 120 api requests per minute can be made, do **NOT** use api endpoints in a loop to get market data, use the streaming service instead.

## API Calls

---

### `client.linked_accounts()`
Returns a `requests.Response` whose JSON body is a list of dicts containing account numbers and hashes. The hash (`hashValue`) is used in other API calls to specify which account to operate on.
<details open><summary><u>Example</u></summary>

```python
> client.linked_accounts().json()
[{'accountNumber': 'XXXXXXXX', 'hashValue': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX'}]
```
</details>

---
### `client.account_details_all(fields=None)`

Returns a `requests.Response` whose JSON body is a list of dicts containing details for all linked accounts.

- `fields (str | None)`: Optional. Additional fields to include.  
  - `"positions"` – include current positions for each account.

<details><summary><u>Example</u></summary>

```python
> client.account_details_all().json()
[{'securitiesAccount':
           {'type': 'MARGIN',
            'accountNumber': 'XXXXXXXX',
            'roundTrips': 0,
            'isDayTrader': False,
            'isClosingOnlyRestricted': False,
            'pfcbFlag': False,
            'initialBalances': {'accruedInterest': 0.0,
                                'availableFundsNonMarginableTrade': 0.0,
                                'bondValue': 0.0,
                                'buyingPower': 0.0,
                                'cashBalance': 0.0,
                                'cashAvailableForTrading': 0.0,
                                'cashReceipts': 0.0,
                                'dayTradingBuyingPower': 0.0,
                                'dayTradingBuyingPowerCall': 0.0,
                                'dayTradingEquityCall': 0.0,
                                'equity': 0.0,
                                'equityPercentage': 0.0,
                                'liquidationValue': 0.0,
                                'longMarginValue': 0.0,
                                'longOptionMarketValue': 0.0,
                                'longStockValue': 0.0,
                                'maintenanceCall': 0.0,
                                'maintenanceRequirement': 0.0,
                                'margin': 0.0,
                                'marginEquity': 0.0,
                                'moneyMarketFund': 0.0,
                                'mutualFundValue': 0.0,
                                'regTCall': 0.0,
                                'shortMarginValue': 0.0,
                                'shortOptionMarketValue': 0.0,
                                'shortStockValue': 0.0,
                                'totalCash': 0.0,
                                'isInCall': False,
                                'pendingDeposits': 0.0,
                                'marginBalance': 0.0,
                                'shortBalance': 0.0,
                                'accountValue': 0.0},
            'currentBalances': {'accruedInterest': 0.0,
                                'cashBalance': 0.0,
                                'cashReceipts': 0.0,
                                'longOptionMarketValue': 0.0,
                                'liquidationValue': 0.0,
                                'longMarketValue': 0.0,
                                'moneyMarketFund': 0.0,
                                'savings': 0.0,
                                'shortMarketValue': 0.0,
                                'pendingDeposits': 0.0,
                                'mutualFundValue': 0.0,
                                'bondValue': 0.0,
                                'shortOptionMarketValue': 0.0,
                                'availableFunds': 0.0,
                                'availableFundsNonMarginableTrade': 0.0,
                                'buyingPower': 0.0,
                                'buyingPowerNonMarginableTrade': 0.0,
                                'dayTradingBuyingPower': 0.0,
                                'equity': 0.0,
                                'equityPercentage': 0.0,
                                'longMarginValue': 0.0,
                                'maintenanceCall': 0.0,
                                'maintenanceRequirement': 0.0,
                                'marginBalance': 0.0,
                                'regTCall': 0.0,
                                'shortBalance': 0.0,
                                'shortMarginValue': 0.0,
                                'sma': 0.0},
            'projectedBalances': {'availableFunds': 0.0,
                                  'availableFundsNonMarginableTrade': 0.0,
                                  'buyingPower': 0.0,
                                  'dayTradingBuyingPower': 0.0,
                                  'dayTradingBuyingPowerCall': 0.0,
                                  'maintenanceCall': 0.0,
                                  'regTCall': 0.0,
                                  'isInCall': False,
                                  'stockBuyingPower': 0.0}},
       'aggregatedBalance': {'currentLiquidationValue': 0.0,
                             'liquidationValue': 0.0}}]
```
If the parameter `fields="positions"` is set then each account will have a `positions` field with a list of `position` objects shown here:

```python
[{'shortQuantity': 0.0,
  'averagePrice': 0.0,
  'currentDayProfitLoss': 0.0,
  'currentDayProfitLossPercentage': 0.0,
  'longQuantity': 0.0,
  'settledLongQuantity': 0.0,
  'settledShortQuantity': 0.0,
  'instrument': {'assetType': 'XXXXXX',
                 'cusip': 'XXXXXXXXX',
                 'symbol': 'XX',
                 'netChange': 0.0},
  'marketValue': 0.0,
  'maintenanceRequirement': 0.0,
  'averageLongPrice': 0.0,
  'taxLotAverageLongPrice': 0.0,
  'longOpenProfitLoss': 0.0,
  'previousSessionLongQuantity': 0.0,
  'currentDayCost': 0.0}, ...]
(Truncated)
```
</details>

---
### `client.account_details(account_hash, fields=None)`
Returns a `requests.Response` whose JSON body is a dicts containing details for the account_hash specified.

- `account_hash (str)`: Account hash to get details of.
- `fields (str | None)`: Optional. Additional fields to include.  
  - `"positions"` – include current positions for each account.

<details><summary><u>Example</u></summary>

```python
> client.account_details(XXXX...XXX).json()
{'securitiesAccount':
           {'type': 'MARGIN',
            'accountNumber': 'XXXXXXXX',
            'roundTrips': 0,
            'isDayTrader': False,
            'isClosingOnlyRestricted': False,
            'pfcbFlag': False,
            'initialBalances': {'accruedInterest': 0.0,
                                'availableFundsNonMarginableTrade': 0.0,
                                'bondValue': 0.0,
                                'buyingPower': 0.0,
                                'cashBalance': 0.0,
                                'cashAvailableForTrading': 0.0,
                                'cashReceipts': 0.0,
                                'dayTradingBuyingPower': 0.0,
                                'dayTradingBuyingPowerCall': 0.0,
                                'dayTradingEquityCall': 0.0,
                                'equity': 0.0,
                                'equityPercentage': 0.0,
                                'liquidationValue': 0.0,
                                'longMarginValue': 0.0,
                                'longOptionMarketValue': 0.0,
                                'longStockValue': 0.0,
                                'maintenanceCall': 0.0,
                                'maintenanceRequirement': 0.0,
                                'margin': 0.0,
                                'marginEquity': 0.0,
                                'moneyMarketFund': 0.0,
                                'mutualFundValue': 0.0,
                                'regTCall': 0.0,
                                'shortMarginValue': 0.0,
                                'shortOptionMarketValue': 0.0,
                                'shortStockValue': 0.0,
                                'totalCash': 0.0,
                                'isInCall': False,
                                'pendingDeposits': 0.0,
                                'marginBalance': 0.0,
                                'shortBalance': 0.0,
                                'accountValue': 0.0},
            'currentBalances': {'accruedInterest': 0.0,
                                'cashBalance': 0.0,
                                'cashReceipts': 0.0,
                                'longOptionMarketValue': 0.0,
                                'liquidationValue': 0.0,
                                'longMarketValue': 0.0,
                                'moneyMarketFund': 0.0,
                                'savings': 0.0,
                                'shortMarketValue': 0.0,
                                'pendingDeposits': 0.0,
                                'mutualFundValue': 0.0,
                                'bondValue': 0.0,
                                'shortOptionMarketValue': 0.0,
                                'availableFunds': 0.0,
                                'availableFundsNonMarginableTrade': 0.0,
                                'buyingPower': 0.0,
                                'buyingPowerNonMarginableTrade': 0.0,
                                'dayTradingBuyingPower': 0.0,
                                'equity': 0.0,
                                'equityPercentage': 0.0,
                                'longMarginValue': 0.0,
                                'maintenanceCall': 0.0,
                                'maintenanceRequirement': 0.0,
                                'marginBalance': 0.0,
                                'regTCall': 0.0,
                                'shortBalance': 0.0,
                                'shortMarginValue': 0.0,
                                'sma': 0.0},
            'projectedBalances': {'availableFunds': 0.0,
                                  'availableFundsNonMarginableTrade': 0.0,
                                  'buyingPower': 0.0,
                                  'dayTradingBuyingPower': 0.0,
                                  'dayTradingBuyingPowerCall': 0.0,
                                  'maintenanceCall': 0.0,
                                  'regTCall': 0.0,
                                  'isInCall': False,
                                  'stockBuyingPower': 0.0}},
       'aggregatedBalance': {'currentLiquidationValue': 0.0,
                             'liquidationValue': 0.0}}
```
If the parameter `fields="positions"` is set then each account will have a `positions` field with a list of `position` objects shown here:
(Truncated)

```python
[{'shortQuantity': 0.0,
  'averagePrice': 0.0,
  'currentDayProfitLoss': 0.0,
  'currentDayProfitLossPercentage': 0.0,
  'longQuantity': 0.0,
  'settledLongQuantity': 0.0,
  'settledShortQuantity': 0.0,
  'instrument': {'assetType': 'XXXXXX',
                 'cusip': 'XXXXXXXXX',
                 'symbol': 'XX',
                 'netChange': 0.0},
  'marketValue': 0.0,
  'maintenanceRequirement': 0.0,
  'averageLongPrice': 0.0,
  'taxLotAverageLongPrice': 0.0,
  'longOpenProfitLoss': 0.0,
  'previousSessionLongQuantity': 0.0,
  'currentDayCost': 0.0}, ...]
```
</details>

---
### `client.account_orders(accountHash, fromEnteredTime, toEnteredTime, maxResults=None, status=None)`
Returns a `requests.Response` whose JSON body is a list of order dicts for the given account within the specified time range, optionally filtered by status.

* `account_hash (str)`: Account hash to get orders for.
* `from_entered_time (datetime | str)`: Start of the date range. Use a `datetime` object or a string in the format `yyyy-MM-dd'T'HH:mm:ss.SSSZ`.
* `to_entered_time (datetime | str)`: End of the date range. Use a `datetime` object or a string in the format `yyyy-MM-dd'T'HH:mm:ss.SSSZ`.
* `max_results (int | None)`: Maximum number of orders to return (default `3000`).
* `status (str | None)`: Optional status filter. One of:
  `"AWAITING_PARENT_ORDER"`, `"AWAITING_CONDITION"`, `"AWAITING_STOP_CONDITION"`, `"AWAITING_MANUAL_REVIEW"`, `"ACCEPTED"`, `"AWAITING_UR_OUT"`, `"PENDING_ACTIVATION"`, `"QUEUED"`, `"WORKING"`, `"REJECTED"`, `"PENDING_CANCEL"`, `"CANCELED"`, `"PENDING_REPLACE"`, `"REPLACED"`, `"FILLED"`, `"EXPIRED"`, `"NEW"`, `"AWAITING_RELEASE_TIME"`, `"PENDING_ACKNOWLEDGEMENT"`, `"PENDING_RECALL"`, `"UNKNOWN"`.

<details><summary><u>Example</u></summary>

(Truncated)
```python
[{'session': 'NORMAL',
  'duration': 'GOOD_TILL_CANCEL',
  'orderType': 'LIMIT',
  'cancelTime': 'YYYY-MM-DDT00:00:00+0000',
  'complexOrderStrategyType': 'NONE',
  'quantity': 0.0,
  'filledQuantity': 0.0,
  'remainingQuantity': 0.0,
  'requestedDestination': 'AUTO',
  'destinationLinkName': 'SOHO',
  'price': 0.0,
  'orderLegCollection': [{'orderLegType': 'EQUITY',
                          'legId': 1,
                          'instrument': {'assetType': 'EQUITY',
                                         'cusip': 'XXXXXXXXX',
                                         'symbol': 'XXX',
                                         'instrumentId': XXXXXXXX},
                          'instruction': 'BUY',
                          'positionEffect': 'OPENING',
                          'quantity': 0.0}],
  'orderStrategyType': 'SINGLE',
  'orderId': XXXXXXXXXXXXX,
  'cancelable': True,
  'editable': True,
  'status': 'PENDING_ACTIVATION',
  'enteredTime': 'YYYY-MM-DDT00:00:00+0000',
  'accountNumber': XXXXXXXX},
... ]
```
</details>

---
### `client.place_order(account_hash, order)`
Places an order for the account specified by account_hash. Returns Order ID in the headers (`order_id = resp.headers.get('location', '/').split('/')[-1]`), unless the order was instantly filled.

* `account_hash (str)`: Account hash to place the order on.
* `order (dict)`: Order payload. See `orders.md` and the Schwab documentation for examples.

<details><summary><u>Example</u></summary>

```python
order = {"orderType": "LIMIT",
            "session": "NORMAL",
            "duration": "DAY",
            "orderStrategyType": "SINGLE",
            "price": '10.00',
            "orderLegCollection": [
                {"instruction": "BUY",
                "quantity": 1,
                "instrument": {"symbol": "INTC",
                                "assetType": "EQUITY"
                                }
                }
            ]
        }
resp = client.place_order(account_hash, order)
order_id = resp.headers.get('location', '/').split('/')[-1]
```

</details>

---

### `client.order_details(account_hash, order_id)`
Returns a `requests.Response` whose JSON body is a dict containing details for a specific order.

* `account_hash (str)`: Account hash that the order was placed on.
* `order_id (int)`: Order ID to get details for.
<details><summary><u>Example</u></summary>

```python
> client.order_details(account_hash, order_id)
{
    "session":"NORMAL",
    "duration":"DAY",
    "orderType":"LIMIT",
    "complexOrderStrategyType":"NONE",
    "quantity":1.0,
    "filledQuantity":0.0,
    "remainingQuantity":0.0,
    "requestedDestination":"AUTO",
    "destinationLinkName":"AutoRoute",
    "price":10.0,
    "orderLegCollection":[
        {
            "orderLegType":"EQUITY",
            "legId":1,
            "instrument":{
                "assetType":"EQUITY",
                "cusip":"XXXXXXXXX",
                "symbol":"INTC",
                "instrumentId":0000000
            },
            "instruction":"BUY",
            "positionEffect":"OPENING",
            "quantity":1.0
        }
    ],
    "orderStrategyType":"SINGLE",
    "orderId":0000000000000,
    "cancelable":false,
    "editable":false,
    "status":"CANCELED",
    "enteredTime":"0000-00-00T00:00:00+0000",
    "closeTime":"0000-00-00T00:00:00+00000",
    "tag":"XXXXXXXXXXXXXXXX",
    "accountNumber":00000000,
    "orderActivityCollection":[
        {
            "activityType":"EXECUTION",
            "activityId":000000000000,
            "executionType":"CANCELED",
            "quantity":1.0,
            "orderRemainingQuantity":0.0,
            "executionLegs":[
                {
                    "legId":1,
                    "quantity":1.0,
                    "mismarkedQuantity":0.0,
                    "price":0.0,
                    "time":"0000-00-00T00:00:00+0000",
                    "instrumentId":0000000
                }
            ]
        }
    ]
}
```
</details>

---
### `client.cancel_order(account_hash, order_id)`
Cancels a specific order and returns a `requests.Response`. The response is typically empty if successful, check the code to know for sure.

* `account_hash (str)`: Account hash that the order was placed on.
* `order_id (int)`: Order ID to cancel.

<details><summary><u>Example</u></summary>

```python
> client.cancel_order(account_hash, order_id)
<requests.Response [200]>
```
</details>

---
### `client.replace_order(account_hash, orderID, order)`
Replaces an existing order with a new order definition. Returns a `requests.Response`, check the code to know if successful.

* `account_hash (str)`: Account hash that the original order was placed on.
* `order_id (int)`: Order ID to replace.
* `order (dict)`: New order payload to replace the existing order with.
<details><summary><u>Example</u></summary>

```python
> client.replace_order(account_hash, order_id, new_order)
<requests.Response [200]>
```
</details>

---
### `client.account_orders_all(fromEnteredTime, toEnteredTime, maxResults=None, status=None)`
Returns a `requests.Response` whose JSON body is a list of order dicts for **all linked accounts** within the specified time range, optionally filtered by status.

* `from_entered_time (datetime | str)`: Start of the date range. Use a `datetime` object or a string in the format `yyyy-MM-dd'T'HH:mm:ss.SSSZ`.
* `to_entered_time (datetime | str)`: End of the date range. Use a `datetime` object or a string in the format `yyyy-MM-dd'T'HH:mm:ss.SSSZ`.
* `max_results (int | None)`: Maximum number of orders to return (default `3000`).
* `status (str | None)`: Optional status filter. One of:
  `"AWAITING_PARENT_ORDER"`, `"AWAITING_CONDITION"`, `"AWAITING_STOP_CONDITION"`, `"AWAITING_MANUAL_REVIEW"`, `"ACCEPTED"`, `"AWAITING_UR_OUT"`, `"PENDING_ACTIVATION"`, `"QUEUED"`, `"WORKING"`, `"REJECTED"`, `"PENDING_CANCEL"`, `"CANCELED"`, `"PENDING_REPLACE"`, `"REPLACED"`, `"FILLED"`, `"EXPIRED"`, `"NEW"`, `"AWAITING_RELEASE_TIME"`, `"PENDING_ACKNOWLEDGEMENT"`, `"PENDING_RECALL"`, `"UNKNOWN"`.

<details><summary><u>Example</u></summary>

(Truncated)
```python
[{'session': 'NORMAL',
  'duration': 'GOOD_TILL_CANCEL',
  'orderType': 'LIMIT',
  'cancelTime': 'YYYY-MM-DDT00:00:00+0000',
  'complexOrderStrategyType': 'NONE',
  'quantity': 0.0,
  'filledQuantity': 0.0,
  'remainingQuantity': 0.0,
  'requestedDestination': 'AUTO',
  'destinationLinkName': 'SOHO',
  'price': 0.0,
  'orderLegCollection': [{'orderLegType': 'EQUITY',
                          'legId': 1,
                          'instrument': {'assetType': 'EQUITY',
                                         'cusip': 'XXXXXXXXX',
                                         'symbol': 'XXX',
                                         'instrumentId': XXXXXXXX},
                          'instruction': 'BUY',
                          'positionEffect': 'OPENING',
                          'quantity': 0.0}],
  'orderStrategyType': 'SINGLE',
  'orderId': XXXXXXXXXXXXX,
  'cancelable': True,
  'editable': True,
  'status': 'PENDING_ACTIVATION',
  'enteredTime': 'YYYY-MM-DDT00:00:00+0000',
  'accountNumber': XXXXXXXX},
... ]
```
</details>

---
### `client.preview_order(account_hash, order)`
Returns a `requests.Response` representing a preview of the order (fees, validation, balances, etc) without actually placing it.

* `account_hash (str)`: Account hash to preview the order on.
* `order (dict)`: Order payload to preview. See `orders.md` and the Schwab documentation for examples.

<details><summary><u>Example</u></summary>

```python
> client.preview_order(account_hash, orderObject)
{
    "orderId":0,
    "orderStrategy":{
        "accountNumber":"XXXXXXXX",
        "advancedOrderType":"NONE",
        "closeTime":"2025-12-04T01:21:21+0000",
        "enteredTime":"2025-12-04T01:21:21+0000",
        "orderBalance":{
            "orderValue":10.0,
            "projectedAvailableFund":0.0,
            "projectedBuyingPower":0.0,
            "projectedCommission":0.0
        },
        "orderStrategyType":"SINGLE",
        "orderVersion":1,
        "session":"NORMAL",
        "status":"REJECTED",
        "discretionary":false,
        "duration":"DAY",
        "filledQuantity":0.0,
        "orderType":"LIMIT",
        "orderValue":10.0,
        "price":10.0,
        "quantity":1.0,
        "remainingQuantity":0.0,
        "sellNonMarginableFirst":false,
        "strategy":"NONE",
        "amountIndicator":"SHARES",
        "orderLegs":[
            {
                "askPrice":217.11,
                "bidPrice":217.01,
                "lastPrice":217.6,
                "markPrice":217.02,
                "projectedCommission":0.0,
                "finalSymbol":"AMD",
                "legId":1,
                "assetType":"EQUITY",
                "instruction":"BUY",
                "positionEffect":"OPENING",
                "instrument":{
                    "assetType":"EQUITY",
                    "symbol":"AMD"
                }
            }
        ]
    },
    "orderValidationResult":{
        "rejects":[
            {
                "activityMessage":"Your limit price is significantly away from the current market price. Please adjust your order.",
                "originalSeverity":"REJECT"
            }
        ]
    },
    "commissionAndFee":{
        "commission":{
            "commissionLegs":[
                {
                    "commissionValues":[
                        {
                            "value":0.0,
                            "type":"BASE_CHARGE"
                        },
                        {
                            "value":0.0,
                            "type":"COMMISSION"
                        }
                    ]
                }
            ]
        },
        "fee":{
            "feeLegs":[
                {
                    "feeValues":[
                        {
                            "value":0.0,
                            "type":"SEC_FEE"
                        },
                        {
                            "value":0.0,
                            "type":"OPT_REG_FEE"
                        },
                        {
                            "value":0.0,
                            "type":"TAF_FEE"
                        }
                    ]
                }
            ]
        },
        "trueCommission":{
            "commissionLegs":[
                {
                    "commissionValues":[
                        {
                            "value":0.0,
                            "type":"BASE_CHARGE"
                        },
                        {
                            "value":0.0,
                            "type":"COMMISSION"
                        }
                    ]
                }
            ]
        }
    }
}
```
</details>

---
### `client.transactions(accountHash, startDate, endDate, types, symbol=None)`
Returns a `requests.Response` whose JSON body is a list of transaction dicts for the given account.

* `account_hash (str)`: Account hash to get transactions from.
* `start_date (datetime | str)`: Start date; use a `datetime` object or a string in the format `yyyy-MM-dd'T'HH:mm:ss.SSSZ`.
* `end_date (datetime | str)`: End date; use a `datetime` object or a string in the format `yyyy-MM-dd'T'HH:mm:ss.SSSZ`.
* `types (list | str)`: Transaction types to include. One or more of:
  `"TRADE"`, `"RECEIVE_AND_DELIVER"`, `"DIVIDEND_OR_INTEREST"`, `"ACH_RECEIPT"`, `"ACH_DISBURSEMENT"`, `"CASH_RECEIPT"`, `"CASH_DISBURSEMENT"`, `"ELECTRONIC_FUND"`, `"WIRE_OUT"`, `"WIRE_IN"`, `"JOURNAL"`, `"MEMORANDUM"`, `"MARGIN_CALL"`, `"MONEY_MARKET"`, `"SMA_ADJUSTMENT"`.
* `symbol (str | None)`: Optional symbol to filter by. Special symbols (like `"/"` or `"$"`) must be URL-encoded.

<details><summary><u>Return Example</u></summary>

```python
[{'activityId': XXXXXXXXXXX,
  'time': 'YYYY-MM-DDT00:00:00+0000',
  'accountNumber': 'XXXXXXXX',
  'type': 'TRADE', 'status': 'VALID',
  'subAccount': 'MARGIN',
  'tradeDate': 'YYYY-MM-DDT00:00:00+0000',
  'positionId': XXXXXXXXXX,
  'orderId': XXXXXXXXXXXXX,
  'netAmount': 0.0,
  'transferItems': [{'instrument': {'assetType': 'CURRENCY',
                                    'status': 'ACTIVE',
                                    'symbol': 'CURRENCY_USD',
                                    'description': 'USD currency',
                                    'instrumentId': 1,
                                    'closingPrice': 0.0},
                     'amount': 0.0,
                     'cost': 0.0,
                     'feeType': 'COMMISSION'},
                    {'instrument': {'assetType': 'CURRENCY',
                                    'status': 'ACTIVE',
                                    'symbol': 'CURRENCY_USD',
                                    'description': 'USD currency',
                                    'instrumentId': 1,
                                    'closingPrice': 0.0},
                     'amount': 0.0,
                     'cost': 0.0,
                     'feeType': 'SEC_FEE'},
                    {'instrument': {'assetType': 'CURRENCY',
                                    'status': 'ACTIVE',
                                    'symbol': 'CURRENCY_USD',
                                    'description': 'USD currency',
                                    'instrumentId': 1,
                                    'closingPrice': 0.0},
                     'amount': 0.0,
                     'cost': 0.0,
                     'feeType': 'OPT_REG_FEE'},
                    {'instrument': {'assetType': 'CURRENCY',
                                    'status': 'ACTIVE',
                                    'symbol': 'CURRENCY_USD',
                                    'description': 'USD currency',
                                    'instrumentId': 1,
                                    'closingPrice': 0.0},
                     'amount': 0.0, 'cost': 0.0,
                     'feeType': 'TAF_FEE'},
                    {'instrument': {'assetType': 'EQUITY',
                                    'status': 'ACTIVE',
                                    'symbol': 'NET',
                                    'instrumentId': XXXXXXXX,
                                    'closingPrice': 0.0,
                                    'type': 'COMMON_STOCK'},
                     'amount': 0.0,
                     'cost': 0.0,
                     'price': 0.0,
                     'positionEffect': 'CLOSING'}]}, ... ]
```
</details>


---
### `client.transaction_details(account_hash, transactionId)`
Returns a `requests.Response` whose JSON body contains details for a specific transaction.

* `account_hash (str)`: Account hash to get the transaction from.
* `transaction_id (str)`: Transaction ID to get details of.

<details><summary><u>Return Example</u></summary>
No example available.
</details>

---
### `client.preferences()`
Returns a `requests.Response` whose JSON body contains user preferences for accounts, including streaming configuration.
<details><summary><u>Example</u></summary>

```python
> client.preferences().json()
{'accounts': [{'accountNumber': 'XXXXXXXX',
               'primaryAccount': True,
               'type': 'BROKERAGE',
               'nickName': 'Individual',
               'displayAcctId': '...XXX',
               'autoPositionEffect': True,
               'accountColor': 'Green'}],
 'streamerInfo': [{'streamerSocketUrl': 'wss://streamer-api.schwab.com/ws',
                   'schwabClientCustomerId': 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX',
                   'schwabClientCorrelId': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX',
                   'schwabClientChannel': 'N9',
                   'schwabClientFunctionId': 'APIAPP'}],
 'offers': [{'level2Permissions': True,
             'mktDataPermission': 'NP'}]}
```

</details>

---
### `client.quotes(symbols=None, fields=None, indicative=False)`
Returns a `requests.Response` whose JSON body is a dict of quote data keyed by symbol.

* `symbols (list | str | None)`: Symbols to get quotes for, e.g. `["AAPL", "AMD"]` or `"AAPL,AMD"`.
* `fields (str | None)`: Fields to request. One of `"all"` (default), `"quote"`, `"fundamental"`.
* `indicative (bool)`: If `True`, return indicative quotes instead of tradable quotes (default `False`).

<details><summary><u>Example</u></summary>

```python
> client.quotes(symbols=["AAPL", "AMD"]).json()
{
   "AAPL": {
       "assetMainType": "EQUITY",
       "assetSubType": "COE",
       "quoteType": "NBBO",
       "realtime": True,
       "ssid": 1973757747,
       "symbol": "AAPL",
       "fundamental": {
           "avg10DaysVolume": 37498265.0,
           "avg1YearVolume": 58820585.0,
           "declarationDate": "2024-08-01T04:00:00Z",
           "divAmount": 1.0,
           "divExDate": "2024-08-12T04:00:00Z",
           "divFreq": 4,
           "divPayAmount": 0.25,
           "divPayDate": "2024-08-15T04:00:00Z",
           "divYield": 0.43144,
           "eps": 6.13,
           "fundLeverageFactor": 0.0,
           "lastEarningsDate": "2024-08-01T04:00:00Z",
           "nextDivExDate": "2024-11-12T05:00:00Z",
           "nextDivPayDate": "2024-11-15T05:00:00Z",
           "peRatio": 35.35277,
       },
       "quote": {
           "52WeekHigh": 237.49,
           "52WeekLow": 164.075,
           "askMICId": "ARCX",
           "askPrice": 234.88,
           "askSize": 1,
           "askTime": 1729295935436,
           "bidMICId": "ARCX",
           "bidPrice": 234.86,
           "bidSize": 2,
           "bidTime": 1729295935436,
           "closePrice": 232.15,
           "highPrice": 236.18,
           "lastMICId": "ARCX",
           "lastPrice": 234.87,
           "lastSize": 10,
           "lowPrice": 234.01,
           "mark": 234.88,
           "markChange": 2.73,
           "markPercentChange": 1.17596382,
           "netChange": 2.72,
           "netPercentChange": 1.17165626,
           "openPrice": 236.18,
           "postMarketChange": -0.13,
           "postMarketPercentChange": -0.05531915,
           "quoteTime": 1729295935436,
           "securityStatus": "Normal",
           "totalVolume": 46430718,
           "tradeTime": 1729295935436,
       },
       "reference": {
           "cusip": "037833100",
           "description": "APPLE INC",
           "exchange": "Q",
           "exchangeName": "NASDAQ",
           "isHardToBorrow": False,
           "isShortable": True,
           "htbQuantity": 9188513,
           "htbRate": 0.0,
       },
       "regular": {
           "regularMarketLastPrice": 235.0,
           "regularMarketLastSize": 4794536,
           "regularMarketNetChange": 2.85,
           "regularMarketPercentChange": 1.22765453,
           "regularMarketTradeTime": 1729281600171,
       },
   },
   "AMD": {
       "assetMainType": "EQUITY",
       "assetSubType": "COE",
       "quoteType": "NBBO",
       "realtime": True,
       "ssid": 1449199007,
       "symbol": "AMD",
       "fundamental": {
           "avg10DaysVolume": 41154190.0,
           "avg1YearVolume": 57606227.0,
           "divAmount": 0.0,
           "divFreq": 0,
           "divPayAmount": 0.0,
           "divYield": 0.0,
           "eps": 0.52912,
           "fundLeverageFactor": 0.0,
           "lastEarningsDate": "2024-07-30T04:00:00Z",
           "peRatio": 187.19749,
       },
       "quote": {
           "52WeekHigh": 227.3,
           "52WeekLow": 93.115,
           "askMICId": "ARCX",
           "askPrice": 155.82,
           "askSize": 5,
           "askTime": 1729295942857,
           "bidMICId": "ARCX",
           "bidPrice": 155.8,
           "bidSize": 1,
           "bidTime": 1729295942857,
           "closePrice": 156.25,
           "highPrice": 158.01,
           "lastMICId": "ARCX",
           "lastPrice": 155.82,
           "lastSize": 2,
           "lowPrice": 155.56,
           "mark": 155.82,
           "markChange": -0.43,
           "markPercentChange": -0.2752,
           "netChange": -0.43,
           "netPercentChange": -0.2752,
           "openPrice": 157.41,
           "postMarketChange": -0.15,
           "postMarketPercentChange": -0.09617234,
           "quoteTime": 1729295942857,
           "securityStatus": "Normal",
           "totalVolume": 23821452,
           "tradeTime": 1729295948896,
       },
       "reference": {
           "cusip": "007903107",
           "description": "Advanced Micro Devic",
           "exchange": "Q",
           "exchangeName": "NASDAQ",
           "isHardToBorrow": False,
           "isShortable": True,
           "htbQuantity": 24302587,
           "htbRate": 0.0,
       },
       "regular": {
           "regularMarketLastPrice": 155.97,
           "regularMarketLastSize": 1471466,
           "regularMarketNetChange": -0.28,
           "regularMarketPercentChange": -0.1792,
           "regularMarketTradeTime": 1729281600213,
       },
   },
}
```

</details>

---
### `client.quote(symbol_id, fields=None)`
Returns a `requests.Response` whose JSON body is a dict containing quote data for a single symbol.

* `symbol_id (str)`: Symbol to quote, e.g. `"AAPL"` (for futures, use `client.quotes(...)`).
* `fields (str | None)`: Fields to request. One of `"all"` (default), `"quote"`, `"fundamental"`.

<details><summary><u>Example</u></summary>

```python
> client.quote("INTC").json()
{
   "INTC": {
       "assetMainType": "EQUITY",
       "assetSubType": "COE",
       "quoteType": "NBBO",
       "realtime": True,
       "ssid": 1854729529,
       "symbol": "INTC",
       "fundamental": {
           "avg10DaysVolume": 51268766.0,
           "avg1YearVolume": 55187560.0,
           "declarationDate": "2024-08-01T04:00:00Z",
           "divAmount": 0.0,
           "divExDate": "2024-08-07T04:00:00Z",
           "divFreq": 4,
           "divPayAmount": 0.125,
           "divPayDate": "2024-09-01T04:00:00Z",
           "divYield": 0.0,
           "eps": 0.4,
           "fundLeverageFactor": 0.0,
           "lastEarningsDate": "2024-08-01T04:00:00Z",
           "nextDivExDate": "2024-11-07T05:00:00Z",
           "nextDivPayDate": "2024-12-02T05:00:00Z",
           "peRatio": 97.67989,
       },
       "quote": {
           "52WeekHigh": 51.28,
           "52WeekLow": 18.51,
           "askMICId": "ARCX",
           "askPrice": 22.75,
           "askSize": 11,
           "askTime": 1729295936452,
           "bidMICId": "ARCX",
           "bidPrice": 22.73,
           "bidSize": 60,
           "bidTime": 1729295936452,
           "closePrice": 22.44,
           "highPrice": 22.82,
           "lastMICId": "XADF",
           "lastPrice": 22.74,
           "lastSize": 100,
           "lowPrice": 22.5,
           "mark": 22.75,
           "markChange": 0.31,
           "markPercentChange": 1.38146168,
           "netChange": 0.3,
           "netPercentChange": 1.3368984,
           "openPrice": 22.61,
           "postMarketChange": -0.03,
           "postMarketPercentChange": -0.13175231,
           "quoteTime": 1729295936452,
           "securityStatus": "Normal",
           "totalVolume": 39966293,
           "tradeTime": 1729295940365,
       },
       "reference": {
           "cusip": "458140100",
           "description": "INTEL CORP",
           "exchange": "Q",
           "exchangeName": "NASDAQ",
           "isHardToBorrow": False,
           "isShortable": True,
           "htbQuantity": 43807315,
           "htbRate": 0.0,
       },
       "regular": {
           "regularMarketLastPrice": 22.77,
           "regularMarketLastSize": 6086410,
           "regularMarketNetChange": 0.33,
           "regularMarketPercentChange": 1.47058824,
           "regularMarketTradeTime": 1729281600078,
       },
   }
}
```

</details>

---
### `client.option_chains(symbol, contractType=None, strikeCount=None, includeUnderlyingQuote=None, strategy=None, interval=None, strike=None, range=None, fromDate=None, toDate=None, volatility=None, underlyingPrice=None,interestRate=None, daysToExpiration=None, expMonth=None, optionType=None, entitlement=None)`
Returns a `requests.Response` whose JSON body contains option chain data for the requested symbol.

* `symbol (str)`: Underlying symbol, e.g. `"AAPL"` or `"$SPX"`.
* `contractType (str | None)`: `"ALL"`, `"CALL"`, `"PUT"`.
* `strikeCount (int | None)`: Number of strikes to return.
* `includeUnderlyingQuote (bool | None)`: Include underlying quote in the response.
* `strategy (str | None)`: Option strategy. One of `"SINGLE"` (default), `"ANALYTICAL"`, `"COVERED"`, `"VERTICAL"`, `"CALENDAR"`, `"STRANGLE"`, `"STRADDLE"`, `"BUTTERFLY"`, `"CONDOR"`, `"DIAGONAL"`, `"COLLAR"`, `"ROLL"`.
* `interval (float | None)`: Strike interval.
* `strike (float | None)`: Specific strike price.
* `range (str | None)`: Range of strikes, e.g. `"ITM"`, `"ATM"`, `"OTM"`, etc.
* `fromDate (datetime | str | None)`: Start date (not earlier than current date). Use a `datetime` or `yyyy-MM-dd`.
* `toDate (datetime | str | None)`: End date. Use a `datetime` or `yyyy-MM-dd`.
* `volatility (float | None)`: Implied volatility override.
* `underlyingPrice (float | None)`: Underlying price override.
* `interestRate (float | None)`: Interest rate override.
* `daysToExpiration (int | None)`: Days to expiration override.
* `expMonth (str | None)`: Expiration month. One of `JAN`, `FEB`, ..., `DEC`.
* `optionType (str | None)`: Option type.
* `entitlement (str | None)`: Entitlement: `"PN"`, `"NP"`, `"PP"` (`PP`=PayingPro, `NP`=NonPro, `PN`=NonPayingPro).
<details><summary><u>Return Example</u></summary>

(Truncated)
```python
{
   "symbol": "AAPL",
   "status": "SUCCESS",
   "strategy": "SINGLE",
   "interval": 0.0,
   "isDelayed": False,
   "isIndex": False,
   "interestRate": 4.738,
   "underlyingPrice": 234.83,
   "volatility": 29.0,
   "daysToExpiration": 0.0,
   "numberOfContracts": 2362,
   "assetMainType": "EQUITY",
   "assetSubType": "COE",
   "isChainTruncated": False,
   "callExpDateMap": {
       "2024-10-18:0": {
           "5.0": [
               {
                   "putCall": "CALL",
                   "symbol": "AAPL  241018C00005000",
                   "description": "AAPL 10/18/2024 5.00 C",
                   "exchangeName": "OPR",
                   "bid": 228.65,
                   "ask": 231.95,
                   "last": 225.88,
                   "mark": 230.3,
                   "bidSize": 65,
                   "askSize": 65,
                   "bidAskSize": "65X65",
                   "lastSize": 0,
                   "highPrice": 0.0,
                   "lowPrice": 0.0,
                   "openPrice": 0.0,
                   "closePrice": 227.16,
                   "totalVolume": 0,
                   "tradeTimeInLong": 1728913897074,
                   "quoteTimeInLong": 1729281600041,
                   "netChange": -1.28,
                   "volatility": 7805.668,
                   "delta": 1.0,
                   "gamma": 0.0,
                   "theta": -0.0,
                   "vega": 0.0,
                   "rho": 0.0,
                   "openInterest": 0,
                   "timeValue": -4.12,
                   "theoreticalOptionValue": 230.0,
                   "theoreticalVolatility": 29.0,
                   "optionDeliverablesList": [
                       {
                           "symbol": "AAPL",
                           "assetType": "STOCK",
                           "deliverableUnits": 100.0,
                       }
                   ],
                   "strikePrice": 5.0,
                   "expirationDate": "2024-10-18T20:00:00.000+00:00",
                   "daysToExpiration": 0,
                   "expirationType": "S",
                   "lastTradingDay": 1729296000000,
                   "multiplier": 100.0,
                   "settlementType": "P",
                   "deliverableNote": "100 AAPL",
                   "percentChange": -0.56,
                   "markChange": 3.14,
                   "markPercentChange": 1.38,
                   "intrinsicValue": 230.0,
                   "extrinsicValue": -4.12,
                   "optionRoot": "AAPL",
                   "exerciseType": "A",
                   "high52Week": 226.89,
                   "low52Week": 167.93,
                   "nonStandard": False,
                   "pennyPilot": True,
                   "inTheMoney": True,
                   "mini": False,
               }
           ],
           "10.0": [
               {
                   "putCall": "CALL",
                   "symbol": "AAPL  241018C00010000",
                   "description": "AAPL 10/18/2024 10.00 C",
                   "exchangeName": "OPR",
                   "bid": 224.0,
                   "ask": 226.35,
                   "last": 0.0,
                   "mark": 225.18,
                   "bidSize": 60,
                   "askSize": 60,
                   "bidAskSize": "60X60",
                   "lastSize": 0,
                   "highPrice": 0.0,
                   "lowPrice": 0.0,
                   "openPrice": 0.0,
                   "closePrice": 222.16,
                   "totalVolume": 0,
                   "tradeTimeInLong": 0,
                   "quoteTimeInLong": 1729281600041,
                   "netChange": 0.0,
                   "volatility": 6305.749,
                   "delta": 1.0,
                   "gamma": 0.0,
                   "theta": -0.0,
                   "vega": 0.0,
                   "rho": 0.0,
                   "openInterest": 0,
                   "timeValue": 0.175,
                   "theoreticalOptionValue": 225.0,
                   "theoreticalVolatility": 29.0,
                   "optionDeliverablesList": [
                       {
                           "symbol": "AAPL",
                           "assetType": "STOCK",
                           "deliverableUnits": 100.0,
                       }
                   ],
                   "strikePrice": 10.0,
                   "expirationDate": "2024-10-18T20:00:00.000+00:00",
                   "daysToExpiration": 0,
                   "expirationType": "S",
                   "lastTradingDay": 1729296000000,
                   "multiplier": 100.0,
                   "settlementType": "P",
                   "deliverableNote": "100 AAPL",
                   "percentChange": 0.0,
                   "markChange": 3.01,
                   "markPercentChange": 1.36,
                   "intrinsicValue": 225.0,
                   "extrinsicValue": -225.0,
                   "optionRoot": "AAPL",
                   "exerciseType": "A",
                   "high52Week": 0.0,
                   "low52Week": 0.0,
                   "nonStandard": False,
                   "pennyPilot": True,
                   "inTheMoney": True,
                   "mini": False,
               }
           ],
           "15.0": [
               {
                   "putCall": "CALL",
                   "symbol": "AAPL  241018C00015000",
                   "description": "AAPL 10/18/2024 15.00 C",
                   "exchangeName": "OPR",
                   "bid": 218.8,
                   "ask": 221.9,
                   "last": 204.8,
                   "mark": 220.35,
                   "bidSize": 65,
                   "askSize": 65,
                   "bidAskSize": "65X65",
                   "lastSize": 0,
                   "highPrice": 0.0,
                   "lowPrice": 0.0,
                   "openPrice": 0.0,
                   "closePrice": 217.16,
                   "totalVolume": 0,
                   "tradeTimeInLong": 1726666804076,
                   "quoteTimeInLong": 1729281600041,
                   "netChange": -12.36,
                   "volatility": 5459.839,
                   "delta": 1.0,
                   "gamma": 0.0,
                   "theta": -0.0,
                   "vega": 0.0,
                   "rho": 0.0,
                   "openInterest": 0,
                   "timeValue": -15.2,
                   "theoreticalOptionValue": 220.0,
                   "theoreticalVolatility": 29.0,
                   "optionDeliverablesList": [
                       {
                           "symbol": "AAPL",
                           "assetType": "STOCK",
                           "deliverableUnits": 100.0,
                       }
                   ],
                   "strikePrice": 15.0,
                   "expirationDate": "2024-10-18T20:00:00.000+00:00",
                   "daysToExpiration": 0,
                   "expirationType": "S",
                   "lastTradingDay": 1729296000000,
                   "multiplier": 100.0,
                   "settlementType": "P",
                   "deliverableNote": "100 AAPL",
                   "percentChange": -5.69,
                   "markChange": 3.19,
                   "markPercentChange": 1.47,
                   "intrinsicValue": 220.0,
                   "extrinsicValue": -15.2,
                   "optionRoot": "AAPL",
                   "exerciseType": "A",
                   "high52Week": 204.8,
                   "low52Week": 196.59,
                   "nonStandard": False,
                   "pennyPilot": True,
                   "inTheMoney": True,
                   "mini": False,
               }
           ],
           "20.0": [
               {
                   "putCall": "CALL",
                   "symbol": "AAPL  241018C00020000",
                   "description": "AAPL 10/18/2024 20.00 C",
                   "exchangeName": "OPR",
                   "bid": 213.95,
                   "ask": 216.3,
                   "last": 0.0,
                   "mark": 215.13,
                   "bidSize": 60,
                   "askSize": 60,
                   "bidAskSize": "60X60",
                   "lastSize": 0,
                   "highPrice": 0.0,
                   "lowPrice": 0.0,
                   "openPrice": 0.0,
                   "closePrice": 212.16,
                   "totalVolume": 0,
                   "tradeTimeInLong": 0,
                   "quoteTimeInLong": 1729281600041,
                   "netChange": 0.0,
                   "volatility": 4871.802,
                   "delta": 1.0,
                   "gamma": 0.0,
                   "theta": -0.0,
                   "vega": 0.0,
                   "rho": 0.0,
                   "openInterest": 0,
                   "timeValue": 0.125,
                   "theoreticalOptionValue": 215.0,
                   "theoreticalVolatility": 29.0,
                   "optionDeliverablesList": [
                       {
                           "symbol": "AAPL",
                           "assetType": "STOCK",
                           "deliverableUnits": 100.0,
                       }
                   ],
                   "strikePrice": 20.0,
                   "expirationDate": "2024-10-18T20:00:00.000+00:00",
                   "daysToExpiration": 0,
                   "expirationType": "S",
                   "lastTradingDay": 1729296000000,
                   "multiplier": 100.0,
                   "settlementType": "P",
                   "deliverableNote": "100 AAPL",
                   "percentChange": 0.0,
                   "markChange": 2.96,
                   "markPercentChange": 1.4,
                   "intrinsicValue": 215.0,
                   "extrinsicValue": -215.0,
                   "optionRoot": "AAPL",
                   "exerciseType": "A",
                   "high52Week": 0.0,
                   "low52Week": 0.0,
                   "nonStandard": False,
                   "pennyPilot": True,
                   "inTheMoney": True,
                   "mini": False,
               }
           ],
           ...
       }
   }
}
```
</details>

---
### `client.option_expiration_chain(symbol)`
Returns a `requests.Response` whose JSON body is a list of option expiration entries for the given symbol.

* `symbol (str)`: Symbol to get expiration chain for, e.g. `"AAPL"`.
<details><summary><u>Example</u></summary>

(Truncated)
```python
> client.option_expiration_chain("AAPL").json()
{
   "expirationList": [
       {
           "expirationDate": "2024-10-18",
           "daysToExpiration": 0,
           "expirationType": "S",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-10-25",
           "daysToExpiration": 7,
           "expirationType": "W",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-11-01",
           "daysToExpiration": 14,
           "expirationType": "W",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-11-08",
           "daysToExpiration": 21,
           "expirationType": "W",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-11-15",
           "daysToExpiration": 28,
           "expirationType": "S",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-11-22",
           "daysToExpiration": 35,
           "expirationType": "W",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-11-29",
           "daysToExpiration": 42,
           "expirationType": "W",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2024-12-20",
           "daysToExpiration": 63,
           "expirationType": "S",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2025-01-17",
           "daysToExpiration": 91,
           "expirationType": "S",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2025-02-21",
           "daysToExpiration": 126,
           "expirationType": "S",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
       {
           "expirationDate": "2025-03-21",
           "daysToExpiration": 154,
           "expirationType": "S",
           "settlementType": "P",
           "optionRoots": "AAPL",
           "standard": True,
       },
     ...
   ]
}
```

</details>

---
### `client.price_history(symbol, periodType=None, period=None, frequencyType=None, frequency=None, startDate=None, endDate=None, needExtendedHoursData=None, needPreviousClose=None)`
Returns a `requests.Response` whose JSON body contains historical price data for a symbol.

* `symbol (str)`: Symbol to get price history for, e.g. `"AAPL"`.
* `periodType (str | None)`: One of `"day"`, `"month"`, `"year"`, `"ytd"`.
* `period (int | None)`:
    * For periodType `"day"`: `1, 2, 3, 4, 5, 10`
    * For `"month"`: `1, 2, 3, 6`
    * For `"year"`: `1, 2, 3, 5, 10, 15, 20`
    * For `"ytd"`: `1`
    Default is `1` (except `"day"` → default `10`).
* `frequencyType (str | None)`:
    * For periodType `"day"`: `"minute"`
    * For `"month"`: `"daily"`, `"weekly"`
    * For `"year"` / `"ytd"`: `"daily"`, `"weekly"`, `"monthly"`
    * Default is the largest possible per `periodType`.
* `frequency (int | None)`:
    * For frequencyType `"minute"`: `1, 5, 10, 15, 30`
    * For `"daily"`, `"weekly"`, `"monthly"`: `1`
* `startDate (datetime | int | None)`: Start date as `datetime` or UNIX epoch.
* `endDate (datetime | int | None)`: End date as `datetime` or UNIX epoch.
* `needExtendedHoursData (bool | None)`: Include extended hours candles if `True`.
* `needPreviousClose (bool | None)`: Include previous close if `True`.

<details><summary><u>Return Example</u></summary>

```python
{
   "candles": [
       {
           "open": 171.0,
           "high": 192.93,
           "low": 170.12,
           "close": 189.95,
           "volume": 1099760711,
           "datetime": 1698814800000,
       },
       {
           "open": 190.33,
           "high": 199.62,
           "low": 187.4511,
           "close": 192.53,
           "volume": 1063181128,
           "datetime": 1701410400000,
       },
       {
           "open": 187.15,
           "high": 196.38,
           "low": 180.17,
           "close": 184.4,
           "volume": 1187490645,
           "datetime": 1704088800000,
       },
       {
           "open": 183.985,
           "high": 191.05,
           "low": 179.25,
           "close": 180.75,
           "volume": 1161711745,
           "datetime": 1706767200000,
       },
       {
           "open": 179.55,
           "high": 180.53,
           "low": 168.49,
           "close": 171.48,
           "volume": 1433151760,
           "datetime": 1709272800000,
       },
       {
           "open": 171.19,
           "high": 178.36,
           "low": 164.075,
           "close": 170.33,
           "volume": 1246221542,
           "datetime": 1711947600000,
       },
       {
           "open": 169.58,
           "high": 193.0,
           "low": 169.11,
           "close": 192.25,
           "volume": 1336570142,
           "datetime": 1714539600000,
       },
       {
           "open": 192.9,
           "high": 220.2,
           "low": 192.15,
           "close": 210.62,
           "volume": 1723984420,
           "datetime": 1717218000000,
       },
       {
           "open": 212.09,
           "high": 237.23,
           "low": 211.92,
           "close": 222.08,
           "volume": 1153193377,
           "datetime": 1719810000000,
       },
       {
           "open": 224.37,
           "high": 232.92,
           "low": 196.0,
           "close": 229.0,
           "volume": 1122666993,
           "datetime": 1722488400000,
       },
       {
           "open": 228.55,
           "high": 233.09,
           "low": 213.92,
           "close": 233.0,
           "volume": 1232391861,
           "datetime": 1725166800000,
       },
       {
           "open": 229.52,
           "high": 237.49,
           "low": 221.33,
           "close": 235.0,
           "volume": 550590311,
           "datetime": 1727758800000,
       },
   ],
   "symbol": "AAPL",
   "empty": False,
}
```

</details>

---
### `client.movers(symbol, sort=None, frequency=None)`
Returns a `requests.Response` whose JSON body is a list of movers for an index or universe.

* `symbol (str)`: Index or screener symbol. Options include: `"$DJI"`, `"$COMPX"`, `"$SPX"`, `"NYSE"`, `"NASDAQ"`, `"OTCBB"`, `"INDEX_ALL"`, `"EQUITY_ALL"`, `"OPTION_ALL"`, `"OPTION_PUT"`, `"OPTION_CALL"`.
* `sort (str | None)`: Sort key. One of `"VOLUME"`, `"TRADES"`, `"PERCENT_CHANGE_UP"`, `"PERCENT_CHANGE_DOWN"`.
* `frequency (int | None)`: Frequency bucket. One of `0` (default), `1`, `5`, `10`, `30`, `60`.
<details><summary><u>Return Example</u></summary>

```python
{
   "screeners": [
       {
           "description": "APPLE INC",
           "volume": 46430830,
           "lastPrice": 235.0,
           "netChange": 235.0,
           "marketShare": 15.28,
           "totalVolume": 303821282,
           "trades": 562489,
           "netPercentChange": 1.0,
           "symbol": "AAPL",
       },
       {
           "description": "INTEL CORP",
           "volume": 39970403,
           "lastPrice": 22.77,
           "netChange": 22.77,
           "marketShare": 13.16,
           "totalVolume": 303821282,
           "trades": 143104,
           "netPercentChange": 1.0,
           "symbol": "INTC",
       },
       {
           "description": "Amazon.com Inc",
           "volume": 37416896,
           "lastPrice": 188.99,
           "netChange": 188.99,
           "marketShare": 12.32,
           "totalVolume": 303821282,
           "trades": 375970,
           "netPercentChange": 1.0,
           "symbol": "AMZN",
       },
       {
           "description": "CISCO SYS INC",
           "volume": 17679841,
           "lastPrice": 56.76,
           "netChange": 56.76,
           "marketShare": 5.82,
           "totalVolume": 303821282,
           "trades": 107680,
           "netPercentChange": 1.0,
           "symbol": "CSCO",
       },
       {
           "description": "Microsoft Corp",
           "volume": 17145258,
           "lastPrice": 418.16,
           "netChange": 418.16,
           "marketShare": 5.64,
           "totalVolume": 303821282,
           "trades": 275276,
           "netPercentChange": 1.0,
           "symbol": "MSFT",
       },
       {
           "description": "The Coca-Cola Co",
           "volume": 15087513,
           "lastPrice": 70.44,
           "netChange": 70.44,
           "marketShare": 4.97,
           "totalVolume": 303821282,
           "trades": 125504,
           "netPercentChange": 1.0,
           "symbol": "KO",
       },
       {
           "description": "VERIZON COMMUNICATIO",
           "volume": 13058369,
           "lastPrice": 43.99,
           "netChange": 43.99,
           "marketShare": 4.3,
           "totalVolume": 303821282,
           "trades": 75477,
           "netPercentChange": 1.0,
           "symbol": "VZ",
       },
       {
           "description": "WALMART INC",
           "volume": 12324148,
           "lastPrice": 81.31,
           "netChange": 81.31,
           "marketShare": 4.06,
           "totalVolume": 303821282,
           "trades": 94227,
           "netPercentChange": 1.0,
           "symbol": "WMT",
       },
       {
           "description": "Merck &amp; Co. Inc.",
           "volume": 9523037,
           "lastPrice": 108.7,
           "netChange": 108.7,
           "marketShare": 3.13,
           "totalVolume": 303821282,
           "trades": 91532,
           "netPercentChange": 1.0,
           "symbol": "MRK",
       },
       {
           "description": "DISNEY WALT CO",
           "volume": 8601528,
           "lastPrice": 97.28,
           "netChange": 97.28,
           "marketShare": 2.83,
           "totalVolume": 303821282,
           "trades": 87916,
           "netPercentChange": 1.0,
           "symbol": "DIS",
       },
   ]
}
```

</details>

---
### `client.market_hours(symbols, date=None)`
Returns a `requests.Response` whose JSON body contains market hours for one or more product types.

* `symbols (list | str)`: Product(s) to get market hours for. Options include `"equity"`, `"option"`, `"bond"`, `"future"`, `"forex"`.
* `date (datetime | str | None)`: Date to query. Use a `datetime` or a string `yyyy-MM-dd`. Defaults to today.
<details><summary><u>Example</u></summary>

```python
> client.market_hours(["equity", "option"]).json()
{
   "equity": {
       "EQ": {
           "date": "2024-10-18",
           "marketType": "EQUITY",
           "product": "EQ",
           "productName": "equity",
           "isOpen": True,
           "sessionHours": {
               "preMarket": [
                   {
                       "start": "2024-10-18T07:00:00-04:00",
                       "end": "2024-10-18T09:30:00-04:00",
                   }
               ],
               "regularMarket": [
                   {
                       "start": "2024-10-18T09:30:00-04:00",
                       "end": "2024-10-18T16:00:00-04:00",
                   }
               ],
               "postMarket": [
                   {
                       "start": "2024-10-18T16:00:00-04:00",
                       "end": "2024-10-18T20:00:00-04:00",
                   }
               ],
           },
       }
   },
   "option": {
       "EQO": {
           "date": "2024-10-18",
           "marketType": "OPTION",
           "product": "EQO",
           "productName": "equity option",
           "isOpen": True,
           "sessionHours": {
               "regularMarket": [
                   {
                       "start": "2024-10-18T09:30:00-04:00",
                       "end": "2024-10-18T16:00:00-04:00",
                   }
               ]
           },
       },
       "IND": {
           "date": "2024-10-18",
           "marketType": "OPTION",
           "product": "IND",
           "productName": "index option",
           "isOpen": True,
           "sessionHours": {
               "regularMarket": [
                   {
                       "start": "2024-10-18T09:30:00-04:00",
                       "end": "2024-10-18T16:15:00-04:00",
                   }
               ]
           },
       },
   },
}
```

</details>

---
### `client.market_hour(market_id, date=None)`
Returns a `requests.Response` whose JSON body contains market hours for a single market type.

* `market_id (str)`: Market ID to get hours for. Options include `"equity"`, `"option"`, `"bond"`, `"future"`, `"forex"`.
* `date (datetime | str | None)`: Date to query. Use a `datetime` or a string `yyyy-MM-dd`. Defaults to today.
<details><summary><u>Example</u></summary>

```python
> client.market_hour("equity").json()
{
   "equity": {
       "EQ": {
           "date": "2024-10-18",
           "marketType": "EQUITY",
           "product": "EQ",
           "productName": "equity",
           "isOpen": True,
           "sessionHours": {
               "preMarket": [
                   {
                       "start": "2024-10-18T07:00:00-04:00",
                       "end": "2024-10-18T09:30:00-04:00",
                   }
               ],
               "regularMarket": [
                   {
                       "start": "2024-10-18T09:30:00-04:00",
                       "end": "2024-10-18T16:00:00-04:00",
                   }
               ],
               "postMarket": [
                   {
                       "start": "2024-10-18T16:00:00-04:00",
                       "end": "2024-10-18T20:00:00-04:00",
                   }
               ],
           },
       }
   }
}
```

</details>

---
### `client.instruments(symbol, projection)`
Returns a `requests.Response` whose JSON body is a dict of instruments matching the query.

* `symbol (str)`: Symbol or search string, e.g. `"AAPL"`.
* `projection (str)`: Projection mode. One of `"symbol-search"`, `"symbol-regex"`, `"desc-search"`, `"desc-regex"`, `"search"`, `"fundamental"`.
<details><summary><u>Return Example</u></summary>

```python
{
   "instruments": [
       {
           "fundamental": {
               "symbol": "AAPL",
               "high52": 237.49,
               "low52": 164.075,
               "dividendAmount": 1.0,
               "dividendYield": 0.43144,
               "dividendDate": "2024-08-12 00:00:00.0",
               "peRatio": 35.35277,
               "pegRatio": 116.555,
               "pbRatio": 48.06189,
               "prRatio": 8.43929,
               "pcfRatio": 23.01545,
               "grossMarginTTM": 45.962,
               "grossMarginMRQ": 46.2571,
               "netProfitMarginTTM": 26.4406,
               "netProfitMarginMRQ": 25.0043,
               "operatingMarginTTM": 26.4406,
               "operatingMarginMRQ": 25.0043,
               "returnOnEquity": 160.5833,
               "returnOnAssets": 22.6119,
               "returnOnInvestment": 50.98106,
               "quickRatio": 0.79752,
               "currentRatio": 0.95298,
               "interestCoverage": 0.0,
               "totalDebtToCapital": 51.3034,
               "ltDebtToEquity": 151.8618,
               "totalDebtToEquity": 129.2138,
               "epsTTM": 6.56667,
               "epsChangePercentTTM": 10.3155,
               "epsChangeYear": 0.0,
               "epsChange": 0.0,
               "revChangeYear": -2.8005,
               "revChangeTTM": 0.4349,
               "revChangeIn": 0.0,
               "sharesOutstanding": 15204137000.0,
               "marketCapFloat": 0.0,
               "marketCap": 3524014873860.0,
               "bookValuePerShare": 4.38227,
               "shortIntToFloat": 0.0,
               "shortIntDayToCover": 0.0,
               "divGrowthRate3Year": 0.0,
               "dividendPayAmount": 0.25,
               "dividendPayDate": "2024-08-15 00:00:00.0",
               "beta": 1.23919,
               "vol1DayAvg": 0.0,
               "vol10DayAvg": 0.0,
               "vol3MonthAvg": 0.0,
               "avg10DaysVolume": 37498265,
               "avg1DayVolume": 58820585,
               "avg3MonthVolume": 51544618,
               "declarationDate": "2024-08-01 00:00:00.0",
               "dividendFreq": 4,
               "eps": 6.13,
               "dtnVolume": 34065076,
               "nextDividendPayDate": "2024-11-15 00:00:00.0",
               "nextDividendDate": "2024-11-12 00:00:00.0",
               "fundLeverageFactor": 0.0,
           },
           "cusip": "037833100",
           "symbol": "AAPL",
           "description": "APPLE INC",
           "exchange": "NASDAQ",
           "assetType": "EQUITY",
       }
   ]
}
```

</details>

---
### `client.instrument_cusip(cusip_id)`
Returns a `requests.Response` whose JSON body is a list of instruments that match the given CUSIP.

* `cusip_id (str)`: CUSIP to look up, e.g. `"037833100"`.
<details><summary><u>Return Example</u></summary>

```python
{
   "instruments": [
       {
           "cusip": "037833100",
           "symbol": "AAPL",
           "description": "APPLE INC",
           "exchange": "NASDAQ",
           "assetType": "EQUITY",
       }
   ]
}
```
</details>

