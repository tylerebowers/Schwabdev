Installation is as simple as:

```bash
pip install schwabdev
```

Schwabdev requires **Python 3.11 or higher**. <br>
*You may need to use `pip3` instead of `pip`.*

### Requirements

* `tzdata` – used for timezone data
* `requests` – used for HTTP requests (API calls)
* `websockets` – used for streaming
* `cryptography` – used for making self-signed certificates
* `aiohttp` – used for asynchronous HTTP requests (async client), **not** included by default

### Some notes

* **On macOS** you need to make sure that you installed Python certificates.
  If you haven't or aren't sure, then in a terminal run:

  ```bash
  open /Applications/Python\ 3.11/Install\ Certificates.command
  ```

  (replace `3.11` with the version of Python you are using).

* **On Linux** it is recommended to use a virtual environment.

