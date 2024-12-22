"""
This file contains functions to create a client class that accesses the Schwab api
Coded by Tyler Bowers
Github: https://github.com/tylerebowers/Schwab-API-Python
"""

import datetime
import logging
import urllib.parse

import requests

from .stream import Stream
from .tokens import Tokens


class Client:
    def __init__(
        self,
        app_key: str,
        app_secret: str,
        callback_url: str = "https://127.0.0.1",
        tokens_file: str = "tokens.json",
        timeout: int = 5,
        update_tokens_auto: bool = True,
    ):
        """Initialize a client to access the Schwab API.

        Args:
            app_key (str): App key credentials.
            app_secret (str): App secret credentials.
            callback_url (str): URL for callback.
            tokens_file (str): Path to tokens file.
            timeout (int): Request timeout.
            update_tokens_auto (bool): Update tokens automatically.
        """

        if timeout <= 0:
            raise Exception("Timeout must be greater than 0 and is recommended to be 5 seconds or more.")

        self.version = "Schwabdev 2.4.4"                        # version of the client
        self.timeout = timeout                                  # timeout to use in requests
        self.tokens = Tokens(self, app_key, app_secret, callback_url, tokens_file, update_tokens_auto)
        self.stream = Stream(self)                              # init the streaming object
        self._logger = logging.getLogger("Schwabdev.Client")    # init the logger

        self._logger.info("Client Initialization Complete")


    def _params_parser(self, params: dict) -> dict:
        """Removes None (null) values from the given dictionary.

        Args:
            params (dict): The dictionary to remove None values from.

        Returns:
            dict: The dictionary without None values.

        """
        for key in list(params.keys()):
            if params[key] is None: del params[key]
        return params

    def _time_convert(self, dt=None, format: str="8601") -> str | int | None:
        """Convert time to correct format, passthrough if a string, preserve None if None for params parser.

        Args:
            dt (datetime.datetime | str | None): Datetime object to convert.
            form (str): Format to convert input to.

        Returns:
            str | None: Converted time or passthrough.
        """
        if dt is None or not isinstance(dt, datetime.datetime):
            return dt
        elif format == "8601":  # assume datetime object from here on
            return f"{dt.isoformat().split('+')[0][:-3]}Z"
        elif format == "epoch":
            return int(dt.timestamp())
        elif format == "epoch_ms":
            return int(dt.timestamp() * 1000)
        elif format == "YYYY-MM-DD":
            return dt.strftime("%Y-%m-%d")
        else:
            return dt

    def _format_list(self, l: list | str | None) -> str | None:
        """Convert a Python list to a string or passthrough if already a string.

        i.e. ["a", "b"] -> "a,b"

        Args:
            l (list | str | None): The list to convert.

        Returns:
            str | None: The converted string or passthrough.
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
        Retrieve the list of plain text/encrypted value pairs for account numbers.

        Account numbers in plain text cannot be used outside of headers or request/response bodies.
        As the first step, consumers must invoke this service to retrieve the list of plain text/encrypted
        value pairs and use encrypted account values for all subsequent calls for any accountNumber request.

        Returns:
            requests.Response: All linked account numbers and hashes.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/accountNumbers',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    def account_details_all(self, fields: str = None) -> requests.Response:
        """
        Retrieve all linked account information for the logged-in user.

        The balances on these accounts are displayed by default. The positions on these accounts will be displayed based on the "positions" flag.

        Args:
            fields (str, optional): Fields to return (options: "positions").

        Returns:
            requests.Response: Details for all linked accounts.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)

    def account_details(self, accountHash: str, fields: str | None = None) -> requests.Response:
        """
        Specific account information with balances and positions.

        The balance information on these accounts is displayed by default but Positions will be returned based on the "positions" flag.

        Args:
            accountHash (str): Account hash from account_linked().
            fields (str, optional): Fields to return.

        Returns:
            requests.Response: Details for one linked account.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)

    def account_orders(
            self,
            accountHash: str,
            fromEnteredTime: datetime.datetime | str,
            toEnteredTime: datetime.datetime | str,
            maxResults: int = None,
            status: str = None
        ) -> requests.Response:
        """
        Retrieve all orders for a specific account.

        Orders retrieved can be filtered based on input parameters below. Maximum date range is 1 year.

        Args:
            accountHash (str): Account hash from account_linked().
            fromEnteredTime (datetime.datetime | str): From entered time.
            toEnteredTime (datetime.datetime | str): To entered time.
            maxResults (int, optional): Maximum number of results.
            status (str, optional): Status ("AWAITING_PARENT_ORDER", "AWAITING_CONDITION", "AWAITING_STOP_CONDITION",
                "AWAITING_MANUAL_REVIEW", "ACCEPTED", "AWAITING_UR_OUT", "PENDING_ACTIVATION", "QUEUED", "WORKING",
                "REJECTED", "PENDING_CANCEL", "CANCELED", "PENDING_REPLACE", "REPLACED", "FILLED", "EXPIRED", "NEW",
                "AWAITING_RELEASE_TIME", "PENDING_ACKNOWLEDGEMENT", "PENDING_RECALL", "UNKNOWN").

        Returns:
            requests.Response: Orders for one linked account hash.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders',
                            headers={"Accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'maxResults': maxResults, 'fromEnteredTime': self._time_convert(fromEnteredTime, "8601"),
                                 'toEnteredTime': self._time_convert(toEnteredTime, "8601"), 'status': status}),
                            timeout=self.timeout)

    def order_place(self, accountHash: str, order: dict) -> requests.Response:
        """
        Place an order for a specific account.

        Args:
            accountHash (str): Account hash from account_linked().
            order (dict): Order dictionary, examples in Schwab docs.

        Returns:
            requests.Response: Order number in response header (if immediately filled then order number not returned).
        """
        return requests.post(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders',
                             headers={"Accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}',
                                      "Content-Type": "application/json"},
                             json=order,
                             timeout=self.timeout)

    def order_details(self, accountHash: str, orderId: int | str) -> requests.Response:
        """
        Get a specific order by its ID, for a specific account.

        Args:
            accountHash (str): Account hash from account_linked().
            orderId (int | str): Order ID.

        Returns:
            requests.Response: Order details.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders/{orderId}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    def order_cancel(self, accountHash: str, orderId: int | str) -> requests.Response:
        """
        Cancel a specific order by its ID, for a specific account.

        Args:
            accountHash (str): Account hash from account_linked().
            orderId (int | str): Order ID.

        Returns:
            requests.Response: Response code.
        """
        return requests.delete(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders/{orderId}',
                               headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                               timeout=self.timeout)

    def order_replace(self, accountHash: str, orderId: int | str, order: dict) -> requests.Response:
        """
        Replace an existing order for an account.

        The existing order will be replaced by the new order.
        Once replaced, the old order will be canceled and a new order will be created.

        Args:
            accountHash (str): Account hash from account_linked().
            orderId (int | str): Order ID.
            order (dict): Order dictionary, examples in Schwab docs.

        Returns:
            requests.Response: Response code.
        """
        return requests.put(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/orders/{orderId}',
                            headers={"Accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}',
                                     "Content-Type": "application/json"},
                            json=order,
                            timeout=self.timeout)

    def account_orders_all(
        self,
        fromEnteredTime: datetime.datetime | str,
        toEnteredTime: datetime.datetime | str,
        maxResults: int | None = None,
        status: str | None = None,
    ) -> requests.Response:
        """
        Get all orders for all accounts.

        Args:
            fromEnteredTime (datetime.datetime | str): Start date.
            toEnteredTime (datetime.datetime | str): End date.
            maxResults (int, optional): Maximum number of results (set to None for default 3000).
            status (str, optional): Status ("AWAITING_PARENT_ORDER", "AWAITING_CONDITION", "AWAITING_STOP_CONDITION",
                "AWAITING_MANUAL_REVIEW", "ACCEPTED", "AWAITING_UR_OUT", "PENDING_ACTIVATION", "QUEUED", "WORKING",
                "REJECTED", "PENDING_CANCEL", "CANCELED", "PENDING_REPLACE", "REPLACED", "FILLED", "EXPIRED", "NEW",
                "AWAITING_RELEASE_TIME", "PENDING_ACKNOWLEDGEMENT", "PENDING_RECALL", "UNKNOWN").

        Returns:
            requests.Response: All orders.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/orders',
                            headers={"Accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'maxResults': maxResults, 'fromEnteredTime': self._time_convert(fromEnteredTime, "8601"),
                                 'toEnteredTime': self._time_convert(toEnteredTime, "8601"), 'status': status}),
                            timeout=self.timeout)

    """
    def order_preview(self, accountHash, orderObject) -> requests.Response:
        #COMING SOON (waiting on Schwab)
        return requests.post(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/previewOrder',
                             headers={'Authorization': f'Bearer {self.tokens.access_token}',
                                      "Content-Type": "application.json"}, data=orderObject)
    """

    def transactions(
        self,
        accountHash: str,
        startDate: datetime.datetime | str,
        endDate: datetime.datetime | str,
        types: str,
        symbol: str | None = None,
    ) -> requests.Response:
        """
        Retrieve all transactions for a specific account. Maximum number of transactions in response is 3000. Maximum date range is 1 year.

        Args:
            accountHash (str): Account hash number.
            startDate (datetime.datetime | str): Start date.
            endDate (datetime.datetime | str): End date.
            types (str): Transaction type ("TRADE, RECEIVE_AND_DELIVER, DIVIDEND_OR_INTEREST, ACH_RECEIPT, ACH_DISBURSEMENT, CASH_RECEIPT, CASH_DISBURSEMENT, ELECTRONIC_FUND, WIRE_OUT, WIRE_IN, JOURNAL, MEMORANDUM, MARGIN_CALL, MONEY_MARKET, SMA_ADJUSTMENT").
            symbol (str, optional): Symbol.

        Returns:
            requests.Response: List of transactions for a specific account.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/transactions',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'accountNumber': accountHash, 'startDate': self._time_convert(startDate, "8601"),
                                 'endDate': self._time_convert(endDate, "8601"), 'symbol': symbol, 'types': types}),
                            timeout=self.timeout)

    def transaction_details(self, accountHash: str, transactionId: str | int) -> requests.Response:
        """
        Get specific transaction information for a specific account.

        Args:
            accountHash (str): Account hash number.
            transactionId (str | int): Transaction ID.

        Returns:
            requests.Response: Transaction details of the transaction ID using accountHash.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/accounts/{accountHash}/transactions/{transactionId}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params={'accountNumber': accountHash, 'transactionId': transactionId},
                            timeout=self.timeout)

    def preferences(self) -> requests.Response:
        """
        Get user preference information for the logged in user.

        Returns:
            requests.Response: User Preferences and Streaming Info.
        """
        return requests.get(f'{self._base_api_url}/trader/v1/userPreference',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)

    """
    Market Data
    """

    def quotes(self, symbols : list[str] | str, fields: str | None = None, indicative: bool = False) -> requests.Response:
        """
        Get quotes for a list of tickers.

        Args:
            symbols (list[str] | str): List of symbols strings (e.g. "AMD,INTC" or ["AMD", "INTC"]).
            fields (str, optional): String of fields to get ("all", "quote", "fundamental").
            indicative (bool, optional): Whether to get indicative quotes (True/False).

        Returns:
            requests.Response: List of quotes.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/quotes',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'symbols': self._format_list(symbols), 'fields': fields, 'indicative': indicative}),
                            timeout=self.timeout)

    def quote(self, symbol_id: str, fields: str | None= None) -> requests.Response:
        """
        Get quote for a single symbol.

        Args:
            symbol_id (str): Ticker symbol (e.g. "AAPL", "/ES", "USD/EUR").
            fields (str, optional): String of fields to get ("all", "quote", "fundamental").

        Returns:
            requests.Response: Quote for a single symbol.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/{urllib.parse.quote(symbol_id,safe="")}/quotes',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'fields': fields}),
                            timeout=self.timeout)

    def option_chains(
        self,
        symbol: str,
        contractType: str = None,
        strikeCount: any = None,
        includeUnderlyingQuote: bool = None,
        strategy: str = None,
        interval: any = None,
        strike: any = None,
        range: str = None,
        fromDate: datetime.datetime | str = None,
        toDate: datetime.datetime | str = None,
        volatility: any = None,
        underlyingPrice: any = None,
        interestRate: any = None,
        daysToExpiration: any = None,
        expMonth: str = None,
        optionType: str = None,
        entitlement: str = None,
    ) -> requests.Response:
        """
        Get Option Chain including information on options contracts associated with each expiration for a ticker.

        Args:
            symbol (str): Ticker symbol.
            contractType (str, optional): Contract type ("CALL"|"PUT"|"ALL").
            strikeCount (int, optional): Strike count.
            includeUnderlyingQuote (bool, optional): Include underlying quote (True|False).
            strategy (str, optional): Strategy ("SINGLE"|"ANALYTICAL"|"COVERED"|"VERTICAL"|"CALENDAR"|"STRANGLE"|"STRADDLE"|"BUTTERFLY"|"CONDOR"|"DIAGONAL"|"COLLAR"|"ROLL).
            interval (str, optional): Strike interval.
            strike (float, optional): Strike price.
            range (str, optional): Range ("ITM"|"NTM"|"OTM"...).
            fromDate (datetime.datetime | str, optional): From date.
            toDate (datetime.datetime | str, optional): To date.
            volatility (float, optional): Volatility.
            underlyingPrice (float, optional): Underlying price.
            interestRate (float, optional): Interest rate.
            daysToExpiration (int, optional): Days to expiration.
            expMonth (str, optional): Expiration month ("JAN"|"FEB"|"MAR"|"APR"|"MAY"|"JUN"|"JUL"|"AUG"|"SEP"|"OCT"|"NOV"|"DEC"|"ALL").
            optionType (str, optional): Option type ("CALL"|"PUT").
            entitlement (str, optional): Entitlement ("PN"|"NP"|"PP").

        Returns:
            requests.Response: List of option chains.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/chains',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'symbol': symbol, 'contractType': contractType, 'strikeCount': strikeCount,
                                 'includeUnderlyingQuote': includeUnderlyingQuote, 'strategy': strategy,
                                 'interval': interval, 'strike': strike, 'range': range, 'fromDate': self._time_convert(fromDate, "YYYY-MM-DD"),
                                 'toDate': self._time_convert(toDate, "YYYY-MM-DD"), 'volatility': volatility, 'underlyingPrice': underlyingPrice,
                                 'interestRate': interestRate, 'daysToExpiration': daysToExpiration,
                                 'expMonth': expMonth, 'optionType': optionType, 'entitlement': entitlement}),
                            timeout=self.timeout)

    def option_expiration_chain(self, symbol: str) -> requests.Response:
        """
        Get an option expiration chain for a ticker.

        Args:
            symbol (str): Ticker symbol.

        Returns:
            requests.Response: Option expiration chain.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/expirationchain',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'symbol': symbol}),
                            timeout=self.timeout)

    def price_history(
        self,
        symbol: str,
        periodType: str = None,
        period: any = None,
        frequencyType: str = None,
        frequency: any = None,
        startDate: datetime.datetime | str = None,
        endDate: any = None,
        needExtendedHoursData: bool = None,
        needPreviousClose: bool = None,
    ) -> requests.Response:
        """
        Get price history for a ticker.

        Args:
            symbol (str): Ticker symbol.
            periodType (str, optional): Period type ("day"|"month"|"year"|"ytd").
            period (int, optional): Period.
            frequencyType (str, optional): Frequency type ("minute"|"daily"|"weekly"|"monthly").
            frequency (int, optional): Frequency (frequencyType: options), (minute: 1, 5, 10, 15, 30), (daily: 1), (weekly: 1), (monthly: 1).
            startDate (datetime.datetime | str, optional): Start date.
            endDate (datetime.datetime | str, optional): End date.
            needExtendedHoursData (bool, optional): Need extended hours data (True|False).
            needPreviousClose (bool, optional): Need previous close (True|False).

        Returns:
            requests.Response: Dictionary containing candle history.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/pricehistory',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'symbol': symbol, 'periodType': periodType, 'period': period,
                                                        'frequencyType': frequencyType, 'frequency': frequency,
                                                        'startDate': self._time_convert(startDate, 'epoch_ms'),
                                                        'endDate': self._time_convert(endDate, 'epoch_ms'),
                                                        'needExtendedHoursData': needExtendedHoursData,
                                                        'needPreviousClose': needPreviousClose}),
                            timeout=self.timeout)

    def movers(self, symbol: str, sort: str = None, frequency: any = None) -> requests.Response:
        """
        Get movers in a specific index and direction.

        Args:
            symbol (str): Symbol ("$DJI", "$COMPX", "$SPX", "NYSE", "NASDAQ", "OTCBB", "INDEX_ALL", "EQUITY_ALL", "OPTION_ALL", "OPTION_PUT", "OPTION_CALL").
            sort (str, optional): Sort ("VOLUME", "TRADES", "PERCENT_CHANGE_UP", "PERCENT_CHANGE_DOWN").
            frequency (int, optional): Frequency (0, 1, 5, 10, 30, 60).

        Returns:
            requests.Response: Movers.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/movers/{symbol}',
                            headers={"accept": "application/json", 'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'sort': sort, 'frequency': frequency}),
                            timeout=self.timeout)

    def market_hours(self, symbols: list[str], date: datetime.datetime | str = None) -> requests.Response:
        """
        Get Market Hours for dates in the future across different markets.

        Args:
            symbols (list[str]): List of market symbols ("equity", "option", "bond", "future", "forex").
            date (datetime.datetime | str, optional): Date.

        Returns:
            requests.Response: Market hours.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/markets',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser(
                                {'markets': symbols, #self._format_list(symbols),
                                 'date': self._time_convert(date, 'YYYY-MM-DD')}),
                            timeout=self.timeout)

    def market_hour(self, market_id: str, date: datetime.datetime | str = None) -> requests.Response:
        """
        Get Market Hours for dates in the future for a single market.

        Args:
            market_id (str): Market id ("equity"|"option"|"bond"|"future"|"forex").
            date (datetime.datetime | str, optional): Date.

        Returns:
            requests.Response: Market hours.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/markets/{market_id}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params=self._params_parser({'date': self._time_convert(date, 'YYYY-MM-DD')}),
                            timeout=self.timeout)

    def instruments(self, symbol: str, projection: str) -> requests.Response:
        """
        Get instruments for a list of symbols.

        Args:
            symbol (str): Symbol.
            projection (str): Projection ("symbol-search", "symbol-regex", "desc-search", "desc-regex", "search", "fundamental").

        Returns:
            requests.Response: Instruments.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/instruments',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            params={'symbol': symbol, 'projection': projection},
                            timeout=self.timeout)

    def instrument_cusip(self, cusip_id: str | int) -> requests.Response:
        """
        Get instrument for a single cusip.

        Args:
            cusip_id (str | int): CUSIP ID.

        Returns:
            requests.Response: Instrument details.
        """
        return requests.get(f'{self._base_api_url}/marketdata/v1/instruments/{cusip_id}',
                            headers={'Authorization': f'Bearer {self.tokens.access_token}'},
                            timeout=self.timeout)
