"""
This file contains functions to create a client class that accesses the Schwab api
Coded by Tyler Bowers
Github: https://github.com/tylerebowers/Schwab-API-Python
"""
import datetime
import logging
import threading
import time
import urllib.parse
from typing import Any

import requests

from schwabdev.enums import TimeFormat

from .stream import Stream
from .tokens import Tokens


class Client:

    def __init__(self, app_key, app_secret, callback_url="https://127.0.0.1", tokens_file="tokens.json", timeout=10, capture_callback=False, use_session=True, call_on_notify=None):
        """
        Initialize a client to access the Schwab API.

        Args:
            app_key (str): App key credential.
            app_secret (str): App secret credential.
            callback_url (str): URL for callback.
            tokens_file (str): Path to tokens file.
            timeout (int): Request timeout in seconds - how long to wait for a response.
            capture_callback (bool): Use a webserver with self-signed cert to capture callback with code (no copy/pasting urls during auth).
            use_session (bool): Use a requests session for requests instead of creating a new session for each request.
            call_on_notify (function | None): Function to call when user needs to be notified (e.g. for input)
        """

        # other checks are done in the tokens class
        if timeout <= 0:
            raise Exception("Timeout must be greater than 0 and is recommended to be 5 seconds or more.")

        self.version = "Schwabdev 2.5.1"                                    # version of the client
        self.timeout = timeout                                              # timeout to use in requests
        self.logger = logging.getLogger("Schwabdev")  # init the logger
        self._session = requests.Session() if use_session else requests  # session to use in requests
        self.tokens = Tokens(self, app_key, app_secret, callback_url, tokens_file, capture_callback, call_on_notify)
        self.stream = Stream(self)                                          # init the streaming object

        # Spawns a thread to check the tokens and updates if necessary, also updates the session
        def checker():
            while True:
                if self.tokens.update_tokens() and use_session:
                    self._session = requests.Session() #make a new session if the access token was updated
                time.sleep(30)

        threading.Thread(target=checker, daemon=True).start()

        self.logger .info("Client Initialization Complete")


    def _params_parser(self, params: dict):
        """
        Removes None (null) values

        Args:
            params (dict): params to remove None values from

        Returns:
            dict: params without None values

        Example:
            params = {'a': 1, 'b': None}
            client._params_parser(params)
            {'a': 1}
        """
        for key in list(params.keys()):
            if params[key] is None: del params[key]
        return params

    def _time_convert(self, dt=None, format: str | TimeFormat=TimeFormat.ISO_8601) -> str | int | None:
        """
        Convert time to the correct format, passthrough if a string, preserve None if None for params parser

        Args:
            dt (datetime.datetime): datetime object to convert
            form (str): format to convert to (check source for options)

        Returns:
            str | None: converted time (or None passed through)
        """
        if dt is None or not isinstance(dt, datetime.datetime):
            return dt
        match format:
            case TimeFormat.ISO_8601 | TimeFormat.ISO_8601.value:
                return f"{dt.isoformat().split('+')[0][:-3]}Z"
            case TimeFormat.EPOCH | TimeFormat.EPOCH.value:
                return int(dt.timestamp())
            case TimeFormat.EPOCH_MS | TimeFormat.EPOCH_MS.value:
                return int(dt.timestamp() * 1000)
            case TimeFormat.YYYY_MM_DD | TimeFormat.YYYY_MM_DD.value:
                return dt.strftime('%Y-%m-%d')
            case _:
                raise ValueError(f"Unsupported time format: {format}")


    def _format_list(self, l: list | str | None):
        """
        Convert python list to string or passthough if a string or None

        Args:
            l (list | str | None): list to convert

        Returns:
            str | None: converted string or passthrough

        Example:
            l = ["a", "b"]
            client._format_list(l)
            "a,b"
        """
        if l is None:
            return None
        elif isinstance(l, list):
            return ",".join(l)
        else:
            return l

    _base_api_url = "https://api.schwabapi.com"

    """
    Accounts and Trading Production
    """

    def account_linked(self) -> requests.Response:
        """
        Account numbers in plain text cannot be used outside of headers or request/response bodies.
        As the first step consumers must invoke this service to retrieve the list of plain text/encrypted value pairs, and use encrypted account values for all subsequent calls for any accountNumber request.

        Return:
            request.Response: All linked account numbers and hashes
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/accountNumbers',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    def account_details_all(self, fields: str | None = None) -> requests.Response:
        """
        All the linked account information for the user logged in. The balances on these accounts are displayed by default however the positions on these accounts will be displayed based on the "positions" flag.

        Args:
            fields (str | None): fields to return (options: "positions")

        Returns:
            request.Response: details for all linked accounts
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)

    def account_details(self, accountHash: str, fields: str | None = None) -> requests.Response:
        """
        Specific account information with balances and positions. The balance information on these accounts is displayed by default but Positions will be returned based on the "positions" flag.

        Args:
            accountHash (str): account hash from account_linked()
            fields (str | None): fields to return

        Returns:
            request.Response: details for one linked account
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)

    def account_orders(self, accountHash: str, fromEnteredTime: datetime.datetime | str, toEnteredTime: datetime.datetime | str, maxResults: int | None = None, status: str | None = None) -> requests.Response:
        """
        All orders for a specific account. Orders retrieved can be filtered based on input parameters below. Maximum date range is 1 year.

        Args:
            accountHash (str): account hash from account_linked()
            fromEnteredTime (datetime.datetime | str): start date
            toEnteredTime (datetime.datetime | str): end date
            maxResults (int | None): maximum number of results (set to None for default 3000)
            status (str | None): status of order

        Returns:
            request.Response: orders for one linked account
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders',
                            headers={"Accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'maxResults': maxResults,
                                 'fromEnteredTime': self._time_convert(fromEnteredTime, TimeFormat.ISO_8601),
                                 'toEnteredTime': self._time_convert(toEnteredTime, TimeFormat.ISO_8601),
                                 'status': status}),
                            timeout=self.timeout)

    def order_place(self, accountHash: str, order: dict) -> requests.Response:
        """
        Place an order for a specific account.

        Args:
            accountHash (str): account hash from account_linked()
            order (dict): order dictionary (format examples in github documentation)

        Returns:
            request.Response: order number in response header (if immediately filled then order number not returned)
        """
        return self._session.post(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders',
                             headers={"Accept": "application/json",
                                      'Authorization': f'Bearer {self.tokens.access_token}',
                                      "Content-Type": "application/json"},
                             json=order,
                             timeout=self.timeout)

    def order_details(self, accountHash: str, orderId: int | str) -> requests.Response:
        """
        Get a specific order by its ID, for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id

        Returns:
            request.Response: order details
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders/{orderId}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    def order_cancel(self, accountHash: str, orderId: int | str) -> requests.Response:
        """
        Cancel a specific order by its ID, for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id

        Returns:
            request.Response: response code
        """
        return self._session.delete(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders/{orderId}',
                               headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                               timeout=self.timeout)

    def order_replace(self, accountHash: str, orderId: int | str, order: dict) -> requests.Response:
        """
        Replace an existing order for an account. The existing order will be replaced by the new order. Once replaced, the old order will be canceled and a new order will be created.

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id
            order (dict): order dictionary (format examples in github documentation)

        Returns:
            request.Response: response code
        """
        return self._session.put(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders/{orderId}',
                            headers={"Accept": "application/json",
                                     'Authorization': f'Bearer {self.tokens.access_token}',
                                     "Content-Type": "application/json"},
                            json=order,
                            timeout=self.timeout)

    def account_orders_all(self, fromEnteredTime: datetime.datetime | str, toEnteredTime: datetime.datetime | str, maxResults: str | None = None, status: str | None = None) -> requests.Response:
        """
        Get all orders for all accounts

        Args:
            fromEnteredTime (datetime.datetime | str): start date
            toEnteredTime (datetime.datetime | str): end date
            maxResults (int | None): maximum number of results (set to None for default 3000)
            status (str | None): status of order (see documentation for possible values)

        Returns:
            request.Response: all orders
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/orders',
                            headers={"Accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'maxResults': maxResults,
                                 'fromEnteredTime': self._time_convert(fromEnteredTime, TimeFormat.ISO_8601),
                                 'toEnteredTime': self._time_convert(toEnteredTime, TimeFormat.ISO_8601),
                                 'status': status}),
                            timeout=self.timeout)

    """
    def order_preview(self, accountHash, orderObject) -> requests.Response:
        #COMING SOON (waiting on Schwab)
        return self._session.post(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/previewOrder',
                             headers={'Authorization': f'Bearer {self.tokens.access_token}',
                                      "Content-Type": "application.json"}, data=orderObject)
    """

    def transactions(self, accountHash: str, startDate: datetime.datetime | str, endDate: datetime.datetime | str, types: str, symbol: str | None = None) -> requests.Response:
        """
        All transactions for a specific account. Maximum number of transactions in response is 3000. Maximum date range is 1 year.

        Args:
            accountHash (str): account hash from account_linked()
            startDate (datetime.datetime | str): start date
            endDate (datetime.datetime | str): end date
            types (str): transaction type (see documentation for possible values)
            symbol (str | None): symbol

        Returns:
            request.Response: list of transactions for a specific account
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/transactions',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'startDate': self._time_convert(startDate, TimeFormat.ISO_8601),
                                 'endDate': self._time_convert(endDate, TimeFormat.ISO_8601),
                                 'symbol': symbol,
                                 'types': types}),
                            timeout=self.timeout)

    def transaction_details(self, accountHash: str, transactionId: str | int) -> requests.Response:
        """
        Get specific transaction information for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            transactionId (str | int): transaction id

        Returns:
            request.Response: transaction details of transaction id using accountHash
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/transactions/{transactionId}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    def preferences(self) -> requests.Response:
        """
        Get user preference information for the logged in user.

        Returns:
            request.Response: User preferences and streaming info
        """
        return self._session.get(f'{self._base_api_url}/trader/v1/userPreference',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    """
    Market Data
    """

    def quotes(self, symbols : list[str] | str, fields: str | None = None, indicative: bool = False) -> requests.Response:
        """
        Get quotes for a list of tickers

        Args:
            symbols (list[str] | str): list of symbols strings (e.g. "AMD,INTC" or ["AMD", "INTC"])
            fields (str): fields to get ("all", "quote", "fundamental")
            indicative (bool): whether to get indicative quotes (True/False)

        Returns:
            request.Response: list of quotes
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/quotes',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'symbols': self._format_list(symbols),
                                 'fields': fields,
                                 'indicative': indicative}),
                            timeout=self.timeout)

    def quote(self, symbol_id: str, fields: str | None = None) -> requests.Response:
        """
        Get quote for a single symbol

        Args:
            symbol_id (str): ticker symbol
            fields (str): fields to get ("all", "quote", "fundamental")

        Returns:
            request.Response: quote for a single symbol
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/{urllib.parse.quote(symbol_id,safe="")}/quotes',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)

    def option_chains(self, symbol: str, contractType: str | None = None, strikeCount: Any = None, includeUnderlyingQuote: bool | None = None, strategy: str | None = None,
               interval: Any = None, strike: Any = None, range: str | None = None, fromDate: datetime.datetime | str | None = None, toDate: datetime.datetime | str | None = None, volatility: Any = None, underlyingPrice: Any = None,
               interestRate: Any = None, daysToExpiration: Any = None, expMonth: str | None = None, optionType: str | None = None, entitlement: str | None = None) -> requests.Response:
        """
        Get Option Chain including information on options contracts associated with each expiration for a ticker.

        Args:
            symbol (str): ticker symbol
            contractType (str): contract type ("CALL"|"PUT"|"ALL")
            strikeCount (int): strike count
            includeUnderlyingQuote (bool): include underlying quote (True|False)
            strategy (str): strategy ("SINGLE"|"ANALYTICAL"|"COVERED"|"VERTICAL"|"CALENDAR"|"STRANGLE"|"STRADDLE"|"BUTTERFLY"|"CONDOR"|"DIAGONAL"|"COLLAR"|"ROLL)
            interval (str): Strike interval
            strike (float): Strike price
            range (str): range ("ITM"|"NTM"|"OTM"...)
            fromDate (datetime.pyi | str): from date, cannot be earlier than the current date
            toDate (datetime.pyi | str): to date
            volatility (float): volatility
            underlyingPrice (float): underlying price
            interestRate (float): interest rate
            daysToExpiration (int): days to expiration
            expMonth (str): expiration month
            optionType (str): option type ("ALL"|"CALL"|"PUT")
            entitlement (str): entitlement ("ALL"|"AMERICAN"|"EUROPEAN")

        Notes:
            1. Some calls can exceed the amount of data that can be returned which results in a "Body buffer overflow"
               error from the server, to fix this you must add additional parameters to limit the amount of data returned.
            2. Some symbols are differnt for Schwab, to find ticker symbols use Schwab research tools search here:
               https://client.schwab.com/app/research/#/tools/stocks

        Returns:
            request.Response: option chain
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/chains',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'symbol': symbol,
                                 'contractType': contractType,
                                 'strikeCount': strikeCount,
                                 'includeUnderlyingQuote': includeUnderlyingQuote,
                                 'strategy': strategy,
                                 'interval': interval,
                                 'strike': strike,
                                 'range': range,
                                 'fromDate': self._time_convert(fromDate, TimeFormat.YYYY_MM_DD),
                                 'toDate': self._time_convert(toDate, TimeFormat.YYYY_MM_DD),
                                 'volatility': volatility,
                                 'underlyingPrice': underlyingPrice,
                                 'interestRate': interestRate,
                                 'daysToExpiration': daysToExpiration,
                                 'expMonth': expMonth,
                                 'optionType': optionType,
                                 'entitlement': entitlement}),
                            timeout=self.timeout)

    def option_expiration_chain(self, symbol: str) -> requests.Response:
        """
        Get an option expiration chain for a ticker

        Args:
            symbol (str): Ticker symbol

        Returns:
            request.Response: Option expiration chain
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/expirationchain',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'symbol': symbol}),
                            timeout=self.timeout)

    def price_history(self, symbol: str, periodType: str | None = None, period: str | None = None, frequencyType: str | None = None, frequency: Any = None, startDate: datetime.datetime | str | None = None,
                      endDate: Any = None, needExtendedHoursData: bool | None = None, needPreviousClose: bool | None = None) -> requests.Response:
        """
        Get price history for a ticker

        Args:
            symbol (str): ticker symbol
            periodType (str): period type ("day"|"month"|"year"|"ytd")
            period (int): period
            frequencyType (str): frequency type ("minute"|"daily"|"weekly"|"monthly")
            frequency (int): frequency (frequencyType: options), (minute: 1, 5, 10, 15, 30), (daily: 1), (weekly: 1), (monthly: 1)
            startDate (datetime.pyi | str): start date
            endDate (datetime.pyi | str): end date
            needExtendedHoursData (bool): need extended hours data (True|False)
            needPreviousClose (bool): need previous close (True|False)

        Returns:
            request.Response: Dictionary containing candle history
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/pricehistory',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'symbol': symbol,
                                                        'periodType': periodType,
                                                        'period': period,
                                                        'frequencyType': frequencyType,
                                                        'frequency': frequency,
                                                        'startDate': self._time_convert(startDate, TimeFormat.EPOCH_MS),
                                                        'endDate': self._time_convert(endDate, TimeFormat.EPOCH_MS),
                                                        'needExtendedHoursData': needExtendedHoursData,
                                                        'needPreviousClose': needPreviousClose}),
                            timeout=self.timeout)

    def movers(self, symbol: str, sort: str | None = None, frequency: Any = None) -> requests.Response:
        """
        Get movers in a specific index and direction

        Args:
            symbol (str): symbol ("$DJI"|"$COMPX"|"$SPX"|"NYSE"|"NASDAQ"|"OTCBB"|"INDEX_ALL"|"EQUITY_ALL"|"OPTION_ALL"|"OPTION_PUT"|"OPTION_CALL")
            sort (str): sort ("VOLUME"|"TRADES"|"PERCENT_CHANGE_UP"|"PERCENT_CHANGE_DOWN")
            frequency (int): frequency (0|1|5|10|30|60)

        Notes:
            Must be called within market hours (there aren't really movers outside of market hours)

        Returns:
            request.Response: Movers
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/movers/{symbol}',
                            headers={"accept": "application/json",
                                     'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'sort': sort,
                                                        'frequency': frequency}),
                            timeout=self.timeout)

    def market_hours(self, symbols: list[str], date: datetime.datetime | str | None = None) -> requests.Response:
        """
        Get Market Hours for dates in the future across different markets.

        Args:
            symbols (list[str]): list of market symbols ("equity", "option", "bond", "future", "forex")
            date (datetime.pyi | str): Date

        Returns:
            request.Response: Market hours
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/markets',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'markets': symbols, #self._format_list(symbols),
                                 'date': self._time_convert(date, TimeFormat.YYYY_MM_DD)}),
                            timeout=self.timeout)

    def market_hour(self, market_id: str, date: datetime.datetime | str | None = None) -> requests.Response:
        """
        Get Market Hours for dates in the future for a single market.

        Args:
            market_id (str): market id ("equity"|"option"|"bond"|"future"|"forex")
            date (datetime.pyi | str): date

        Returns:
            request.Response: Market hours
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/markets/{market_id}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'date': self._time_convert(date, TimeFormat.YYYY_MM_DD)}),
                            timeout=self.timeout)

    def instrument_list(self, symbols : list[str] | str, projection: str) -> requests.Response:
        """
        Get instruments for a list of symbols

        Args:
            symbol (list[str] | str): list of symbols strings (e.g. "AMD,INTC" or ["AMD", "INTC"])
            projection (str): projection ("symbol-search"|"symbol-regex"|"desc-search"|"desc-regex"|"search"|"fundamental")

        Returns:
            request.Response: Instruments
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/instruments',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'symbol': self._format_list(symbols),
                                 'projection': projection}),
                            timeout=self.timeout)
    

    def instruments(self, symbol: str, projection: str) -> requests.Response:
        """
        Get instruments for a list of symbols

        Args:
            symbol (str): symbol
            projection (str): projection ("symbol-search"|"symbol-regex"|"desc-search"|"desc-regex"|"search"|"fundamental")

        Returns:
            request.Response: Instruments
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/instruments',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params={'symbol': symbol,
                                    'projection': projection},
                            timeout=self.timeout)

    def instrument_cusip(self, cusip_id: str | int) -> requests.Response:
        """
        Get instrument for a single cusip

        Args:
            cusip_id (str|int): cusip id

        Returns:
            request.Response: Instrument
        """
        return self._session.get(f'{self._base_api_url}/marketdata/v1/instruments/{cusip_id}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)
