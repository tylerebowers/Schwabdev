# Schwabdev MCP Server — Design Specification

**Date:** 2026-05-30
**Status:** Draft
**Author:** Automated design session

---

## 1. Purpose

Build a local MCP (Model Context Protocol) server that wraps the `schwabdev` Python library, allowing AI assistants (Claude Desktop, Gemini CLI, etc.) to interact with the Charles Schwab API through MCP tools.

**Goals:**
- Personal use today, structured well enough to eventually ship as part of the `schwabdev` package.
- Full REST API coverage: read-only market data, read-only account data, and write operations (orders).
- No real-time streaming in V1.

**Non-goals:**
- Multi-user / multi-account support.
- Server-side order confirmation flow (relies on LLM client's tool-approval UX).
- WebSocket streaming tools.
- Automated test suite with mocks (deferred to a future version).

---

## 2. Architecture

### 2.1 High-Level Overview

```
┌──────────────────┐    stdio     ┌──────────────────┐    HTTPS    ┌──────────────────┐
│   LLM Client     │◄────────────►│  mcp_server.py   │◄──────────►│  Schwab API      │
│ (Claude Desktop, │              │  (FastMCP)       │            │  api.schwabapi   │
│  Gemini CLI)     │              │                  │            │  .com            │
└──────────────────┘              └────────┬─────────┘            └──────────────────┘
                                           │
                                           │ uses
                                           ▼
                                  ┌──────────────────┐
                                  │  schwabdev.Client │
                                  │  (existing lib)  │
                                  └────────┬─────────┘
                                           │
                                           │ reads/writes
                                           ▼
                                  ┌──────────────────┐
                                  │  tokens.db       │
                                  │  (SQLite)        │
                                  └──────────────────┘
```

### 2.2 Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Framework | FastMCP | High-level, decorator-based, less boilerplate, widely adopted |
| Transport | stdio (V1), structured for easy SSE addition | stdio is standard for local LLM clients |
| Code location | `mcp_server.py` at repo root | Clearly separate from library; easy to move into package later |
| Code structure | Single file | ~25 tools as thin wrappers; well under 500 lines; refactor to multi-module if/when streaming is added |
| Client mode | Synchronous `schwabdev.Client` | MCP tool calls are sequential from the model's perspective; async adds complexity for no gain |

---

## 3. Configuration

The server loads configuration through a two-tier system. Environment variables take precedence over config file values.

### 3.1 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SCHWAB_APP_KEY` | Yes* | — | Schwab app key credential |
| `SCHWAB_APP_SECRET` | Yes* | — | Schwab app secret credential |
| `SCHWAB_CALLBACK_URL` | No | `https://127.0.0.1` | OAuth callback URL |
| `SCHWAB_TOKENS_DB` | No | `~/.schwabdev/tokens.db` | Path to SQLite token database |
| `SCHWAB_ENCRYPTION_KEY` | No | `None` | Fernet encryption key for token DB |
| `SCHWAB_LOG_LEVEL` | No | `WARNING` | Logging level for the schwabdev logger |

*Required unless provided via config file.

### 3.2 Config File Fallback

**Path:** `~/.schwabdev/mcp_config.json`

```json
{
  "app_key": "...",
  "app_secret": "...",
  "callback_url": "https://127.0.0.1",
  "tokens_db": "~/.schwabdev/tokens.db",
  "encryption_key": null
}
```

### 3.3 Config Loading Logic

```
_load_config():
  1. Read env vars into a dict (skip any that are unset)
  2. If ~/.schwabdev/mcp_config.json exists:
     a. Read and parse it
     b. For each key NOT already set by env vars, use the config file value
  3. Apply defaults for callback_url and tokens_db if still unset
  4. If app_key or app_secret are still missing, raise ValueError with a clear
     message listing both configuration methods
  5. Return the final config dict
```

### 3.4 Config File Permissions

After creating `~/.schwabdev/mcp_config.json` (if the user creates it manually or via a setup script), the documentation will instruct users to set permissions to `0600`:

```bash
chmod 600 ~/.schwabdev/mcp_config.json
```

At startup, if the config file exists and its permissions are more open than `0600`, the server logs a warning:

```
WARNING: ~/.schwabdev/mcp_config.json is readable by other users. Run: chmod 600 ~/.schwabdev/mcp_config.json
```

---

## 4. Client Lifecycle

### 4.1 Lazy Initialization

The `schwabdev.Client` is **not** created at server startup. It is lazily instantiated on the first tool call via a module-level `_get_client()` function:

```python
_client: Client | None = None

def _get_client() -> Client:
    global _client
    if _client is None:
        config = _load_config()
        _client = Client(
            app_key=config["app_key"],
            app_secret=config["app_secret"],
            callback_url=config["callback_url"],
            tokens_db=config["tokens_db"],
            encryption=config.get("encryption_key"),
            timeout=10,
            call_on_auth=_handle_auth,        # SEE §4.2
            open_browser_for_auth=False,       # SEE §4.2
        )
    return _client
```

Lazy initialization means the server starts instantly and only fails when a tool is actually called — giving the model a useful error message instead of a silent startup crash.

### 4.2 Authentication & the 7-Day Refresh Problem

> [!CAUTION]
> Schwab refresh tokens expire every 7 days. When this happens, `schwabdev` triggers
> an interactive OAuth flow that calls `input()` — which would deadlock an MCP server
> running over stdio.

**Solution:** The server sets `open_browser_for_auth=False` and provides a `call_on_auth` callback:

```python
def _handle_auth(auth_url: str) -> str:
    """
    Called by schwabdev when re-authentication is needed.
    Instead of blocking on input(), raises an error with instructions.
    """
    raise AuthenticationRequiredError(
        f"Schwab authentication required. Your refresh token has expired.\n"
        f"To re-authenticate:\n"
        f"1. Open this URL in your browser: {auth_url}\n"
        f"2. Log in and authorize the app.\n"
        f"3. Copy the callback URL from the browser address bar.\n"
        f"4. Run: python mcp_server.py --auth <callback_url>\n"
        f"5. Restart the MCP server."
    )
```

`AuthenticationRequiredError` is a custom exception class defined in `mcp_server.py`. When it propagates up through a tool call, the tool's error handler catches it and returns the message as the tool result, so the model can tell the user what to do.

**Standalone auth mode:** The server supports a `--auth <callback_url>` CLI flag that:
1. Loads config.
2. Creates a `schwabdev.Client` with a `call_on_auth` that returns the provided URL.
3. Triggers token refresh.
4. Prints success/failure and exits.

This lets users re-authenticate without needing an interactive terminal attached to the MCP server process.

### 4.3 Token Health: `get_auth_status` Tool

A dedicated tool lets the model proactively check token health:

```python
@mcp.tool()
def get_auth_status() -> str:
    """Check the authentication status, including access and refresh token expiry times."""
```

Returns:
- Whether the client is initialized.
- Access token time remaining.
- Refresh token time remaining.
- A warning if the refresh token expires within 24 hours.

---

## 5. Tool Design

### 5.1 General Principles

1. **Primitive parameters only.** All tool parameters are `str`, `int`, `float`, `bool`, or `None`. No `datetime` objects. Date parameters are accepted as ISO 8601 strings (e.g., `"2026-01-15T00:00:00Z"`) and passed through to `schwabdev`, which handles string passthrough natively.

2. **1:1 mapping to Client methods.** Each tool is a thin wrapper around a `schwabdev.Client` method. No business logic in the tool layer.

3. **Descriptive docstrings.** Each tool's docstring includes parameter descriptions, valid values for enum-like parameters, and usage notes. This is the model's only documentation.

4. **Consistent error handling.** Every tool follows the same pattern (see §5.5).

5. **snake_case tool names.** MCP convention; matches Python function names.

### 5.2 Account & Trading Tools (12 tools)

| Tool | Client Method | Key Parameters |
|---|---|---|
| `get_linked_accounts` | `linked_accounts()` | — |
| `get_account_details` | `account_details()` | `account_hash: str`, `fields: str? = None` |
| `get_all_account_details` | `account_details_all()` | `fields: str? = None` |
| `get_account_orders` | `account_orders()` | `account_hash: str`, `from_entered_time: str`, `to_entered_time: str`, `max_results: int? = None`, `status: str? = None` |
| `get_all_orders` | `account_orders_all()` | `from_entered_time: str`, `to_entered_time: str`, `max_results: int? = None`, `status: str? = None` |
| `place_order` | `place_order()` | `account_hash: str`, `order_json: str` |
| `cancel_order` | `cancel_order()` | `account_hash: str`, `order_id: str` |
| `replace_order` | `replace_order()` | `account_hash: str`, `order_id: str`, `order_json: str` |
| `preview_order` | `preview_order()` | `account_hash: str`, `order_json: str` |
| `get_transactions` | `transactions()` | `account_hash: str`, `start_date: str`, `end_date: str`, `types: str`, `symbol: str? = None` |
| `get_transaction_details` | `transaction_details()` | `account_hash: str`, `transaction_id: str` |
| `get_preferences` | `preferences()` | — |

### 5.3 Market Data Tools (8 tools)

| Tool | Client Method | Key Parameters |
|---|---|---|
| `get_quotes` | `quotes()` | `symbols: str` (comma-separated), `fields: str? = None`, `indicative: bool? = False` |
| `get_quote` | `quote()` | `symbol: str`, `fields: str? = None` |
| `get_option_chains` | `option_chains()` | `symbol: str`, + all optional params as primitives |
| `get_option_expiration_chain` | `option_expiration_chain()` | `symbol: str` |
| `get_price_history` | `price_history()` | `symbol: str`, + all optional params as primitives |
| `get_movers` | `movers()` | `symbol: str`, `sort: str? = None`, `frequency: int? = None` |
| `get_market_hours` | `market_hours()` | `symbols: str` (comma-separated), `date: str? = None` |
| `get_instruments` | `instruments()` | `symbols: str`, `projection: str` |

### 5.4 Diagnostic & Helper Tools (4 tools)

| Tool | Purpose |
|---|---|
| `get_auth_status` | Check token health: initialized, access/refresh token expiry, warnings |
| `build_equity_market_order` | Helper: construct a market order JSON from `symbol`, `quantity`, `instruction` (BUY/SELL) |
| `build_equity_limit_order` | Helper: construct a limit order JSON from `symbol`, `quantity`, `price`, `instruction` (BUY/SELL) |
| `build_option_order` | Helper: construct a single-leg option order JSON from `symbol`, `quantity`, `instruction`, `contract_type`, and optional `price` (limit) |

**Order builder tools** return the order JSON as a string. They do **not** place orders. The model uses the output as input to `preview_order` or `place_order`. This avoids the model having to hand-craft complex JSON:

```python
@mcp.tool()
def build_equity_market_order(symbol: str, quantity: int, instruction: str) -> str:
    """
    Build an equity market order JSON payload. Does NOT place the order.
    Use the returned JSON with preview_order or place_order.

    Args:
        symbol: Ticker symbol (e.g., "AAPL")
        quantity: Number of shares
        instruction: "BUY" or "SELL"

    Returns:
        JSON string representing the order payload.
    """
    if instruction.upper() not in ("BUY", "SELL"):
        return "Error: instruction must be 'BUY' or 'SELL'"
    order = {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [{
            "instruction": instruction.upper(),
            "quantity": quantity,
            "instrument": {
                "symbol": symbol.upper(),
                "assetType": "EQUITY"
            }
        }]
    }
    return json.dumps(order, indent=2)
```

### 5.5 Error Handling Pattern

Every tool follows this structure:

```python
@mcp.tool()
def some_tool(param: str) -> str:
    """Tool description."""
    try:
        client = _get_client()
        response = client.some_method(param=param)
        if response.ok:
            return _format_response(response)
        else:
            return f"Schwab API error (HTTP {response.status_code}): {response.text}"
    except AuthenticationRequiredError as e:
        return str(e)
    except json.JSONDecodeError as e:
        return f"Invalid JSON input: {e}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"
```

**Key properties:**
- No exceptions leak to FastMCP — all are caught and returned as strings.
- `AuthenticationRequiredError` gets special handling with clear re-auth instructions.
- `json.JSONDecodeError` gets clear messaging for order tools.
- HTTP errors include both status code and response body.

### 5.6 `order_json` Validation

For `place_order`, `replace_order`, and `preview_order`, the `order_json` string parameter is validated before being sent to the API:

```python
def _parse_order_json(order_json: str) -> dict:
    """Parse and validate order JSON string."""
    try:
        order = json.loads(order_json)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Could not parse order JSON. Ensure it is valid JSON. "
            f"Consider using build_equity_market_order or build_equity_limit_order "
            f"to generate the order payload. Parse error: {e.msg}",
            e.doc, e.pos
        )
    if not isinstance(order, dict):
        raise ValueError("Order JSON must be a JSON object (dict), not an array or primitive.")
    return order
```

---

## 6. Response Handling

### 6.1 Standard Response Formatting

Successful API responses are formatted as pretty-printed JSON:

```python
def _format_response(response: requests.Response) -> str:
    """Format a successful API response."""
    try:
        data = response.json()
        text = json.dumps(data, indent=2)
        if len(text) > MAX_RESPONSE_SIZE:
            return _truncate_response(text)
        return text
    except json.JSONDecodeError:
        return response.text
```

### 6.2 Response Size Truncation

> [!WARNING]
> Some API responses (especially `option_chains`) can return megabytes of data, which
> would overflow the model's context window and make conversations unusably expensive.

**Mitigation:** Responses are truncated if they exceed `MAX_RESPONSE_SIZE` (default: **50,000 characters**, approximately 12,500 tokens).

```python
MAX_RESPONSE_SIZE = 50_000  # characters

def _truncate_response(text: str) -> str:
    """Truncate oversized responses with guidance."""
    truncated = text[:MAX_RESPONSE_SIZE]
    return (
        truncated + "\n\n"
        "... [RESPONSE TRUNCATED] ...\n"
        "The full response exceeded the size limit. "
        "To get more targeted results, try narrowing your query with additional parameters "
        "(e.g., strikeCount, contractType, fromDate, toDate for option chains)."
    )
```

This applies to all tools uniformly. The threshold is a module-level constant that can be adjusted.

---

## 7. Security

### 7.1 Financial Data Privacy

> [!CAUTION]
> All data returned by MCP tools is sent to your LLM provider (Anthropic, Google, etc.)
> as part of the conversation. This includes account balances, positions, transaction
> history, and order details. By using this MCP server, you accept that your financial
> data will be transmitted to third-party AI providers.

**Enforcement:**
- This warning is printed to stderr at server startup.
- This warning is documented prominently in the README section of the server docs.
- The `get_auth_status` tool description also mentions this.

### 7.2 Credential Storage

| Layer | Protection |
|---|---|
| Environment variables | Standard OS-level process isolation |
| Config file (`mcp_config.json`) | `0600` permissions enforced; startup warning if too open |
| Token database (`tokens.db`) | Optional Fernet encryption via `SCHWAB_ENCRYPTION_KEY` |
| In-process memory | Tokens live in `schwabdev.Client`; no additional copies |

### 7.3 Logging Safety

`schwabdev` uses Python's `logging` module. At `DEBUG` level, it may log token values, auth URLs, or API responses containing sensitive data. Since MCP stdio servers have stderr captured by the client, this data could leak into client-side logs.

**Mitigation:**
- Default log level is `WARNING`. Configurable via `SCHWAB_LOG_LEVEL` env var.
- Documentation warns that `DEBUG` level may expose sensitive data.
- The MCP server does NOT add its own logging of request/response bodies.

### 7.4 Order Safety

The user has chosen to rely on the LLM client's tool-approval UX for order safety. The server does **not** implement server-side confirmation.

**Mitigations provided:**
- Order builder helper tools reduce the chance of malformed orders.
- `preview_order` is available and documented as the recommended step before `place_order`.
- Tool descriptions for `place_order`, `cancel_order`, and `replace_order` include a note: `"⚠️ This tool executes a real trade. Review the order carefully before confirming."`

---

## 8. Logging

### 8.1 Startup Messages

At server startup (before entering the MCP event loop), the server prints to stderr:

```
[Schwabdev MCP] Starting server...
[Schwabdev MCP] WARNING: Financial data returned by tools will be sent to your LLM provider.
[Schwabdev MCP] Config: callback_url=https://127.0.0.1, tokens_db=~/.schwabdev/tokens.db
[Schwabdev MCP] Transport: stdio
[Schwabdev MCP] Ready.
```

Credentials (`app_key`, `app_secret`) are **never** logged, not even partially.

### 8.2 Runtime Logging

- Tool calls are logged at `INFO` level: tool name and non-sensitive parameters only.
- Errors are logged at `ERROR` level.
- The `schwabdev` library's own logger is set to the level specified by `SCHWAB_LOG_LEVEL`.

---

## 9. CLI Interface

The server has a minimal CLI for startup and standalone auth:

```
Usage:
  python mcp_server.py              # Start the MCP server (stdio transport)
  python mcp_server.py --auth URL   # Re-authenticate with a callback URL
  python mcp_server.py --help       # Show help
```

### 9.1 `--auth` Mode

When the refresh token expires (every 7 days), the user must re-authenticate:

```bash
# 1. The model (or get_auth_status tool) tells the user the auth URL
# 2. User opens the URL in a browser, logs in, copies the callback URL
# 3. User runs:
python mcp_server.py --auth "https://127.0.0.1?code=<authorization_code>&session=<session_id>"
# 4. Server refreshes tokens and exits
# 5. User restarts the MCP server (or it auto-restarts via the LLM client)
```

---

## 10. Running the Server

### 10.1 Direct Execution

```bash
# Set credentials via environment
export SCHWAB_APP_KEY="your_app_key"
export SCHWAB_APP_SECRET="your_app_secret"

# Start the server
python mcp_server.py
```

### 10.2 FastMCP Dev Inspector

For interactive testing:

```bash
mcp dev mcp_server.py
```

### 10.3 Claude Desktop Configuration

```json
{
  "mcpServers": {
    "schwabdev": {
      "command": "python",
      "args": ["/absolute/path/to/Schwabdev/mcp_server.py"],
      "env": {
        "SCHWAB_APP_KEY": "your_app_key",
        "SCHWAB_APP_SECRET": "your_app_secret"
      }
    }
  }
}
```

### 10.4 Gemini CLI Configuration

In `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "schwabdev": {
      "command": "python",
      "args": ["/absolute/path/to/Schwabdev/mcp_server.py"],
      "env": {
        "SCHWAB_APP_KEY": "your_app_key",
        "SCHWAB_APP_SECRET": "your_app_secret"
      }
    }
  }
}
```

---

## 11. Dependencies

### 11.1 New Dependencies

| Package | Purpose | Version |
|---|---|---|
| `fastmcp` | MCP server framework | Latest stable |

All other dependencies (`requests`, `aiohttp`, `websockets`, `cryptography`, `tzdata`) are already required by `schwabdev`.

### 11.2 Python Version

Python 3.11+ (inherited from `schwabdev` requirement).

---

## 12. File Structure (Final)

```
Schwabdev/
├── mcp_server.py              # NEW: The MCP server (single file)
├── schwabdev/                  # UNCHANGED: Existing library
│   ├── __init__.py
│   ├── client.py
│   ├── enums.py
│   ├── stream.py
│   ├── tokens.py
│   └── translate.py
├── docs/
│   └── ...
├── pyproject.toml              # UNCHANGED
├── README.md                   # UNCHANGED (MCP docs go in server file docstring)
└── ...
```

---

## 13. Complete Tool Inventory (24 tools)

### Account & Trading (12)

| # | Tool Name | Description |
|---|---|---|
| 1 | `get_linked_accounts` | Get all linked account numbers and encrypted hashes |
| 2 | `get_account_details` | Get details for a specific account (balances, optionally positions) |
| 3 | `get_all_account_details` | Get details for all linked accounts |
| 4 | `get_account_orders` | Get orders for a specific account within a date range |
| 5 | `get_all_orders` | Get orders across all accounts within a date range |
| 6 | `place_order` | Place an order for a specific account |
| 7 | `cancel_order` | Cancel a specific order |
| 8 | `replace_order` | Replace an existing order with a new one |
| 9 | `preview_order` | Preview an order without placing it |
| 10 | `get_transactions` | Get transactions for a specific account within a date range |
| 11 | `get_transaction_details` | Get details for a specific transaction |
| 12 | `get_preferences` | Get user preference and streaming info |

### Market Data (8)

| # | Tool Name | Description |
|---|---|---|
| 13 | `get_quotes` | Get quotes for multiple symbols (comma-separated) |
| 14 | `get_quote` | Get quote for a single symbol |
| 15 | `get_option_chains` | Get option chain for a symbol |
| 16 | `get_option_expiration_chain` | Get option expiration dates for a symbol |
| 17 | `get_price_history` | Get historical price candles for a symbol |
| 18 | `get_movers` | Get top movers in an index |
| 19 | `get_market_hours` | Get market hours for specified markets |
| 20 | `get_instruments` | Search for instruments by symbol or description |

### Diagnostics & Helpers (4)

| # | Tool Name | Description |
|---|---|---|
| 21 | `get_auth_status` | Check auth status: client initialized, token expiry times, warnings |
| 22 | `build_equity_market_order` | Build a market order JSON payload (does not place order) |
| 23 | `build_equity_limit_order` | Build a limit order JSON payload (does not place order) |
| 24 | `build_option_order` | Build a single-leg option order JSON payload (does not place order) |

---

## 14. Known Limitations & Future Work

### V1 Limitations

| Limitation | Impact | Future Mitigation |
|---|---|---|
| No rate limiting | Model can trigger API throttling with rapid calls | Add in-process rate limiter |
| No streaming tools | Cannot subscribe to real-time market data | Add streaming tools in V2 (refactor to multi-module at that point) |
| Single account only | Module-level global client supports one credential set | Support multi-account via config |
| No automated tests | Requires real API credentials to test | Add mock mode and unit tests |
| 7-day re-auth | User must manually re-authenticate weekly | Document clearly; explore long-lived token strategies |

### Rate Limiting Guidance (V1 Workaround)

Since the server has no built-in rate limiter, tool descriptions guide the model toward efficient usage:

- `get_quotes` description: *"Prefer this over get_quote for multiple symbols. Pass comma-separated symbols (e.g., 'AAPL,TSLA,NVDA') instead of making separate calls."*
- `get_option_chains` description: *"Use strikeCount, contractType, fromDate, and toDate to limit response size. Unfiltered chains for popular symbols can be very large."*

---

## 15. Spec Self-Review Checklist

- [x] **Placeholder scan:** No TBDs, TODOs, or incomplete sections.
- [x] **Internal consistency:** Architecture matches tool descriptions; error handling is uniform.
- [x] **Scope check:** Single file, ~24 tools, clear boundaries — appropriate for one implementation plan.
- [x] **Ambiguity check:** All enum-like parameters have documented valid values. Date format is specified (ISO 8601). Response truncation threshold is explicit (50,000 chars).
- [x] **Security review incorporated:** Auth deadlock (§4.2), data privacy (§7.1), credential storage (§7.2), logging safety (§7.3), order safety (§7.4), config permissions (§3.4).
