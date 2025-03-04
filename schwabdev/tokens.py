"""
This file contains a class to manage tokens
Coded by Tyler Bowers
Github: https://github.com/tylerebowers/Schwab-API-Python
"""
import base64
import datetime
import http.server
import json
import logging
import os
import ssl
import webbrowser
from typing import Callable

import requests


class Tokens:
    def __init__(self, client, app_key: str, app_secret: str, callback_url: str, tokens_file: str="tokens.json", capture_callback=False, call_on_notify=None):
        """
        Initialize a tokens manager

        Args:
            client (Client): Client object
            app_key (str): App key credential
            app_secret (str): App secret credential
            callback_url (str): Url for callback
            tokens_file (str): Path to tokens file
            capture_callback (bool): Use a webserver with self-signed cert to callback
            call_on_notify (function | None): Function to call when user needs to be notified (e.g. for input)
        """
        self._validate_input(app_key, app_secret, callback_url, tokens_file, call_on_notify)

        self._client = client                               # client object
        self._app_key = app_key                             # app key credential
        self._app_secret = app_secret                       # app secret credential
        self._callback_url = callback_url                   # callback url to use

        self.access_token = None                            # access token from auth
        self.refresh_token = None                           # refresh token from auth
        self.id_token = None                                # id token from auth
        self._access_token_issued = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc)  # datetime of access token issue
        self._refresh_token_issued = datetime.datetime.min.replace(tzinfo=datetime.timezone.utc) # datetime of refresh token issue
        self._access_token_timeout = 1800                   # in seconds (from schwab)
        self._refresh_token_timeout = 7 * 24 * 60 * 60      # in seconds (from schwab)
        self._tokens_file = tokens_file                     # path to tokens file

        self._capture_callback = capture_callback               # use a webserver with self-signed cert to callback
        self.call_on_notify = call_on_notify                    # function to call when user needs to be notified (e.g. for input)

        try:
            with open(self._tokens_file, 'r') as f: # Load tokens if the file exists.
                d = json.load(f)
                token_dictionary = d.get("token_dictionary")
                self.access_token = token_dictionary.get("access_token")
                self.refresh_token = token_dictionary.get("refresh_token")
                self.id_token = token_dictionary.get("id_token")
                self._access_token_issued = datetime.datetime.fromisoformat(d.get("access_token_issued")).replace(tzinfo=datetime.timezone.utc)
                self._refresh_token_issued = datetime.datetime.fromisoformat(d.get("refresh_token_issued")).replace(tzinfo=datetime.timezone.utc)

                self.update_tokens()  # check if tokens need to be updated and update if needed
                at_delta = self._access_token_timeout - (datetime.datetime.now(datetime.timezone.utc) - self._access_token_issued).total_seconds()
                rt_delta = self._refresh_token_timeout - (datetime.datetime.now(datetime.timezone.utc) - self._refresh_token_issued).total_seconds()
                self._client.logger.info(f"Access token expires in {'-' if at_delta < 0 else ''}{int(abs(at_delta) / 3600):02}H:{int((abs(at_delta) % 3600) / 60):02}M:{int((abs(at_delta) % 60)):02}S")
                self._client.logger.info(f"Refresh token expires in {'-' if rt_delta < 0 else ''}{int(abs(rt_delta) / 3600):02}H:{int((abs(rt_delta) % 3600) / 60):02}M:{int((abs(rt_delta) % 60)):02}S")

        except Exception as e:
            self._client.logger.error(e)
            self._client.logger.warning(f"Token file does not exist or invalid formatting, creating \"{str(tokens_file)}\"")
            # Tokens must be updated.
            self.update_refresh_token()

    @staticmethod
    def _validate_input(app_key: str, app_secret: str, callback_url: str, tokens_file: str, call_on_notify: Callable) -> None:
        """
        Validates initialization parameters.

        Args:
            app_key (str): App key credentials.
            app_secret (str): App secret credentials.
            callback_url (str): URL for callback.
            tokens_file (str): Path to the tokens file.

        Raises:
            ValueError: If any validation checks fail.
        """
        if not app_key:
            raise ValueError("[Schwabdev] app_key cannot be None.")
        if not app_secret:
            raise ValueError("[Schwabdev] app_secret cannot be None.")
        if not callback_url:
            raise ValueError("[Schwabdev] callback_url cannot be None.")
        if not tokens_file:
            raise ValueError("[Schwabdev] tokens_file cannot be None.")

        if len(app_key) != 32 or len(app_secret) != 16:
            raise ValueError("[Schwabdev] App key or app secret invalid length.")
        if not callback_url.startswith("https"):
            raise ValueError("[Schwabdev] callback_url must be https.")
        if callback_url.endswith("/"):
            raise Exception("[Schwabdev] callback_url cannot be path (ends with \"/\").")
        if tokens_file.endswith("/"):
            raise Exception("[Schwabdev] Tokens file cannot be path.")
        if call_on_notify is not None and not callable(call_on_notify):
            raise ValueError("[Schwabdev] call_on_notify must be a callable function.")

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

    def _set_tokens(self, at_issued: datetime.datetime, rt_issued: datetime.datetime, token_dictionary: dict):
        """
        Writes token file and sets variables

        Args:
            at_issued (datetime.pyi): access token issued
            rt_issued (datetime.pyi): refresh token issued
            token_dictionary (dict): token dictionary

        Notes:
            Writes to tokens and expiration times to self._tokens_file
        """
        self.access_token = token_dictionary.get("access_token")
        self.refresh_token = token_dictionary.get("refresh_token")
        self.id_token = token_dictionary.get("id_token")
        self._access_token_issued = at_issued
        self._refresh_token_issued = rt_issued
        try:
            with open(self._tokens_file, 'w') as f:
                to_write = {"access_token_issued": at_issued.isoformat(),
                            "refresh_token_issued": rt_issued.isoformat(),
                            "token_dictionary": token_dictionary}
                json.dump(to_write, f, ensure_ascii=False, indent=4)
        except Exception as e:
            self._client.logger.error(e)
            self._client.logger.error("Could not write tokens file")


    def update_tokens(self, force_access_token=False, force_refresh_token=False):
        """
        Checks if tokens need to be updated and updates if needed (only access token is automatically updated)

        Args:
            force_access_token (bool): force update of access token. Defaults to False
            force_refresh_token (bool): force update of refresh token (also updates refresh token). Defaults to False

        Returns:
            bool: True if tokens were updated and False otherwise
        """
        def call_notifier(message, importance=0):
            if callable(self.call_on_notify):
                try:
                    self.call_on_notify(message=message, importance=importance)
                except Exception as e:
                    self._client.logger.error(e)

        # refresh token notification
        rt_delta = self._refresh_token_timeout - (datetime.datetime.now(datetime.timezone.utc) - self._refresh_token_issued).total_seconds()
        at_delta = self._access_token_timeout - (datetime.datetime.now(datetime.timezone.utc) - self._access_token_issued).total_seconds()
        if 30 <= rt_delta <= 43300 and rt_delta % 900 <= 30:  # call every hour
            print(f"The refresh token will expire soon! ({'-' if rt_delta < 0 else ''}{int(abs(rt_delta) / 3600):02}H:{int((abs(rt_delta) % 3600) / 60):02}M:{int((abs(rt_delta) % 60)):02}S remaining)")
            if rt_delta < 21700 and rt_delta % 3600 <= 30: call_notifier(message=f"Refresh token expires in less than {int(abs(rt_delta) / 3600):01} hours", importance=int(abs(rt_delta) / 3600))


        # check if we need to update refresh (and access) token
        if (rt_delta < 1800) or force_refresh_token:
            self._client.logger.warning("The refresh token has expired!")
            call_notifier(message="Input required for refresh token", importance=0)
            self.update_refresh_token()
            return True
        # check if we need to update access token
        elif (at_delta < 61) or force_access_token:
            self._client.logger.info("The access token has expired, updating automatically.")
            self.update_access_token()
            return True
        else:
            return False

    """
        Access Token functions:
    """

    def update_access_token(self):
        """
        "refresh" the access token using the refresh token
        """
        response = self._post_oauth_token('refresh_token', self.refresh_token)
        if response.ok:
            # get and update to the new access token
            at_issued = datetime.datetime.now(datetime.timezone.utc)
            self._set_tokens(at_issued, self._refresh_token_issued, response.json())
            # show user that we have updated the access token
            self._client.logger.info(f"Access token updated: {self._access_token_issued}")
        else:
            self._client.logger.error(response.text)
            self._client.logger.error(f"Could not get new access token; refresh_token likely invalid.")

    """
        Refresh Token functions:
    """

    def _generate_certificate(self, common_name="common_name", key_filepath="localhost.key", cert_filepath="localhost.crt"):
        """
        Generate a self-signed certificate for use in capturing the callback during authentication

        Args:
            common_name (str, optional): Common name for the certificate. Defaults to "common_name".
            key_filepath (str, optional): Filepath for the key file. Defaults to "localhost.key".
            cert_filepath (str, optional): Filepath for the certificate file. Defaults to "localhost.crt".

        Notes:
            Schwabdev will change the filepaths to ~/.schwabdev/* (user's home directory)

        """
        from cryptography import x509
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        from cryptography.x509.oid import NameOID

        # make folders for cert files
        os.makedirs(os.path.dirname(key_filepath), exist_ok=True)
        os.makedirs(os.path.dirname(cert_filepath), exist_ok=True)

        # create a key pair
        key = rsa.generate_private_key(public_exponent=65537,key_size=2048)

        # create a self-signed cert
        builder = x509.CertificateBuilder()
        builder = builder.subject_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Schwabdev"),
            x509.NameAttribute(NameOID.ORGANIZATIONAL_UNIT_NAME, "Authentication"),
        ]))
        builder = builder.issuer_name(x509.Name([
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ]))
        builder = builder.not_valid_before(datetime.datetime.now(datetime.timezone.utc))
        builder = builder.not_valid_after(datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=3650))
        builder = builder.serial_number(x509.random_serial_number())
        builder = builder.public_key(key.public_key())
        builder = builder.add_extension(
            x509.SubjectAlternativeName([x509.DNSName(common_name)]),
            critical=False,
        )
        builder = builder.sign(key, hashes.SHA256())
        with open(key_filepath, "wb") as f:
            f.write(key.private_bytes(encoding=serialization.Encoding.PEM,
                                      format=serialization.PrivateFormat.TraditionalOpenSSL,
                                      encryption_algorithm=serialization.NoEncryption()))
        with open(cert_filepath, "wb") as f:
            f.write(builder.public_bytes(serialization.Encoding.PEM))
        self._client.logger.info(f"Certificate generated and saved to {key_filepath} and {cert_filepath}")



    def _update_refresh_token_from_code(self, url_or_code):
        """
        Get new access and refresh tokens using callback url or authorization code.

        Args:
            url_or_code (str): callback url (full url) or authorization code (the code=... in url)
        """
        if url_or_code.startswith("https://"):
            code = f"{url_or_code[url_or_code.index('code=') + 5:url_or_code.index('%40')]}@"
            # session = responseURL[responseURL.index("session=")+8:]
        else:
            code = url_or_code
        # get new access and refresh tokens
        now = datetime.datetime.now(datetime.timezone.utc)
        response = self._post_oauth_token('authorization_code', code)
        if response.ok:
            # update token file and variables
            self._set_tokens(now, now, response.json())
            self._client.logger.info("Refresh and Access tokens updated")
        else:
            self._client.logger.error(response.text)
            self._client.logger.error("Could not get new refresh and access tokens, check these:\n"
                               "1. App status is \"Ready For Use\".\n"
                               "2. App key and app secret are valid.\n"
                               "3. You pasted the whole url within 30 seconds. (it has a quick expiration)")

    def _launch_capture_server(self, url_base, url_port):

        # class used to share code outside the http server
        class SharedCode:
            def __init__(self):
                self.code = ""

        # custom HTTP handler to silence logger and get code
        class HTTPHandler(http.server.BaseHTTPRequestHandler):
            shared = None

            def log_message(self, format, *args):
                pass  # silence logger

            def do_GET(self):
                if self.path.find("code=") != -1:
                    self.shared.code = f"{self.path[self.path.index('code=') + 5:self.path.index('%40')]}@"
                self.send_response(200, "OK")
                self.end_headers()
                self.wfile.write(b"You may now close this page.")

        shared = SharedCode()

        HTTPHandler.shared = shared
        httpd = http.server.HTTPServer((url_base, url_port), HTTPHandler)
        # httpd.socket.settimeout(1)

        cert_filepath = os.path.expanduser("~/.schwabdev/localhost.crt")
        key_filepath = os.path.expanduser("~/.schwabdev/localhost.key")
        if not (os.path.isfile(cert_filepath) and os.path.isfile(key_filepath)):  # this does not check validity
            self._generate_certificate(common_name=url_base, cert_filepath=cert_filepath, key_filepath=key_filepath)

        ctx = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ctx.load_cert_chain(certfile=cert_filepath, keyfile=key_filepath)
        # ctx.load_default_certs()

        print(f"[Schwabdev] Listening on port {url_port} for callback...")
        httpd.socket = ctx.wrap_socket(httpd.socket, server_side=True)
        while len(shared.code) < 1:  # wait for code
            httpd.handle_request()

        httpd.server_close()
        return shared.code

    def update_refresh_token(self):
        """
        Get new access and refresh tokens using authorization code.
        """

        # get and open the link that the user will authorize with.
        auth_url = f'https://api.schwabapi.com/v1/oauth/authorize?client_id={self._app_key}&redirect_uri={self._callback_url}'
        print(f"[Schwabdev] Open to authenticate: {auth_url}")

        # try to open the link
        try:
            webbrowser.open(auth_url)
        except Exception as e:
            self._client.logger.error(e)
            self._client.logger.warning("Could not open browser for authorization (open the link manually)")

        # parse the callback url
        url_split = self._callback_url.split("://")[-1].split(":")
        url_base = url_split[0]
        url_port = url_split[-1] # this may or may not have the port

        if self._capture_callback and not url_port.isdigit(): # if there is a port then capture the callback url
            self._client.logger.error("Could not find port in callback url, so you will have to copy/paste the url.")
            self._capture_callback = False

        if self._capture_callback:
            self._update_refresh_token_from_code(self._launch_capture_server(url_base, int(url_port)))
        else:
            response_url = input("[Schwabdev] After authorizing, paste the address bar url here: ")
            code = f"{response_url[response_url.index('code=') + 5:response_url.index('%40')]}@"
            if code is not None:
                self._update_refresh_token_from_code(code)
            else:
                self._client.logger.error("Could not get new refresh token without code.")
