"""
This file contains functions to create a client class that accesses the Schwab api
Coded by Tyler Bowers
Github: https://github.com/tylerebowers/Schwab-API-Python
"""
import datetime
import logging
import asyncio
import urllib.parse
from typing import Any
import threading
import requests

try:
    import aiohttp
except ImportError:
    aiohttp = None

from .enums import TimeFormat
from .tokens import Tokens


class ClientBase:

    _base_api_url = "https://api.schwabapi.com"

    def __init__(self, app_key, app_secret, callback_url="https://127.0.0.1", tokens_db="~/.schwabdev/tokens.db", timeout=10, capture_callback=False, call_on_auth=None):
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

        self.version = "Schwabdev 2.6.0"                                    # version of the client
        self.timeout = timeout                                              # timeout to use in requests
        self.logger = logging.getLogger("Schwabdev")  # init the logger
        self.tokens = Tokens(app_key, app_secret, callback_url, self.logger, tokens_db, capture_callback, call_on_auth)
        self.tokens.update_tokens()                                               # ensure tokens are up to date on init


    def _parse_params(self, params: dict):
        """
        Removes None (null) values.

        Args:
            params (dict): params to remove None values from

        Returns:
            dict: params without None values

        Example:
            params = {'a': 1, 'b': None}
            client._parse_params(params)
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
    
    def _get_streamer_info(self):
        self.tokens.update_tokens()
        response = requests.request("GET", f'{self._base_api_url}/trader/v1/userPreference', headers={'Authorization': f'Bearer {self.tokens.access_token}'})
        if response.ok:
            return response.json().get('streamerInfo', None)[0]
        else:
            self.logger.error("Could not get streamerInfo")
            return

class Client(ClientBase):

    def __init__(self, app_key, app_secret, callback_url="https://127.0.0.1", tokens_db="~/.schwabdev/tokens.db", timeout=10, capture_callback=False, call_on_auth=None):
        """
        Initialize a client to access the Schwab API.

        Args:
            app_key (str): App key credential.
            app_secret (str): App secret credential.
            callback_url (str): URL for callback.
            tokens_file (str): Path to tokens file.
            timeout (int): Request timeout in seconds - how long to wait for a response.
            capture_callback (bool): Use a webserver with self-signed cert to capture callback with code (no copy/pasting urls during auth).
            call_on_auth (function | None): Function to call for custom auth flow.
        """
        super().__init__(app_key, app_secret, callback_url, tokens_db, timeout, capture_callback, call_on_auth)

        self._session = requests.Session()                                  # session to use in requests
        self._session.headers.update({'Authorization': f'Bearer {self.tokens.access_token}'})
        self._session_lock = threading.RLock()

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        if self.tokens.update_tokens():
            with self._session_lock:
                self._session.headers['Authorization'] = f'Bearer {self.tokens.access_token}'
        with self._session_lock:
            return self._session.request(method, f'{self._base_api_url}{path}', timeout=self.timeout, **kwargs)

    def close(self):
        with self._session_lock:
            try:
                self._session.close()
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.close()

    def __del__(self):
        self.close()
        
    """
    Accounts and Trading Production
    """

    def linked_accounts(self) -> requests.Response:
        """
        Account numbers in plain text cannot be used outside of headers or request/response bodies.
        As the first step consumers must invoke this service to retrieve the list of plain text/encrypted value pairs, and use encrypted account values for all subsequent calls for any accountNumber request.

        Return:
            request.Response: All linked account numbers and hashes
        """
        return self._request('GET', '/trader/v1/accounts/accountNumbers')

    def account_details_all(self, fields: str | None = None) -> requests.Response:
        """
        All the linked account information for the user logged in. The balances on these accounts are displayed by default however the positions on these accounts will be displayed based on the "positions" flag.

        Args:
            fields (str | None): fields to return (options: "positions")

        Returns:
            request.Response: details for all linked accounts
        """
        return self._request('GET', '/trader/v1/accounts/', 
                             params=self._parse_params({'fields': fields}))

    def account_details(self, accountHash: str, fields: str | None = None) -> requests.Response:
        """
        Specific account information with balances and positions. The balance information on these accounts is displayed by default but Positions will be returned based on the "positions" flag.

        Args:
            accountHash (str): account hash from account_linked()
            fields (str | None): fields to return

        Returns:
            request.Response: details for one linked account
        """
        return self._request('GET', f'/trader/v1/accounts/{accountHash}', 
                             params=self._parse_params({'fields': fields}))

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
        return self._request("GET", f'/trader/v1/accounts/{accountHash}/orders', 
                             params=self._parse_params({'fromEnteredTime': self._time_convert(fromEnteredTime, TimeFormat.ISO_8601), 
                                                         'toEnteredTime': self._time_convert(toEnteredTime, TimeFormat.ISO_8601), 
                                                         'maxResults': maxResults, 
                                                         'status': status}))
    
    def place_order(self, accountHash: str, order: dict) -> requests.Response:
        """
        Place an order for a specific account.

        Args:
            accountHash (str): account hash from account_linked()
            order (dict): order dictionary (format examples in github documentation)

        Returns:
            request.Response: order number in response header (if immediately filled then order number not returned)
        """
        return self._request("POST", f'/trader/v1/accounts/{accountHash}/orders', 
                             headers={"Accept": "application/json", "Content-Type": "application/json"}, 
                             json=order)

    def order_details(self, accountHash: str, orderId: int | str) -> requests.Response:
        """
        Get a specific order by its ID, for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id

        Returns:
            request.Response: order details
        """
        return self._request("GET", f'/trader/v1/accounts/{accountHash}/orders/{orderId}')

    def cancel_order(self, accountHash: str, orderId: int | str) -> requests.Response:
        """
        Cancel a specific order by its ID, for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id

        Returns:
            request.Response: response code
        """
        return self._request("DELETE", f'/trader/v1/accounts/{accountHash}/orders/{orderId}')

    def replace_order(self, accountHash: str, orderId: int | str, order: dict) -> requests.Response:
        """
        Replace an existing order for an account. The existing order will be replaced by the new order. Once replaced, the old order will be canceled and a new order will be created.

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id
            order (dict): order dictionary (format examples in github documentation)

        Returns:
            request.Response: response code
        """
        return self._request("PUT", f'/trader/v1/accounts/{accountHash}/orders/{orderId}', 
                             headers={"Accept": "application/json", "Content-Type": "application/json"}, 
                             json=order)

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
        return self._request("GET", '/trader/v1/orders', 
                             headers={"Accept": "application/json"},
                             params=self._parse_params({'fromEnteredTime': self._time_convert(fromEnteredTime, TimeFormat.ISO_8601), 
                                                         'toEnteredTime': self._time_convert(toEnteredTime, TimeFormat.ISO_8601), 
                                                         'maxResults': maxResults, 
                                                         'status': status}))

    def preview_order(self, accountHash: str, orderObject: dict) -> requests.Response:
        """
        Preview an order for a specific account.

        Args:
            accountHash (str): account hash from account_linked()
        """
        return self._request("POST", f'/trader/v1/accounts/{accountHash}/previewOrder',
                             headers={'Content-Type': 'application/json'}, json=orderObject)


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
        return self._request("GET", f'/trader/v1/accounts/{accountHash}/transactions',
                             params=self._parse_params({'startDate': self._time_convert(startDate, TimeFormat.ISO_8601), 
                                                         'endDate': self._time_convert(endDate, TimeFormat.ISO_8601), 
                                                         'types': types,
                                                         'symbol': symbol}))

    def transaction_details(self, accountHash: str, transactionId: str | int) -> requests.Response:
        """
        Get specific transaction information for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            transactionId (str | int): transaction id

        Returns:
            request.Response: transaction details of transaction id using accountHash
        """
        return self._request("GET", f'/trader/v1/accounts/{accountHash}/transactions/{transactionId}')

    def preferences(self) -> requests.Response:
        """
        Get user preference information for the logged in user.

        Returns:
            request.Response: User preferences and streaming info
        """
        return self._request("GET", '/trader/v1/userPreference')

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
        return self._request("GET", '/marketdata/v1/quotes',
                             params=self._parse_params({'symbols': self._format_list(symbols),
                                                         'fields': fields,
                                                         'indicative': indicative}))

    def quote(self, symbol_id: str, fields: str | None = None) -> requests.Response:
        """
        Get quote for a single symbol

        Args:
            symbol_id (str): ticker symbol
            fields (str): fields to get ("all", "quote", "fundamental")

        Returns:
            request.Response: quote for a single symbol
        """
        return self._request("GET", f'/marketdata/v1/{urllib.parse.quote(symbol_id,safe="")}/quotes', 
                             params=self._parse_params({'fields': fields}))

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
        return self._request("GET", '/marketdata/v1/chains',
                            params=self._parse_params(
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
                                 'entitlement': entitlement}))

    def option_expiration_chain(self, symbol: str) -> requests.Response:
        """
        Get an option expiration chain for a ticker

        Args:
            symbol (str): Ticker symbol

        Returns:
            request.Response: Option expiration chain
        """
        return self._request("GET", '/marketdata/v1/expirationchain', 
                             params=self._parse_params({'symbol': symbol}))

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
        return self._request("GET", '/marketdata/v1/pricehistory',
                             params=self._parse_params({'symbol': symbol,
                                                         'periodType': periodType,
                                                         'period': period,
                                                         'frequencyType': frequencyType,
                                                         'frequency': frequency,
                                                         'startDate': self._time_convert(startDate, TimeFormat.EPOCH_MS),
                                                         'endDate': self._time_convert(endDate, TimeFormat.EPOCH_MS),
                                                         'needExtendedHoursData': needExtendedHoursData,
                                                         'needPreviousClose': needPreviousClose}))
    

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
        return self._request("GET", f'/marketdata/v1/movers/{symbol}', 
                             headers={"accept": "application/json"}, 
                             params=self._parse_params({'sort': sort, 'frequency': frequency}))

    def market_hours(self, symbols: list[str], date: datetime.datetime | str | None = None) -> requests.Response:
        """
        Get Market Hours for dates in the future across different markets.

        Args:
            symbols (list[str]): list of market symbols ("equity", "option", "bond", "future", "forex")
            date (datetime.pyi | str): Date

        Returns:
            request.Response: Market hours
        """
        return self._request("GET", '/marketdata/v1/markets', 
                             params=self._parse_params({'markets': self._format_list(symbols), 
                                                         'date': self._time_convert(date, TimeFormat.YYYY_MM_DD)}))

    def market_hour(self, market_id: str, date: datetime.datetime | str | None = None) -> requests.Response:
        """
        Get Market Hours for dates in the future for a single market.

        Args:
            market_id (str): market id ("equity"|"option"|"bond"|"future"|"forex")
            date (datetime.pyi | str): date

        Returns:
            request.Response: Market hours
        """
        return self._request("GET", f'/marketdata/v1/markets/{market_id}', 
                             params=self._parse_params({'date': self._time_convert(date, TimeFormat.YYYY_MM_DD)}))

    def instruments(self, symbols: str, projection: str) -> requests.Response:
        """
        Get instruments for a list of symbols

        Args:
            symbol (str): symbol
            projection (str): projection ("symbol-search"|"symbol-regex"|"desc-search"|"desc-regex"|"search"|"fundamental")

        Returns:
            request.Response: Instruments
        """
        return self._request("GET", '/marketdata/v1/instruments', 
                             params={'symbol': self._format_list(symbols), 'projection': projection})

    def instrument_cusip(self, cusip_id: str | int) -> requests.Response:
        """
        Get instrument for a single cusip

        Args:
            cusip_id (str|int): cusip id

        Returns:
            request.Response: Instrument
        """
        return self._request("GET", f'/marketdata/v1/instruments/{cusip_id}')

class ClientAsync(ClientBase):

    def __init__(self, app_key, app_secret, callback_url="https://127.0.0.1", tokens_db="~/.schwabdev/tokens.db", timeout=10, parsed:bool = False, capture_callback=False, call_on_auth=None):
        if aiohttp is None:
            raise ImportError("aiohttp is required to use ClientAsync")
        super().__init__(app_key, app_secret, callback_url, tokens_db, timeout, capture_callback, call_on_auth)
        self._parsed = parsed
        self._session = self._get_session()                              

    def _get_session(self) -> aiohttp.ClientSession:
        return aiohttp.ClientSession(base_url=self._base_api_url,
                                     headers={'Authorization': f'Bearer {self.tokens.access_token}'}, 
                                     timeout=aiohttp.ClientTimeout(total=self.timeout))

    async def _checker(self):
        while True:
            if self.tokens.update_tokens():
                await self._session.close()
                self._session = self._get_session()
            await asyncio.sleep(30)

    async def __aenter__(self):
        self._task_group = asyncio.TaskGroup()
        await self._task_group.__aenter__()
        self._checker_task = self._task_group.create_task(self._checker()) # Start the token checker in the background
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self._checker_task.cancel()
        await asyncio.shield(self._session.close())
        retval = await self._task_group.__aexit__(exc_type, exc_val, exc_tb)
        return retval
    
    async def _parse_response(self, response: aiohttp.ClientResponse, parsed: bool = None) -> aiohttp.ClientResponse | dict:
        if (parsed is None and self._parsed) or (parsed is True):
            content_type = response.headers.get("Content-Type", "").lower()
            if content_type.startswith("application/json"):
                return await response.json()
            else: # assume "text/html" | "text/plain" | etc.
                return await response.text()
        else:
            return response
            
    def _handle_aiohttp_bool(self, value: bool) -> str:
        if value is None: return None
        return "true" if value else "false"

    """
    Accounts and Trading Production
    """

    async def linked_accounts(self, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Account numbers in plain text cannot be used outside of headers or request/response bodies.
        As the first step consumers must invoke this service to retrieve the list of plain text/encrypted value pairs, and use encrypted account values for all subsequent calls for any accountNumber request.

        Return:
            aiohttp.ClientResponse: All linked account numbers and hashes
        """
        return await self._parse_response(
            await self._session.get('/trader/v1/accounts/accountNumbers'),
            parsed,
        )

    async def account_details_all(self, fields: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        All the linked account information for the user logged in. The balances on these accounts are displayed by default however the positions on these accounts will be displayed based on the "positions" flag.

        Args:
            fields (str | None): fields to return (options: "positions")

        Returns:
            aiohttp.ClientResponse: details for all linked accounts
        """
        return await self._parse_response(
            await self._session.get(
                '/trader/v1/accounts/',
                params=self._parse_params({'fields': fields}),
            ),
            parsed,
        )
        
    async def account_details(self, accountHash: str, fields: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Specific account information with balances and positions. The balance information on these accounts is displayed by default but Positions will be returned based on the "positions" flag.

        Args:
            accountHash (str): account hash from account_linked()
            fields (str | None): fields to return

        Returns:
            aiohttp.ClientResponse: details for one linked account
        """
        return await self._parse_response(
            await self._session.get(
                f'/trader/v1/accounts/{accountHash}',
                params=self._parse_params({'fields': fields}),
            ),
            parsed,
        )

    async def account_orders(self, accountHash: str, 
                             fromEnteredTime: datetime.datetime | str, 
                             toEnteredTime: datetime.datetime | str, 
                             maxResults: int = None, status: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        All orders for a specific account. Orders retrieved can be filtered based on input parameters below. Maximum date range is 1 year.

        Args:
            accountHash (str): account hash from account_linked()
            fromEnteredTime (datetime.datetime | str): start date
            toEnteredTime (datetime.datetime | str): end date
            maxResults (int | None): maximum number of results (set to None for default 3000)
            status (str | None): status of order

        Returns:
            aiohttp.ClientResponse: orders for one linked account
        """
        return await self._parse_response(
            await self._session.get(
                f'/trader/v1/accounts/{accountHash}/orders',
                headers={"Accept": "application/json"},
                params=self._parse_params(
                    {
                        'maxResults': maxResults,
                        'fromEnteredTime': self._time_convert(fromEnteredTime, "8601"),
                        'toEnteredTime': self._time_convert(toEnteredTime, "8601"),
                        'status': status,
                    }
                ),
            ),
            parsed,
        )

    async def place_order(self, accountHash: str, order: dict) -> aiohttp.ClientResponse:
        """
        Place an order for a specific account.

        Args:
            accountHash (str): account hash from account_linked()
            order (dict): order dictionary (format examples in github documentation)

        Returns:
            aiohttp.ClientResponse: order number in response header (if immediately filled then order number not returned)
        """
        return await self._parse_response(
            await self._session.post(
                f'/trader/v1/accounts/{accountHash}/orders',
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json=order,
            ),
            False, # must be raw to get headers
        )

    async def order_details(self, accountHash: str, orderId: int | str, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get a specific order by its ID, for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id

        Returns:
            aiohttp.ClientResponse: order details
        """
        return await self._parse_response(
            await self._session.get(
                f'/trader/v1/accounts/{accountHash}/orders/{orderId}',
            ),
            parsed,
        )


    async def cancel_order(self, accountHash: str, orderId: int | str, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Cancel a specific order by its ID, for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id

        Returns:
            aiohttp.ClientResponse: response code
        """
        return await self._parse_response(
            await self._session.delete(
                f'/trader/v1/accounts/{accountHash}/orders/{orderId}',
            ),
            parsed,
        )
    async def replace_order(self, accountHash: str, orderId: int | str, order: dict) -> aiohttp.ClientResponse:
        """
        Replace an existing order for an account. The existing order will be replaced by the new order. Once replaced, the old order will be canceled and a new order will be created.

        Args:
            accountHash (str): account hash from account_linked()
            orderId (int | str): order id
            order (dict): order dictionary (format examples in github documentation)

        Returns:
            aiohttp.ClientResponse: response code
        """
        return await self._parse_response(
            await self._session.put(
                f'/trader/v1/accounts/{accountHash}/orders/{orderId}',
                headers={"Accept": "application/json", "Content-Type": "application/json"},
                json=order,
            ),
            False, # must be raw to get headers
        )

    async def account_orders_all(self, fromEnteredTime: datetime.datetime | str, 
                                 toEnteredTime: datetime.datetime | str, 
                                 maxResults: int = None, status: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get all orders for all accounts

        Args:
            fromEnteredTime (datetime.datetime | str): start date
            toEnteredTime (datetime.datetime | str): end date
            maxResults (int | None): maximum number of results (set to None for default 3000)
            status (str | None): status of order (see documentation for possible values)

        Returns:
            aiohttp.ClientResponse: all orders
        """
        return await self._parse_response(
            await self._session.get(
                '/trader/v1/orders',
                headers={"Accept": "application/json"},
                params=self._parse_params(
                    {
                        'maxResults': maxResults,
                        'fromEnteredTime': self._time_convert(fromEnteredTime, "8601"),
                        'toEnteredTime': self._time_convert(toEnteredTime, "8601"),
                        'status': status,
                    }
                ),
            ),
            parsed,
        )


    async def preview_order(self, accountHash: str, orderObject: dict, parsed: bool = None) -> aiohttp.ClientResponse:
        return await self._parse_response(
            await self._session.post(
                f'/trader/v1/accounts/{accountHash}/previewOrder',
                headers={'Content-Type': 'application/json'},
                json=orderObject,
            ),            
            parsed,
        )
        


    async def transactions(self, accountHash: str, startDate: datetime.datetime | str, 
                           endDate: datetime.datetime | str, types: str, symbol: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        All transactions for a specific account. Maximum number of transactions in response is 3000. Maximum date range is 1 year.

        Args:
            accountHash (str): account hash from account_linked()
            startDate (datetime.datetime | str): start date
            endDate (datetime.datetime | str): end date
            types (str): transaction type (see documentation for possible values)
            symbol (str | None): symbol

        Returns:
            aiohttp.ClientResponse: list of transactions for a specific account
        """
        return await self._parse_response(
            await self._session.get(
                f'/trader/v1/accounts/{accountHash}/transactions',
                params=self._parse_params(
                    {
                        'startDate': self._time_convert(startDate, "8601"),
                        'endDate': self._time_convert(endDate, "8601"),
                        'symbol': symbol,
                        'types': types,
                    }
                ),
            ),
            parsed,
        )

    async def transaction_details(self, accountHash: str, transactionId: str | int, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get specific transaction information for a specific account

        Args:
            accountHash (str): account hash from account_linked()
            transactionId (str | int): transaction id

        Returns:
            aiohttp.ClientResponse: transaction details of transaction id using accountHash
        """
        return await self._parse_response(
            await self._session.get(
                f'/trader/v1/accounts/{accountHash}/transactions/{transactionId}',
            ),
            parsed,
        )

    async def preferences(self, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get user preference information for the logged in user.

        Returns:
            aiohttp.ClientResponse: User preferences and streaming info
        """
        return await self._parse_response(
            await self._session.get('/trader/v1/userPreference'),
            parsed,
        )


    """
    Market Data
    """

    async def quotes(self, symbols : list[str] | str, fields: str = None, indicative: bool = False, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get quotes for a list of tickers

        Args:
            symbols (list[str] | str): list of symbols strings (e.g. "AMD,INTC" or ["AMD", "INTC"])
            fields (str): fields to get ("all", "quote", "fundamental")
            indicative (bool): whether to get indicative quotes (True/False)

        Returns:
            aiohttp.ClientResponse: list of quotes
        """
        return await self._parse_response(
            await self._session.get(
                '/marketdata/v1/quotes',
                params=self._parse_params(
                    {
                        'symbols': self._format_list(symbols),
                        'fields': fields,
                        'indicative': self._handle_aiohttp_bool(indicative),
                    }
                ),
            ),
            parsed,
        )

    async def quote(self, symbol_id: str, fields: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get quote for a single symbol

        Args:
            symbol_id (str): ticker symbol
            fields (str): fields to get ("all", "quote", "fundamental")

        Returns:
            aiohttp.ClientResponse: quote for a single symbol
        """
        return await self._parse_response(
            await self._session.get(
                f'/marketdata/v1/{urllib.parse.quote(symbol_id, safe="")}/quotes',
                params=self._parse_params({'fields': fields}),
            ),
            parsed,
        )

    async def option_chains(self, symbol: str, contractType: str = None, strikeCount: any = None, includeUnderlyingQuote: bool = None, strategy: str = None,
               interval: any = None, strike: any = None, range: str = None, fromDate: datetime.datetime | str = None, toDate: datetime.datetime | str = None, volatility: any = None, underlyingPrice: any = None,
               interestRate: any = None, daysToExpiration: any = None, expMonth: str = None, optionType: str = None, entitlement: str = None, parsed: bool = None) -> aiohttp.ClientResponse:
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
            aiohttp.ClientResponse: option chain
        """
        return await self._parse_response(
            await self._session.get(
                '/marketdata/v1/chains',
                params=self._parse_params(
                    {
                        'symbol': symbol,
                        'contractType': contractType,
                        'strikeCount': strikeCount,
                        'includeUnderlyingQuote': self._handle_aiohttp_bool(includeUnderlyingQuote),
                        'strategy': strategy,
                        'interval': interval,
                        'strike': strike,
                        'range': range,
                        'fromDate': self._time_convert(fromDate, "YYYY-MM-DD"),
                        'toDate': self._time_convert(toDate, "YYYY-MM-DD"),
                        'volatility': volatility,
                        'underlyingPrice': underlyingPrice,
                        'interestRate': interestRate,
                        'daysToExpiration': daysToExpiration,
                        'expMonth': expMonth,
                        'optionType': optionType,
                        'entitlement': entitlement,
                    }
                ),
            ),
            parsed,
        )


    async def option_expiration_chain(self, symbol: str, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get an option expiration chain for a ticker

        Args:
            symbol (str): Ticker symbol

        Returns:
            aiohttp.ClientResponse: Option expiration chain
        """
        return await self._parse_response(
            await self._session.get(
                '/marketdata/v1/expirationchain',
                params=self._parse_params({'symbol': symbol}),
            ),
            parsed,
        )
        
    async def price_history(self, symbol: str, periodType: str = None, period: any = None, frequencyType: str = None, frequency: any = None, startDate: datetime.datetime | str = None,
                        endDate: any = None, needExtendedHoursData: bool = None, needPreviousClose: bool = None, parsed: bool = None) -> aiohttp.ClientResponse:
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
                aiohttp.ClientResponse: Dictionary containing candle history
            """
            return await self._parse_response(
            await self._session.get(
                '/marketdata/v1/pricehistory',
                params=self._parse_params(
                    {
                        'symbol': symbol,
                        'periodType': periodType,
                        'period': period,
                        'frequencyType': frequencyType,
                        'frequency': frequency,
                        'startDate': self._time_convert(startDate, 'epoch_ms'),
                        'endDate': self._time_convert(endDate, 'epoch_ms'),
                        'needExtendedHoursData': self._handle_aiohttp_bool(needExtendedHoursData),
                        'needPreviousClose': self._handle_aiohttp_bool(needPreviousClose),
                    }
                ),
            ),
            parsed,
        )

    async def movers(self, symbol: str, sort: str = None, frequency: any = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get movers in a specific index and direction

        Args:
            symbol (str): symbol ("$DJI"|"$COMPX"|"$SPX"|"NYSE"|"NASDAQ"|"OTCBB"|"INDEX_ALL"|"EQUITY_ALL"|"OPTION_ALL"|"OPTION_PUT"|"OPTION_CALL")
            sort (str): sort ("VOLUME"|"TRADES"|"PERCENT_CHANGE_UP"|"PERCENT_CHANGE_DOWN")
            frequency (int): frequency (0|1|5|10|30|60)

        Notes:
            Must be called within market hours (there aren't really movers outside of market hours)

        Returns:
            aiohttp.ClientResponse: Movers
        """
        return await self._parse_response(
            await self._session.get(
                f'/marketdata/v1/movers/{symbol}',
                headers={"accept": "application/json"},
                params=self._parse_params({'sort': sort, 'frequency': frequency}),
            ),
            parsed,
        )

    async def market_hours(self, symbols: list[str], date: datetime.datetime | str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get Market Hours for dates in the future across different markets.

        Args:
            symbols (list[str]): list of market symbols ("equity", "option", "bond", "future", "forex")
            date (datetime.pyi | str): Date

        Returns:
            aiohttp.ClientResponse: Market hours
        """
        return await self._parse_response(
            await self._session.get(
                '/marketdata/v1/markets',
                params=self._parse_params(
                    {
                        'markets': symbols,
                        'date': self._time_convert(date, 'YYYY-MM-DD'),
                    }
                ),
            ),
            parsed,
        )

    async def market_hour(self, market_id: str, date: datetime.datetime | str = None, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get Market Hours for dates in the future for a single market.

        Args:
            market_id (str): market id ("equity"|"option"|"bond"|"future"|"forex")
            date (datetime.pyi | str): date

        Returns:
            aiohttp.ClientResponse: Market hours
        """
        return await self._parse_response(
            await self._session.get(
                f'/marketdata/v1/markets/{market_id}',
                params=self._parse_params({'date': self._time_convert(date, 'YYYY-MM-DD')}),
            ),
            parsed,
        )

    async def instruments(self, symbol: str, projection: str, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get instruments for a list of symbols

        Args:
            symbol (str): symbol
            projection (str): projection ("symbol-search"|"symbol-regex"|"desc-search"|"desc-regex"|"search"|"fundamental")

        Returns:
            aiohttp.ClientResponse: Instruments
        """
        return await self._parse_response(
            await self._session.get(
                '/marketdata/v1/instruments',
                params={'symbol': symbol, 'projection': projection},
            ),
            parsed,
        )

    async def instrument_cusip(self, cusip_id: str | int, parsed: bool = None) -> aiohttp.ClientResponse:
        """
        Get instrument for a single cusip

        Args:
            cusip_id (str|int): cusip id

        Returns:
            aiohttp.ClientResponse: Instrument
        """
        return await self._parse_response(
            await self._session.get(
                f'/marketdata/v1/instruments/{cusip_id}',
            ),
            parsed,
        )
