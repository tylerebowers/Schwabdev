"""
Schwabdev Stream & StreamAsync Module.
For streaming data from Schwab Streamer API.
https://github.com/tylerebowers/Schwab-API-Python
"""

import asyncio
import datetime
import json
import logging
import threading
import time
import zoneinfo
import websockets
import websockets.exceptions


class StreamBase:

    def __init__(self, tokens, get_streamer_info, logger: logging.Logger):
        """
        Initialize the stream object to stream data from Schwab Streamer

        Args:
            client (Client): Client object needed to get streamer info
        """
        self._tokens = tokens                           # tokens object
        self._get_streamer_info = get_streamer_info     # function to get streamer info
        self._logger = logger                           # logger

        self._websocket = None                          # the websocket
        self._event_loop = None                         # the asyncio loop
        self._thread = None                             # the thread that runs the stream
        self._loop_ready = threading.Event()            # event to signal that the loop is ready
        self._should_stop = True                        # main stream loop
        self._backoff_time = 2.0                        # default backoff time (time to wait before retrying)

        self._streamer_info = None                      # streamer info from api call
        self._request_id = 0                            # a counter for the request id
        
        self.active = False                             # whether the stream is active
        self.subscriptions = {}                         # a dictionary of subscriptions



    async def _run_streamer(self, receiver_func=print, ping_timeout: int = 30, **kwargs):
        """
        Start the streamer

        Args:
            receiver_func (function, optional): function to call when data is received. Defaults to print.
            ping_timeout (int, optional): how long to wait for pongs from the server. Defaults to 30.
            **kwargs: keyword arguments to pass to receiver_func
        """
        self._event_loop = asyncio.get_running_loop()
        is_async_receiver = True if asyncio.iscoroutinefunction(receiver_func) else False
        async def call_receiver(response, **kwargs):
            if is_async_receiver:
                await receiver_func(response, **kwargs)
            else:
                receiver_func(response, **kwargs)
        
        self._should_stop = False
        while not self._should_stop:

            try:
                self._streamer_info = self._get_streamer_info()
            except Exception as e:
                self._logger.error("Error getting streamer info, cannot start stream.")
                self._logger.error(e)
                return

            if self._streamer_info is None:
                self._logger.warning(f"Streamer info unavailable, retrying in {self._backoff_time}s...")
                await self._wait_for_backoff()
                continue

            start_time = datetime.datetime.now(datetime.timezone.utc)
            try:
                self._logger.debug("Connecting to streaming server...")
                async with websockets.connect(self._streamer_info.get('streamerSocketUrl'), ping_timeout=ping_timeout) as self._websocket:
                    self._logger.debug("Connected to streaming server.")
                    login_payload = self.basic_request(service="ADMIN",
                                                       command="LOGIN",
                                                       parameters={"Authorization": self._tokens.access_token,
                                                                   "SchwabClientChannel": self._streamer_info.get("schwabClientChannel"),
                                                                   "SchwabClientFunctionId": self._streamer_info.get("schwabClientFunctionId")})
                    await self._websocket.send(json.dumps(login_payload))
                    self._loop_ready.set()
                
                    await call_receiver(await self._websocket.recv(), **kwargs)  # receive login response
                    self.active = True

                    # send subscriptions (that are recorded (queued or previously sent))
                    for service, subs in self.subscriptions.items():
                        grouped: dict[str, list[str]] = {} # group subscriptions by fields for more efficient requests
                        for key, fields in subs.items():
                            grouped.setdefault(self._list_to_string(fields), []).append(key)
                        reqs = [] # list of requests to send for this service
                        for fields, keys in grouped.items():
                            reqs.append(self.basic_request(service=service, command="ADD", parameters={"keys": self._list_to_string(keys), "fields": fields}))
                        if reqs:
                            self._logger.debug(f"Sending subscriptions: {reqs}")
                            await self._websocket.send(json.dumps({"requests": reqs}))
                            await call_receiver(await self._websocket.recv(), **kwargs)  # receive subscription response

                    # reset backoff time
                    self._backoff_time = 2.0

                    # main listener loop
                    if is_async_receiver:
                        while self.active and not self._should_stop:
                            await receiver_func(await self._websocket.recv(), **kwargs)
                    else:
                        while self.active and not self._should_stop:
                            receiver_func(await self._websocket.recv(), **kwargs)

            except (websockets.exceptions.ConnectionClosedOK, websockets.exceptions.ConnectionClosed) as e: # "received 1000 (OK); then sent 1000 (OK)", "sent 1000 (OK); no close frame received"
                self._logger.info(f"Stream connection closed. ({e})")
                break
            except websockets.exceptions.ConnectionClosedError as e: # lost internet connection
                elapsed = (datetime.datetime.now(datetime.timezone.utc) - start_time).total_seconds()
                if elapsed <= 90:
                    self._logger.warning(f"Stream has crashed within 90 seconds, likely no subscriptions, invalid login, or lost connection. Not restarting. {e}")
                    break
                else:
                    self._logger.error(f"Stream connection Error. Reconnecting in {self._backoff_time} seconds...")
                    await self._wait_for_backoff()
            except Exception as e:  # stream has quit unexpectedly, try to reconnect
                self._logger.error(e)
                self._logger.warning(f"Stream connection lost to server, reconnecting...")
                await self._wait_for_backoff()
            finally:
                self.active = False
                self._websocket = None

    async def _wait_for_backoff(self):
        """
        Wait for the backoff time
        """
        await asyncio.sleep(self._backoff_time)
        self._backoff_time = min(self._backoff_time * 2, 120)


    def _record_request(self, request: dict):
        """
        Record the request into self.subscriptions (for the event of crashes)

        Args:
            request (dict): request
        """

        try:
            def str_to_list(st):
                return st.split(",") if isinstance(st, str) else st
            
            service = request.get("service", None)
            command = request.get("command", None)
            parameters = request.get("parameters", None)
            if parameters is not None and service is not None:
                keys = str_to_list(parameters.get("keys", []))
                fields = str_to_list(parameters.get("fields", []))
                # add service to subscriptions if not already there
                if service not in self.subscriptions:
                    self.subscriptions[service] = {}
                if command == "ADD":
                    for key in keys:
                        if key not in self.subscriptions[service]:
                            self.subscriptions[service][key] = fields
                        else:
                            self.subscriptions[service][key] = list(set(fields) | set(self.subscriptions[service][key]))
                elif command == "SUBS":
                    self.subscriptions[service] = {}
                    for key in keys:
                        self.subscriptions[service][key] = fields
                elif command == "UNSUBS":
                    for key in keys:
                        if key in self.subscriptions[service]:
                            del self.subscriptions[service][key]
                elif command == "VIEW": 
                    for key in self.subscriptions[service].keys():
                        self.subscriptions[service][key] = fields
        except Exception as e:
            self._logger.error(e)
            self._logger.error("Error recording request - subscription not saved.")

    def basic_request(self, service: str, command: str, parameters: dict | None = None):
        """
        Create a basic request (all requests follow this format)

        Args:
            service (str): service to use
            command (str): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"|"LOGIN"|"LOGOUT")
            parameters (dict, optional): parameters to use. Defaults to None.

        Returns:
            dict: request
        """
        if self._streamer_info is None:
            self._streamer_info = self._get_streamer_info()

        if self._streamer_info is None:
            raise ConnectionError("Streamer info unavailable")

        # remove None parameters
        if parameters is not None:
            for key in parameters.keys():
                if parameters[key] is None: del parameters[key]

        self._request_id += 1
        request = {"service": service.upper(),
                   "command": command.upper(),
                   "requestid": self._request_id,
                   "SchwabClientCustomerId": self._streamer_info.get("schwabClientCustomerId"),
                   "SchwabClientCorrelId": self._streamer_info.get("schwabClientCorrelId")}
        if parameters is not None and len(parameters) > 0: request["parameters"] = parameters
        return request

    @staticmethod
    def _list_to_string(ls: list | str | tuple | set):
        """
        Convert a list to a string (e.g. [1, "B", 3] -> "1,B,3"), or passthrough if already a string

        Args:
            ls (list | str | tuple | set): list to convert

        Returns:
            str: converted string
        """
        if isinstance(ls, str): return ls
        elif hasattr(ls, '__iter__'): return ",".join(map(str, ls)) # yes, this is true for string too but those are caught first
        else: return str(ls)

    def level_one_equities(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Level one equities

        Args:
            keys (list | str): list of keys to use (e.g. ["AAPL", "GOOG"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Returns:
            dict: stream request
        """
        return self.basic_request("LEVELONE_EQUITIES", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def level_one_options(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Level one options

        Args:
            keys (list | str): list of keys to use (e.g. ["GOOG  240809C00095000", "AAPL  240517P00190000"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Contract format: [Underlying Symbol (6 characters including spaces) | Expiration (6 characters) | Call/Put (1 character) | Strike Price (5+3=8 characters)]

        Returns:
            dict: stream request
        """
        return self.basic_request("LEVELONE_OPTIONS", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def level_one_futures(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Level one futures

        Args:
            keys (list | str): list of keys to use (e.g. ["/ESF24", "/GCG24"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Key format: key format: '/' + 'root symbol' + 'month code' + 'year code'
              month code is 1 character: (F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec)
              year code is 2 characters (i.e. 2024 = 24)

        Returns:
            dict: stream request
        """
        return self.basic_request("LEVELONE_FUTURES", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def level_one_futures_options(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Level one futures options

        Args:
            keys (list | str): list of keys to use (e.g. ["./OZCZ23C565"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Key format: key format: '.' + '/' + 'root symbol' + 'month code' + 'year code' + 'Call/Put code' + 'Strike Price'
                month code is 1 character: (F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec)
                year code is 2 characters (i.e. 2024 = 24)
                Call/Put code is 1 character: (C: Call, P: Put)

        Returns:
            dict: stream request
        """
        return self.basic_request("LEVELONE_FUTURES_OPTIONS", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def level_one_forex(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Level one forex

        Args:
            keys (list | str): list of keys to use (e.g. ["EUR/USD", "JPY/USD"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Key format: 'from currency' + '/' + 'to currency'

        Returns:
            dict: stream request
        """
        return self.basic_request("LEVELONE_FOREX", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def nyse_book(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        NYSE book orders

        Args:
            keys (list | str): list of keys to use (e.g. ["NIO", "F"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Returns:
            dict: stream request
        """
        return self.basic_request("NYSE_BOOK", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def nasdaq_book(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        NASDAQ book orders

        Args:
            keys (list | str): list of keys to use (e.g. ["AMD", "CRWD"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Returns:
            dict: stream request
        """
        return self.basic_request("NASDAQ_BOOK", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def options_book(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Options book orders

        Args:
            keys (list | str): list of keys to use (e.g. ["GOOG  240809C00095000", "AAPL  240517P00190000"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Contract format: [Underlying Symbol (6 characters including spaces) | Expiration (6 characters) | Call/Put (1 character) | Strike Price (5+3=8 characters)]

        Returns:
            dict: stream request
        """
        return self.basic_request("OPTIONS_BOOK", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def chart_equity(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Chart equity

        Args:
            keys (list | str): list of keys to use (e.g. ["GOOG", "AAPL"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Returns:
            dict: stream request
        """
        return self.basic_request("CHART_EQUITY", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def chart_futures(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Chart futures

        Args:
            keys (list | str): list of keys to use (e.g. ["/ESF24", "/GCG24"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            key format: '/' + 'root symbol' + 'month code' + 'year code'
                month code is 1 character: (F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec)
                year code is 2 characters (i.e. 2024 = 24)

        Returns:
            dict: stream request
        """
        return self.basic_request("CHART_FUTURES", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def screener_equity(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Screener equity

        Args:
            keys (list | str): list of keys to use (e.g. ["$DJI_PERCENT_CHANGE_UP_60", "NASDAQ_VOLUME_30"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Key format: (PREFIX)_(SORTFIELD)_(FREQUENCY);
                Prefix: ($COMPX, $DJI, $SPX.X, INDEX_AL, NYSE, NASDAQ, OTCBB, EQUITY_ALL)
                Sortfield: (VOLUME, TRADES, PERCENT_CHANGE_UP, PERCENT_CHANGE_DOWN, AVERAGE_PERCENT_VOLUME)
                Frequency: (0 (all day), 1, 5, 10, 30 60)

        Returns:
            dict: stream request
        """
        return self.basic_request("SCREENER_EQUITY", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def screener_options(self, keys: str | list, fields: str | list, command: str = "ADD") -> dict:
        """
        Screener option key format:

        Args:
            keys (list | str): list of keys to use (e.g. ["OPTION_PUT_PERCENT_CHANGE_UP_60", "OPTION_CALL_TRADES_30"])
            fields (list | str): list of fields to use
            command (str, optional): command to use ("SUBS"|"ADD"|"UNSUBS"|"VIEW"). Defaults to "ADD".

        Note:
            Kay format: (PREFIX)_(SORTFIELD)_(FREQUENCY);
                Prefix: (OPTION_PUT, OPTION_CALL, OPTION_ALL);
                Sortfield: (VOLUME, TRADES, PERCENT_CHANGE_UP, PERCENT_CHANGE_DOWN, AVERAGE_PERCENT_VOLUME)
                Frequency: (0 (all day), 1, 5, 10, 30 60)

        Returns:
            dict: stream request
        """
        return self.basic_request("SCREENER_OPTION", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})

    def account_activity(self, keys="Account Activity", fields="0,1,2,3", command: str = "SUBS") -> dict:
        """
        Account activity

        Args:
            keys (str | list, optional): list of keys to use (e.g. ["Account Activity"]). Defaults to "Account Activity".
            fields (str | list, optional): list of fields to use (e.g. ["0,1,2,3"]). Defaults to "0,1,2,3".
            command (str, optional): command to use ("SUBS"|"UNSUBS"). Defaults to "SUBS".

        Returns:
            dict: stream request
        """
        return self.basic_request("ACCT_ACTIVITY", command, parameters={"keys": Stream._list_to_string(keys), "fields": Stream._list_to_string(fields)})
    
class Stream(StreamBase):
    def __init__(self, client):
        super().__init__(client.tokens, client._get_streamer_info, client.logger)

    def start(self, receiver=print, daemon: bool = True, ping_interval: int = 20, **kwargs):
        """
        Start the stream

        Args:
            receiver (function, optional): function to call when data is received. Defaults to print.
            daemon (bool, optional): whether to run the thread in the background (as a daemon). Defaults to True.
            ping_interval (int, optional): interval in seconds to send pings to the streamer. Defaults to 20.
        """
        if self.active and (self._thread and self._thread.is_alive()):
            self._logger.warning("Stream already active.")
            return
        else:
            self._loop_ready.clear()

            def _start_asyncio():
                asyncio.run(self._run_streamer(receiver, ping_interval, **kwargs))

            self._thread = threading.Thread(target=_start_asyncio, daemon=daemon)
            self._thread.start()

            self._loop_ready.wait(timeout=4.0)

    def __enter__(self):
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.stop()

    def __del__(self):
        self.stop()

    def start_auto(self, receiver=print, start_time: datetime.time = datetime.time(9, 29, 0),
                   stop_time: datetime.time = datetime.time(16, 0, 0), on_days: list[int] = [0,1,2,3,4],
                   now_timezone: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo("America/New_York"), daemon: bool = True, **kwargs):
        """
        Start the stream automatically at market open and close, will NOT erase subscriptions

        Args:
            receiver (function, optional): function to call when data is received. Defaults to print.
            start_time (datetime.time, optional): time to start the stream. Defaults to 9:30 (for EST).
            stop_time (datetime.time, optional): time to stop the stream. Defaults to 4:00 (for EST).
            on_days (list[int], optional): day(s) to start the stream default: (0,1,2,3,4) = Mon-Fri, (0 = Monday, ..., 6 = Sunday). Defaults to (0,1,2,3,4).
            now_timezone (zoneinfo.ZoneInfo, optional): timezone to use for now. Defaults to ZoneInfo("America/New_York").
            daemon (bool, optional): whether to run the thread in the background (as a daemon). Defaults to True.
        """
        def checker():

            while True:
                now = datetime.datetime.now(now_timezone)
                in_hours = (start_time <= now.time() <= stop_time) and (now.weekday() in on_days)
                if in_hours and not self.active:
                    if len(self.subscriptions) == 0:
                        self._logger.warning("No subscriptions, starting stream anyways.")
                    self.start(receiver=receiver, daemon=daemon, **kwargs)
                elif not in_hours and self.active:
                    self._logger.info("Stopping Stream.")
                    self.stop(clear_subscriptions=False)
                time.sleep(30)

        threading.Thread(target=checker, daemon=daemon).start()

        if not start_time <= datetime.datetime.now(now_timezone).time() <= stop_time:
            self._logger.info("Stream was started outside of active hours and will launch when in hours.")
    
    def send(self, requests: list | dict, record: bool=True):
        """
        Send a request to the stream

        Args:
            requests (list | dict): list of requests or a single request
        """
        if not isinstance(requests, list):
            requests = [requests]

        if record:
            for request in requests:
                self._record_request(request)

        if self._event_loop is None:
            self._logger.info("Stream event loop not initialized yet; request queued.")
        elif not self.active:
            self._logger.info("Stream is not active, request queued.")
        else:
            asyncio.run_coroutine_threadsafe(self._websocket.send(json.dumps({"requests": requests})), self._event_loop)

    async def send_async(self, requests: list | dict):
        """
        Send a request to the stream

        Args:
            request (list | dict): list of requests or a single request
        """
        if not isinstance(requests, list):
            requests = [requests]

        for req in requests:
            self._record_request(req)

        payload = json.dumps({"requests": requests})

        if self._event_loop is None:
            self._logger.info("Stream event loop not initialized yet; request queued.")
        elif not self.active:
            self._logger.info("Stream is not active, request queued.")
        else:
            await asyncio.wrap_future(asyncio.run_coroutine_threadsafe(self._websocket.send(payload), self._event_loop))

    def stop(self, clear_subscriptions: bool = True):
        """
        Stop the stream

        Args:
            clear_subscriptions (bool, optional): clear records. Defaults to True.
        """
        if clear_subscriptions:
            self.subscriptions = {}

        self._should_stop = True
        
        if self.active and self._websocket:
            try:
                self.send(self.basic_request(service="ADMIN", command="LOGOUT"), record=False)
            except Exception as e:
                self._logger.error(e)
            finally:
                self.active = False

        if self._event_loop and self._websocket:
            try:
                asyncio.run_coroutine_threadsafe(self._websocket.close(), self._event_loop).result(timeout=5)
            except Exception as e:
                self._logger.error(f"Error closing websocket: {e}")
            finally:
                self._event_loop = None
                self._websocket = None
        
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

class StreamAsync(StreamBase):
    def __init__(self, client):
        super().__init__(client.tokens, client._get_streamer_info, client.logger)
        self._task = None

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.stop()

    async def start(self, receiver=print, ping_interval: int = 20, **kwargs):
        """
        Start the stream in the *current* event loop (no thread).
        """
        if self.active or (self._task and not self._task.done()):
            self._logger.warning("Stream already active.")
            return
        else:
            self._event_loop = asyncio.get_running_loop() #override with where we are called from
            self._task = self._event_loop.create_task(
                self._run_streamer(
                    receiver_func=receiver,
                    ping_timeout=ping_interval,
                    **kwargs,
                )
            )

    async def start_auto(self, receiver=print, start_time: datetime.time = datetime.time(9, 29, 0),
                   stop_time: datetime.time = datetime.time(16, 0, 0), on_days: list[int] | tuple[int] = (0,1,2,3,4),
                   now_timezone: zoneinfo.ZoneInfo = zoneinfo.ZoneInfo("America/New_York"), daemon: bool = True, **kwargs):
        """
        Start the stream automatically at market open and close, will NOT erase subscriptions

        Args:
            receiver (function, optional): function to call when data is received. Defaults to print.
            start_time (datetime.time, optional): time to start the stream. Defaults to 9:30 (for EST).
            stop_time (datetime.time, optional): time to stop the stream. Defaults to 4:00 (for EST).
            on_days (list[int], optional): day(s) to start the stream default: (0,1,2,3,4) = Mon-Fri, (0 = Monday, ..., 6 = Sunday). Defaults to (0,1,2,3,4).
            now_timezone (zoneinfo.ZoneInfo, optional): timezone to use for now. Defaults to ZoneInfo("America/New_York").
            daemon (bool, optional): whether to run the thread in the background (as a daemon). Defaults to True.
        """
        async def checker():

            while True:
                now = datetime.datetime.now(now_timezone)
                in_hours = (start_time <= now.time() <= stop_time) and (now.weekday() in on_days)
                if in_hours and not self.active:
                    if len(self.subscriptions) == 0:
                        self._logger.warning("No subscriptions, starting stream anyways.")
                    await self.start(receiver=receiver, daemon=daemon, **kwargs)
                elif not in_hours and self.active:
                    self._logger.info("Stopping Stream.")
                    await self.stop(clear_subscriptions=False)
                await asyncio.sleep(30)

        asyncio.create_task(checker())

    async def send(self, requests: list | dict, record: bool=True):
        """
        Send a request to the stream

        Args:
            request (list | dict): list of requests or a single request
        """
        if not isinstance(requests, list):
            requests = [requests]

        if record:
            for req in requests:
                self._record_request(req)

        if self._event_loop is None:
            self._logger.info("Stream event loop not initialized yet; request queued.")
        elif not self.active:
            self._logger.info("Stream is not active, request queued.")
        else:
            await self._websocket.send(json.dumps({"requests": requests}))
            

    async def stop(self, clear_subscriptions: bool = True):
        """
        Stop the stream started with start_async.
        """
        if clear_subscriptions:
            self.subscriptions = {}

        self._should_stop = True

        if self.active and self._websocket is not None:
            try:
                await self.send(self.basic_request("ADMIN", "LOGOUT"), record=False)
            except Exception as e:
                self._logger.error(f"Error sending LOGOUT: {e}")
            finally:
                self.active = False
        
        if self._websocket is not None:
            try:
                await self._websocket.close()
            except Exception as e:
                self._logger.error(f"Error closing websocket: {e}")
            finally:
                self._event_loop = None
                self._websocket = None

        if self._task is not None:
            try:
                await self._task
            except Exception as e:
                self._logger.error(f"Stream task error on shutdown: {e}")
            finally:
                self._task = None

