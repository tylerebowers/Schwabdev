## Version 3.0.0
* Added Asyncronous Client (`schwabdev.ClientAsync`) for async/await usage
* Added Asyncronous Streamer (`schwabdev.StreamAsync`) for async/await usage
* Tokens backend rework to use an sqlite database instead of a json file for concurrency handling (supports many clients at the same time).
* Standard client no longer uses a background thread to check tokens, and instead checks/refreshes tokens on each request.
* Now including streamer fields with translator function.
* Removed parameters `call_on_notify` and `capture_callback`; replaced with `call_on_auth` (called with auth url, expected to return the final redirect url).


## Version 2.5.1
* Compatibility fix for new key and secret lengths.

## Version 2.5.0
* Added parameter `call_on_notify` which calls a function before the refresh token is about to expire
* Added parameter `capture_callback` (set to `True` to host a webserver to capture the callback — callback URL needs a port)
* Moved all code to Google Docstrings
* New documentation
* Improved refresh logic
* Now only one logger across modules
* Added parameter `use_session` (default `True`) to use a session to send requests and refresh the session for each new access token
* Increased request timeout to 10s and increased streamer pong timeout to 30s

## Version 2.4.4
* Better `stream.start_auto`
* More efficient sending of queued stream requests

## Version 2.4.2
* Fixed 2.4.1 (yanked) issue in `client.quote(...)`

## Version 2.4.0
* Improved stream stability
* Added automatic capture of auth URL (off by default)
* Changed from prints to `logging` module
* Better automatic stream starter

## Version 2.3.0
* Token management rework
* Datetime conversion bugfix

## Version 2.2.6
* Python 3.11 compatibility hotfix

## Version 2.2.5
* Changed streaming daemon mode
* Improved type hinting
* Fixed issue in `stream.start_auto`
* Better “time remaining” prints

## Version 2.2.3
* Added async stream sending function `send_async`
* Changed streamer datetime implementation
* Better print messages

## Version 2.2.2
* Improved datetime usage
* Improved stream crash handling
* Better var type enforcement
* Changed `tokens.json` file format

## Version 2.2.1
* Better error messages
* Bugfixes
* Renamed `screener_option` to `screener_options` in streamer

## Version 2.2.0
* Streaming recovery will resend subscriptions if the stream crashes (toggleable)
* Better initialization error messages
* Removed color printing for compatibility
* Context menu docs for streamer

## Version 2.1.1
* Args/kwargs can now be passed to the `response_handler` during stream start

## Version 2.1.0
* Inline documentation for all user-facing functions

## Version 2.0.2
* Added adjustable timeout parameter for requests
* Increased default timeout

## Version 2.0.1
* Added streamer

## Version 1.9.0
* Changed to color prints
* Preparation for streamer

## Version 1.0.0
* Initial release
* Support for all API calls
* Automatic token refresh

