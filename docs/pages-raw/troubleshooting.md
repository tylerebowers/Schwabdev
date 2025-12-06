## Common Issues

> **Problem:** unauthorized error
> `{'errors': [{'id': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', 'status': 401, 'title': 'Unauthorized', 'detail': 'Client not authorized'}]}`
> **Cause:** You do not have access to both APIs and are attempting to access one that you have not added to your app.
> **Fix:** Add both APIs **"Accounts and Trading Production"** and **"Market Data Production"** to your app.
> **Cause:** The access token is expired; sometimes Schwab invalidates tokens when they make backend changes.
> **Fix:** Manually update the access token by changing the date in `tokens.json` or update both tokens by calling `client.tokens.update_tokens(force=True)`.

> **Problem:** Trying to sign into account and get error message:
> `"We are unable to complete your request. Please contact customer service for further assistance."`
> **Problem:**
> `"Whitelabel Error Page This application has no configured error view, so you are seeing this as a fallback." (status=500)`
> **Fix:** Your app is **"Approved - Pending"**, you must wait for status **"Ready for Use"**.
> **Note:** Or you *could* have an account type that is not supported by the Schwab API.

> **Problem:** `SSL: CERTIFICATE_VERIFY_FAILED - self-signed certificate in certificate chain` error when connecting to streaming server
> **Fix:** For macOS you must run the Python certificates installer:
> `open /Applications/Python\ 3.12/Install\ Certificates.command`

> **Problem:** Issues with option contracts in API calls or streaming
> **Fix:** You are likely not following the format for option contracts.
> **Option contract format:**
> `Symbol (6 characters including spaces) | Expiration (6 characters) | Call/Put (1 character) | Strike Price (5+3=8 characters)`

> **Problem:**
> `{"error":"unsupported_token_type","error_description":"400 Bad Request: \"{\"error_description\":\"Exception while authenticating refresh token..."`
> **Problem:** `"Could not get new access token (1 of 3)."` (or x of 3 etc.)
> **Cause:** Your refresh token is invalid (maybe you created a new refresh token on a different machine).
> **Fix:** Manually update the refresh token by changing the date in `tokens.json` or by calling `client.tokens.update_tokens(force=True)`.

> **Problem:** `"can't register atexit after shutdown"`
> **Cause:** The main thread dies before the stream thread starts.
> **Fix:** Add a delay after starting or sending a request — something to let the stream thread start up before the main thread closes.

> **Problem:** API calls throwing errors despite access token and refresh token being valid / not expired.
> **Fix:** Manually update refresh / access tokens by calling `client.tokens.update_tokens(force=True)`; you can also delete the `tokens.json` file.

> **Problem:** Streaming `ACCT_ACTIVITY` yields no responses.
> **Fix:** This is a known issue on Schwab's end.

> **Problem:** After signing in, you get an **"Access Denied"** web page.
> **Fix:** Your callback URL is likely incorrect due to a trailing slash `/` at the end.

> **Problem:** App Registration Error
> **Fix:** Email Schwab: `traderapi@schwab.com`

> **Problem:** Issue in streaming with websockets –
> `"Unsupported extension: name = permessage-deflate, params = []"`
> **Cause:** You are using a proxy that is blocking streaming or your DNS is not correctly resolving.
> **Fix:** Change DNS servers (Google’s are known-working) or change/bypass the proxy.

> **Problem:**
> `{'fault': {'faultstring': 'Body buffer overflow', 'detail': {'errorcode': 'protocol.http.TooBigBody'}}}`
> **Cause:** The call that you made exceeds the amount of data that can be returned.
> **Example:** The call `print(client.option_chains("$SPX").json())` returns too much data and will exceed the buffer size.
> **Fix:** Add additional parameters to limit the amount of data returned.

> **Problem:** Refresh token expiring in 7 days is too short.
> **Fix:** *I know.* 😅

---

For issues not shown here, please ask in the [Discord](https://discord.gg/m7SSjr9rs9) server.

