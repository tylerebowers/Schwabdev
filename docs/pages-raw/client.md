# Using the Client

The client is the main class of Schwabdev and where you access all parts of the Schwab API. 

Making a client is as simple as:

```python
import schwabdev

client = schwabdev.Client(app_key, app_secret)
# client = schwabdev.ClientAsync(...) # For an asynchronous client
```

And from here on `client` can be used to make API calls. All calls can be found in the "API Calls" documentation tab and are also are outlined in `/docs/examples/api_demo.py`. Now let’s look at all of the parameters that can be passed to the client constructor:

```python
client = schwabdev.Client(
    app_key,
    app_secret,
    callback_url="https://127.0.0.1",
    tokens_db="~/.schwabdev/tokens.db",
    encryption=None,
    timeout=10,
    call_for_auth=None,
)
```

* `app_key (str)`: App key credential (e.g. `"xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"`).
* `app_secret (str)`: App secret credential (e.g. `"xxxxxxxxxxxxxxxx"`).
* `callback_url (str)`: URL for callback (e.g. `"https://127.0.0.1"`).
* `tokens_db (str)`: Path to tokens database (e.g. `"~/.schwabdev/tokens.db"`).
* `encryption` `(str | None)`: Encryption key to encrypt the tokens database, if `None` then no encryption is used. To create a key use `from cryptography.fernet import Fernet` and run `key = Fernet.generate_key()`, save the key using the string representation `key.decode()`. See example in <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/extra/encrypted_db_setup.py">encrypted_db_setup.py</a>.
* `timeout (int)`: Request timeout in seconds (how long to wait for a response).
* `call_for_auth (function | None)`: Function to call for authentication, the function is called with one argument: the URL to visit for authentication, it is expected to return the full callback URL or code from the callback URL after the user has signed in, see an example in <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/extra/capture_callback.py">capture_callback.py</a>.

---

Schwabdev also has an Asyncronous client (<a target="_blank" href="https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/async_api_calls.py">useful for concurrent api calls</a>) that can be used with `asyncio`:

```python
client = schwabdev.ClientAsync(
    app_key,
    app_secret,
    callback_url="https://127.0.0.1",
    tokens_db="~/.schwabdev/tokens.db",
    encryption=None,
    timeout=10,
    call_for_auth=None,
    parsed = False,
)
```

The parameters are the same as the synchronous client with the addition of:

* `parsed (bool)`: If set to `True` then all API responses will be returned as parsed JSON objects (dictionaries/lists). This can be overridden on a per-call basis by passing `parsed=True` or `parsed=False` to the API call. Several API calls related to Orders are not parsed by default since they cannot be. The aim of autoparsing is to reduce the amount of code needed for the user.

---

### Notes
* Multiple clients can be run at the same time, though they must share the same `tokens_db` file to avoid token conflicts and only one streamer can be run at a time.
* Clients are likely not thread-safe, but there are some inbuilt protections. If you want to use a client in multiple threads it is recommended to use a threading lock around the client calls.
* In order to use all API calls you must have both API sections added to your app: **Accounts and Trading Production** and **Market Data Production**.
* If you are storing your code in a GitHub repo then use <a target="_blank" href="https://pypi.org/project/python-dotenv/">dotenv</a> to store your keys, especially if you are using a git repo.
With a GitHub repo you can include `*.env` in the `.gitignore` file to stop your credentials from getting committed.
* Schwabdev uses the `logging` module to log/print information, warnings and errors. You can change the level of logging by setting
  `logging.basicConfig(level=logging.XXXX)`
  where `XXXX` is the level of logging you want such as `INFO` or `WARNING`.
* There are a maximum of 120 api requests per minute, 4000 order-related api calls per day, and 500 tickers concurrently streamed. If you exceed these limits you will get HTTP error 429 (Too Many Requests).


---

The Schwab API uses two tokens to use the API:

* **Refresh token** – valid for 7 days, used to “refresh” the access token.
* **Access token** – valid for 30 minutes, used in all API calls.

If you want to access the access or refresh tokens you can call `client.tokens.access_token` or `client.tokens.refresh_token`. 

The access token can be easily updated/refreshed assuming that the refresh token is valid. Getting a new refresh token, however, requires user input. It is recommended to force-update the refresh token during weekends so it is valid during the week. To force-update the refresh token (this can be run concurrently on a separate script), make this call:

```python
client.update_tokens(force_refresh_token=True)
```

Otherwise, the client will start the process 30 minutes before the refresh token will expire.


