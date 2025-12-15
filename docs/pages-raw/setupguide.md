# Setup Guide

Watch the <a target="_blank" href="https://youtu.be/69cniU1CTf8">Youtube</a> tutorial.

1. **Set up your Schwab developer account and app:**
    1. <a target="_blank" href="https://developer.schwab.com/login">Create a Schwab developer account"</a>. Use the **same email** as in your Schwab brokerage account.
    2. Request access to the <a target="_blank" href="https://developer.schwab.com/products/trader-api--individual">Trader API - Individual</a>  API product.. 
    2. Make a new Schwab individual developer app in the <a target="_blank" href="https://developer.schwab.com/dashboard/apps">dashboard</a> with callback URL `https://127.0.0.1`
        * Multiple callbacks can be used by separating them with commas, e.g. you might also want a callback with a port on the end: `https://127.0.0.1:7777`
        * Callback URLs must be https and localhost addresses.
        * Add **both** API products to the app: **"Accounts and Trading Production"** and **"Market Data Production"**. Both are needed for full functionality.
            * If you didn't during app creation: Apps Dashboard > View Details > Modify App > APIs.
    4. Wait until the app status is **"Ready for use"** (this can take a couple days). Note that **"Approved - Pending" will not work**.
    5. Enable TOS (<a target="_blank" href="https://www.schwab.com/trading/thinkorswim">Thinkorswim</a>) for your Schwab account; it is needed for orders and other API calls. You can do this by logging into your Schwab account on a TOS platform.
2. **Install packages:**
    1. In a terminal run: `pip install schwabdev`
        * *You may need to use `pip3` instead of `pip`.*
        * Schwabdev requires **Python 3.11 or higher**.
        * MacOS requires installation of Python certificates (see notes below).
3. **Start Coding** 
    1. The first time you run, you will have to sign in to your Schwab account using the generated link in the terminal.
    2. After signing in, agree to the terms, and select account(s). Then you will have to copy the link in the address bar and paste it into the terminal.
    3. Examples are in the <a target="_blank" href="https://github.com/tylerebowers/Schwabdev/blob/main/docs/examples/">`docs/examples/`</a> folder remember to [add your keys to a .env](examples.html) file.
    4. Questions? Join the <a target="_blank" href="https://discord.gg/m7SSjr9rs9">Discord Group</a> or consult the documentation.

---

### Simple starter code

```python
import schwabdev  # import the package

client = schwabdev.Client("Your app key", "Your app secret")  # create a client

print(client.quotes("AMD").json())  # make api calls
```

---

### Notes

* If you are storing your code in a GitHub repo then use <a target="_blank" href="https://pypi.org/project/python-dotenv/">dotenv</a> to store your keys.
* **On MacOS** you need to make sure that you installed Python certificates.
  If you haven't or aren't sure, then in a terminal run:
  `open /Applications/Python\ 3.11/Install\ Certificates.command`
  (replace `3.11` with the version of Python you are using).
* **On Linux** it is recommended to use a virtual environment.

### Dependencies

* `tzdata` – used for timezone data
* `requests` – used for HTTP requests (API calls)
* `websockets` – used for streaming
* `cryptography` – used for encryption of the token database (optional)
* `aiohttp` – used for asynchronous HTTP requests (async client), **not** included by default
