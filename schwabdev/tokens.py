"""
Schwabdev Tokens Module.
Manages Schwab OAuth tokens including storage, retrieval, and refreshing.
https://github.com/tylerebowers/Schwab-API-Python
"""
import base64
import datetime
import logging
import os
import webbrowser
import sqlite3
import requests


class Tokens:
    def __init__(self,app_key: str, app_secret: str, callback_url: str, logger: logging.Logger, tokens_db: str="~/.schwabdev/tokens.db", call_for_auth=None):
        """
        Initialize a tokens manager

        Args:
            client (Client): Client object
            app_key (str): App key credential
            app_secret (str): App secret credential
            callback_url (str): Url for callback
            tokens_file (str): Path to tokens file
            call_for_auth (function | None): Function to call for custom auth flow
        """
        #parameter validation
        if not app_key:
            raise ValueError("[Schwabdev] app_key cannot be None.")
        if not app_secret:
            raise ValueError("[Schwabdev] app_secret cannot be None.")
        if not callback_url:
            raise ValueError("[Schwabdev] callback_url cannot be None.")
        if not tokens_db:
            raise ValueError("[Schwabdev] tokens_file cannot be None.")
        if len(app_key) not in (32, 48) or len(app_secret) not in (16, 64):
            raise ValueError("[Schwabdev] App key or app secret invalid length.")
        if not callback_url.startswith("https"):
            raise ValueError("[Schwabdev] callback_url must be https.")
        if callback_url.endswith("/"):
            raise Exception("[Schwabdev] callback_url cannot be path (ends with \"/\").")
        if tokens_db.endswith("/"):
            raise Exception("[Schwabdev] Tokens file cannot be path.")
        if call_for_auth is not None and not callable(call_for_auth):
            raise ValueError("[Schwabdev] call_on_notify must be a callable function.")
        
        #set public variables
        self.access_token = None                            # access token from auth
        self.refresh_token = None                           # refresh token from auth
        self.id_token = None                                # id token from auth
        self.call_for_auth = call_for_auth                    # function to call for custom auth

        #set private variables
        self._app_key = app_key                             # app key credential
        self._app_secret = app_secret                       # app secret credential
        self._callback_url = callback_url                   # callback url to use
        self._access_token_issued = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)  # datetime of access token issue
        self._refresh_token_issued = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc) # datetime of refresh token issue
        self._access_token_timeout = 30 * 60                # in seconds (30 min from schwab)
        self._refresh_token_timeout = 7 * 24 * 60 * 60      # in seconds (7 days from schwab)
        self._logger = logger                               # logger

        #init token database
        tokens_db = os.path.expanduser(tokens_db)
        os.makedirs(os.path.dirname(tokens_db), exist_ok=True)
        self._conn = sqlite3.connect(tokens_db, check_same_thread=False)
        self._cur = self._conn.cursor()
        self._cur.execute("""
        CREATE TABLE IF NOT EXISTS schwabdev (
            access_token_issued TEXT NOT NULL,
            refresh_token_issued TEXT NOT NULL,
            access_token TEXT NOT NULL,
            refresh_token TEXT NOT NULL,
            id_token TEXT NOT NULL,
            expires_in INTEGER,
            token_type TEXT,
            scope TEXT
        );
        """)
        self._conn.commit()

        if self._load_tokens_from_db():
            self.update_tokens()
            at_delta = datetime.timedelta(seconds=self._access_token_timeout) - (datetime.datetime.now(datetime.timezone.utc) - self._access_token_issued)
            rt_delta = datetime.timedelta(seconds=self._refresh_token_timeout) - (datetime.datetime.now(datetime.timezone.utc) - self._refresh_token_issued)
            self._logger.info(f"Access token {"has been expired for: " if at_delta  < datetime.timedelta(0) else 'expires in '}{str(at_delta)[:-7]}")
            self._logger.info(f"Refresh token {"has been expired for: " if rt_delta  < datetime.timedelta(0) else 'expires in '}{str(rt_delta)[:-7]}")
        else:
            self._logger.warning("[Schwabdev] No tokens found in sqlite DB, starting authorization flow.")
            self.update_tokens(force_refresh_token=True)

    def _close(self):
        try:
            self._conn.close()
        except Exception:
            pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self._close()

    def __del__(self):
        self._close()

    def _load_tokens_from_db(self) -> bool:
        """
        Load tokens from sqlite database into memory.

        Returns:
            bool: True if tokens were loaded, False if no row exists.
        """
        row = self._cur.execute(
            """
            SELECT
                access_token_issued,
                refresh_token_issued,
                access_token,
                refresh_token,
                id_token,
                expires_in,
                token_type,
                scope
            FROM schwabdev
            LIMIT 1
            """
        ).fetchone()

        if not row:
            return False

        (at_issued_str,
         rt_issued_str,
         access_token,
         refresh_token,
         id_token,
         expires_in,
         token_type,
         scope) = row
        
        self._access_token_issued = datetime.datetime.fromisoformat(at_issued_str).replace(tzinfo=datetime.timezone.utc)
        self._refresh_token_issued = datetime.datetime.fromisoformat(rt_issued_str).replace(tzinfo=datetime.timezone.utc)

        self.access_token = access_token
        self.refresh_token = refresh_token
        self.id_token = id_token
        #self._expires_in = expires_in
        #self._token_type = token_type
        #self._scope = scope

        return True
    
    def _set_tokens(self, at_issued: datetime.datetime, rt_issued: datetime.datetime, token_dictionary: dict):
        """
        Persist tokens to sqlite and set in-memory variables.

        Args:
            at_issued (datetime.datetime): access token issued datetime
            rt_issued (datetime.datetime): refresh token issued datetime
            token_dictionary (dict): token dictionary from Schwab OAuth
        """
        self.access_token = token_dictionary.get("access_token")
        self.refresh_token = token_dictionary.get("refresh_token")
        self.id_token = token_dictionary.get("id_token", "")
        self._access_token_issued = at_issued
        self._refresh_token_issued = rt_issued

        expires_in = token_dictionary.get("expires_in", 1800)
        token_type = token_dictionary.get("token_type", "Bearer")
        scope = token_dictionary.get("scope", "api")

        try:
            # Only ever keep one row; simplest is delete + insert
            self._cur.execute("DELETE FROM schwabdev")
            self._cur.execute(
                """
                INSERT INTO schwabdev (
                    access_token_issued,
                    refresh_token_issued,
                    access_token,
                    refresh_token,
                    id_token,
                    expires_in,
                    token_type,
                    scope
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    at_issued.isoformat(),
                    rt_issued.isoformat(),
                    self.access_token,
                    self.refresh_token,
                    self.id_token,
                    expires_in,
                    token_type,
                    scope,
                ),
            )
            self._conn.commit()
        except Exception as e:
            self._logger.error(e)
            self._logger.error("[Schwabdev] Could not write tokens to sqlite database")


    def _post_oauth_token(self, grant_type: str, code: str):
        """
        Makes API calls for auth code and refresh tokens

        Args:
            grant_type (str): 'authorization_code' or 'refresh_token'
            code (str): authorization code

        Returns:
            requests.Response
        """
        headers = {'Authorization': f'Basic {base64.b64encode(bytes(f"{self._app_key}:{self._app_secret}", "utf-8")).decode("utf-8")}',
                   'Content-Type': 'application/x-www-form-urlencoded'}
        if grant_type == 'authorization_code':  # gets access and refresh tokens using authorization code
            data = {'grant_type': 'authorization_code',
                    'code': code,
                    'redirect_uri': self._callback_url}
        elif grant_type == 'refresh_token':  # refreshes the access token
            data = {'grant_type': 'refresh_token',
                    'refresh_token': code}
        else:
            raise Exception("Invalid grant type; options are 'authorization_code' or 'refresh_token'")
        return requests.post('https://api.schwabapi.com/v1/oauth/token', headers=headers, data=data)


    def update_tokens(self, force_access_token=False, force_refresh_token=False):
        """
        Checks if tokens need to be updated and updates if needed (only access token is automatically updated)

        Args:
            force_access_token (bool): force update of access token. Defaults to False
            force_refresh_token (bool): force update of refresh token (also updates access token). Defaults to False

        Returns:
            bool: True if tokens were updated and False otherwise
        """
        now = datetime.datetime.now(datetime.timezone.utc)
        rt_delta = datetime.timedelta(seconds=self._refresh_token_timeout) - (now - self._refresh_token_issued)
        at_delta = datetime.timedelta(seconds=self._access_token_timeout) - (now - self._access_token_issued)

        refresh_threshold = datetime.timedelta(seconds=1830)  # 30.5 minutes
        access_threshold = datetime.timedelta(seconds=61)     # 61 seconds

        # check if we need to update refresh (and access) token
        if (rt_delta < refresh_threshold) or force_refresh_token:
            self._logger.warning("The refresh token has expired!")
            self._update_refresh_token()
            return True
        # check if we need to update access token
        elif (at_delta < access_threshold) or force_access_token:
            self._logger.debug("The access token has expired, updating...")
            self._update_access_token()
            return True
        else:
            return False

    """
        Access Token functions:
    """

    def _update_access_token(self):
        """
        "refresh" the access token using the refresh token
        """
        try:
            last_known_at_issued = self._access_token_issued
            self._load_tokens_from_db()
            if self._access_token_issued > last_known_at_issued:
                self._logger.info(f"Access token updated elsewhere at {self._access_token_issued}.")
                return 
        except:
            pass

        try:
            self._cur.execute("BEGIN EXCLUSIVE") # Start an explicit transaction that blocks other readers/writers.
        except sqlite3.Error as e:
            self._logger.error(e)
            self._logger.error("[Schwabdev] Could not start EXCLUSIVE transaction for access token update")
            return
        
        committed = False

        try:
            response = self._post_oauth_token('refresh_token', self.refresh_token)
            if not response.ok:
                self._logger.error(response.text)
                self._logger.error("Could not get new access token; refresh_token likely invalid.")
                self._conn.rollback()  # release lock, no write performed
                return
            self._set_tokens(datetime.datetime.now(datetime.timezone.utc), self._refresh_token_issued, response.json())
            committed = True
            self._logger.info(f"Access token updated at {self._access_token_issued}")
        except Exception as e:
            self._logger.error(e)
            self._logger.error("[Schwabdev] Could not update access token")
            if not committed:
                try:
                    self._conn.rollback()
                except sqlite3.Error:
                    pass


    """
        Refresh Token functions:
    """

    def _get_auth_url(self):
        return f'https://api.schwabapi.com/v1/oauth/authorize?client_id={self._app_key}&redirect_uri={self._callback_url}'

    def _update_refresh_token_from_code(self, url_or_code: str) -> None:
        """
        Get new access and refresh tokens using callback URL or authorization code,
        under an EXCLUSIVE sqlite transaction.
        """
        try:
            self._cur.execute("BEGIN EXCLUSIVE")
        except sqlite3.Error as e:
            self._logger.error(e)
            self._logger.error("[Schwabdev] Could not start EXCLUSIVE transaction for refresh token update")
            return

        committed = False
        try:
            last_known_rt_issued = self._refresh_token_issued
            self._load_tokens_from_db()

            # If refresh token was already updated by someone else, bail
            if self._refresh_token_issued > last_known_rt_issued:
                self._logger.info("Refresh token updated elsewhere (Did you auth twice?)")
                self._conn.rollback()
                return

            if url_or_code.startswith("https://"):
                try:
                    code = f"{url_or_code[url_or_code.index('code=') + 5:url_or_code.index('%40')]}@"
                except ValueError:
                    self._logger.error("Could not parse authorization code from URL.")
                    self._conn.rollback()
                    return
            else:
                code = url_or_code

            now = datetime.datetime.now(datetime.timezone.utc)
            response = self._post_oauth_token('authorization_code', code)
            if not response.ok:
                self._logger.error(response.text)
                self._logger.error(
                    "Could not get new refresh and access tokens, check these:\n"
                    "1. App status is \"Ready For Use\".\n"
                    "2. App key and app secret are valid.\n"
                    "3. You pasted the whole url within 30 seconds. (it has a quick expiration)\n"
                    "4. https://tylerebowers.github.io/Schwabdev/?source=pages%2Ftroubleshooting.html"
                )
                self._conn.rollback()
                return

            self._set_tokens(now, now, response.json())
            committed = True
            self._logger.info("Refresh and Access tokens updated")

        except Exception as e:
            self._logger.error(e)
            self._logger.error("[Schwabdev] Could not update refresh token")
            if not committed:
                try:
                    self._conn.rollback()
                except sqlite3.Error:
                    pass

    def _update_refresh_token(self):
        """
        Get new access and refresh tokens using authorization code.
        """

        try: #check for newer tokens in the db
            last_known_rt_issued = self._refresh_token_issued
            self._load_tokens_from_db()
            if self._refresh_token_issued > last_known_rt_issued:
                self._logger.info(f"Refresh token updated elsewhere at {self._refresh_token_issued}.")
                return
        except:
            pass

        auth_url = self._get_auth_url()

        if self.call_for_auth is not None and callable(self.call_for_auth):
            self._update_refresh_token_from_code(self.call_for_auth(auth_url))
        else:
            print(f"[Schwabdev] Open to authenticate: {auth_url}")
            try:
                webbrowser.open(auth_url)
            except Exception as e:
                self._logger.error(e)
                self._logger.warning("Could not open browser for authorization (open the link manually)")

            # parse the callback url
        
            response_url = input("[Schwabdev] After authorizing, paste the address bar url here: ")
            url_or_code = response_url  # helper will handle URL vs raw code

            self._update_refresh_token_from_code(url_or_code)
