## Common Issues

* `{'errors': [{'id': 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX', 'status': 401, 'title': 'Unauthorized', 'detail': 'Client not authorized'}]}`
    * **Cause:** You do not have access to both APIs and are attempting to access one that you have not added to your app.
    * **Fix:** Add both APIs **"Accounts and Trading Production"** and **"Market Data Production"** to your app.
    * **Cause:** The access token is expired; sometimes Schwab invalidates tokens when they make backend changes.
    * **Fix:** Manually update the access token by calling `client.tokens.update_tokens(force_access_token=True)`.

* `"We are unable to complete your request. Please contact customer service for further assistance."` or `"Whitelabel Error Page This application has no configured error view, so you are seeing this as a fallback." (status=500)`
    * **Fix:** Your app is **"Approved - Pending"**, you must wait for status **"Ready for Use"**.
    * **Note:** Or you *could* have an account type that is not supported by the Schwab API.

* `SSL: CERTIFICATE_VERIFY_FAILED - self-signed certificate in certificate chain` 
    * **Fix:** For macOS you must run the Python certificates installer:
    * `open /Applications/Python\ 3.12/Install\ Certificates.command`


* Issues with certain symbols (streaming/api), e.g:`{'errors': [{'id': 'f00192c6-155b-4cd6-b1ac-f11d7cb91962', 'status': '404', 'title': 'Not Found'}]}` 
    * **Cause:** The symbol you are using is in an invalid format or not found
    * **Fix:** Indexes require a `$` prefix (e.g. `$SPX`, `$DJI`).
    * **Fix:** Option contract:
        * `Symbol (6 characters including spaces) | Expiration (6 characters) | Call/Put (1 character) | Strike Price (5+3=8 characters)`
        * Expiration is in `YYMMDD` format.
        * e.g. `"AAPL  240517P00190000"`, `"AAPL  251219C00200000"`
    * **Fix:** Futures:
        * `'/' + 'root symbol' + 'month code' + 'year code'`
        * Month code is 1 character: `F: Jan, G: Feb, H: Mar, J: Apr, K: May, M: Jun, N: Jul, Q: Aug, U: Sep, V: Oct, X: Nov, Z: Dec`
        * Year code is 2 characters (i.e. 2024 → `24`).
    * **Fix:** Futures Options:
        * `'.' + '/' + 'root symbol' + 'month code' + 'year code' + 'Call/Put (1 char)' + 'Strike Price'`
        * Month code is 1 character (same mapping as futures).
        * Year code is 2 characters (i.e. 2024 → `24`).
    * **Fix** Make sure the symbol can be found on Schwab's platform (i.e. TOS)

* `{"error":"unsupported_token_type","error_description":"400 Bad Request: \"{\"error_description\":\"Exception while authenticating refresh token..."`
    * **Cause:** Your refresh token is invalid (maybe you created a new refresh token on a different machine).
    * **Fix:** Manually update the refresh token by changing the date in `tokens.json` or by calling `client.tokens.update_tokens(force=True)`.

*  `"can't register atexit after shutdown"`
    *  **Cause:** The main thread dies before the stream thread starts.
    *  **Fix:** Add a delay after starting or sending a request — something to let the stream thread start up before the main thread closes.

*  API calls throwing errors despite access token and refresh token being valid / not expired.
    *  **Fix:** Manually update refresh / access tokens by calling `client.tokens.update_tokens(force=True)`.

*  Streaming `ACCT_ACTIVITY` yields no responses.
    *  **Fix:** This is a known issue on Schwab's end.

*  After signing in, you get an **"Access Denied"** web page.
    *  **Fix:** Your callback URL is likely incorrect due to a trailing slash `/` at the end.

*  App Registration Error
    *  **Fix:** Email Schwab: `traderapi@schwab.com`

*  Issue in streaming with websockets –
    *  `"Unsupported extension: name = permessage-deflate, params = []"`
    *  **Cause:** You are using a proxy that is blocking streaming or your DNS is not correctly resolving.
    *  **Fix:** Change DNS servers (Google’s are known-working) or change/bypass the proxy.

* 
    *  `{'fault': {'faultstring': 'Body buffer overflow', 'detail': {'errorcode': 'protocol.http.TooBigBody'}}}`
    *  **Cause:** The call that you made exceeds the amount of data that can be returned.
    *  **Example:** The call `print(client.option_chains("$SPX").json())` returns too much data and will exceed the buffer size.
    *  **Fix:** Add additional parameters to limit the amount of data returned.

*  can't register atexit after shutdown
    *  **Cause:** The main thread dies before the stream thread starts.
    *  **Fix:** Add a delay after starting or sending a request — something to let the stream thread start up before the main thread closes.

*  Refresh token expiring in 7 days is too short.
    *  **Fix:** *I know.* 😅

---

For issues not shown here, please ask in the [Discord](https://discord.gg/m7SSjr9rs9) server.

