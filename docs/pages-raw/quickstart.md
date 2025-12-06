# Quick setup

1. **Set up your Schwab developer account and app:**

   1. Create a Schwab developer account [here](https://beta-developer.schwab.com/). Use the same email as in your Schwab brokerage account.
   2. Make a new Schwab individual developer app with callback URL `https://127.0.0.1`.
   3. Add **both** API products to the app: **"Accounts and Trading Production"** and **"Market Data Production"**.
   4. Wait until the app status is **"Ready for use"** (this can take a couple days). Note that **"Approved - Pending" will not work**.
   5. Enable TOS (Thinkorswim) for your Schwab account; it is needed for orders and other API calls.

2. **Install packages:**

   1. In a terminal run: `pip install schwabdev`
   2. More installation details can be found [here](installation.html).

3. **Examples on how to use the client** are in the GitHub `examples/` folder (add your keys in the `.env` file).

   1. The first time you run, you will have to sign in to your Schwab account using the generated link in the terminal.
   2. After signing in, agree to the terms, and select account(s). Then you will have to copy the link in the address bar and paste it into the terminal.
   3. Questions? Join the [Discord group](https://discord.gg/m7SSjr9rs9) or consult the documentation.

---

### Simple starter code

```python
import schwabdev  # import the package

client = schwabdev.Client("Your app key", "Your app secret")  # create a client

print(client.account_linked().json())  # make api calls
```

---

### Notes

* If you are storing your code in a GitHub repo then use [dotenv](https://pypi.org/project/python-dotenv/) to store your keys.
* **On macOS** you need to make sure that you installed Python certificates.
  If you haven't or aren't sure, then in a terminal run:
  `open /Applications/Python\ 3.11/Install\ Certificates.command`
  (replace `3.11` with the version of Python you are using).
* **On Linux** it is recommended to use a virtual environment.


