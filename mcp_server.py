#!/usr/bin/env python3
"""
Schwabdev MCP Server

A local MCP (Model Context Protocol) server that wraps the schwabdev Python library,
allowing AI assistants (Claude Desktop, Gemini CLI, etc.) to interact with the
Charles Schwab API through MCP tools.

Usage:
    python mcp_server.py                  Start the MCP server (stdio transport)
    python mcp_server.py --auth           Interactive re-authentication flow
    python mcp_server.py --auth <URL>     Non-interactive re-authentication with callback URL
    python mcp_server.py --help           Show help

Configuration:
    Set credentials via environment variables (preferred) or ~/.schwabdev/mcp_config.json.
    Environment variables take precedence over config file values.

    Required:
        SCHWAB_APP_KEY          App key credential
        SCHWAB_APP_SECRET       App secret credential

    Optional:
        SCHWAB_CALLBACK_URL     OAuth callback URL (default: https://127.0.0.1)
        SCHWAB_TOKENS_DB        Path to token database (default: ~/.schwabdev/tokens.db)
        SCHWAB_ENCRYPTION_KEY   Fernet encryption key for token DB (default: None)
        SCHWAB_LOG_LEVEL        Logging level (default: WARNING)

WARNING:
    All data returned by MCP tools is sent to your LLM provider (Anthropic, Google, etc.)
    as part of the conversation. This includes account balances, positions, transaction
    history, and order details. By using this MCP server, you accept that your financial
    data will be transmitted to third-party AI providers.

See: docs/superpowers/specs/2026-05-30-schwabdev-mcp-server-design.md
"""

import argparse
import datetime
import json
import logging
import os
import stat
import sys

try:
    from fastmcp import FastMCP
except ImportError:
    print(
        "Error: fastmcp is required. Install it with: pip install fastmcp",
        file=sys.stderr,
    )
    sys.exit(1)

from schwabdev.client import Client

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

MAX_RESPONSE_SIZE = 50_000  # characters (~12,500 tokens)
CONFIG_FILE_PATH = os.path.expanduser("~/.schwabdev/mcp_config.json")

_PRIVACY_WARNING = (
    "WARNING: Financial data returned by tools will be sent to your LLM provider."
)

# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------


class AuthenticationRequiredError(Exception):
    """Raised when Schwab OAuth re-authentication is needed."""

    pass


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


def _load_config() -> dict:
    """
    Load configuration from environment variables, falling back to config file.
    Environment variables take precedence.

    Returns:
        dict with keys: app_key, app_secret, callback_url, tokens_db, encryption_key

    Raises:
        ValueError: if app_key or app_secret are missing from all sources.
    """
    config: dict[str, str | None] = {
        "app_key": os.environ.get("SCHWAB_APP_KEY"),
        "app_secret": os.environ.get("SCHWAB_APP_SECRET"),
        "callback_url": os.environ.get("SCHWAB_CALLBACK_URL"),
        "tokens_db": os.environ.get("SCHWAB_TOKENS_DB"),
        "encryption_key": os.environ.get("SCHWAB_ENCRYPTION_KEY"),
    }

    # Fall back to config file for any missing values
    if os.path.exists(CONFIG_FILE_PATH):
        _check_config_permissions()
        try:
            with open(CONFIG_FILE_PATH, "r") as f:
                file_config = json.load(f)
            for key in config:
                if config[key] is None and key in file_config:
                    config[key] = file_config[key]
        except (json.JSONDecodeError, OSError) as e:
            print(
                f"[Schwabdev MCP] Warning: Could not read config file {CONFIG_FILE_PATH}: {e}",
                file=sys.stderr,
            )

    # Apply defaults
    if config["callback_url"] is None:
        config["callback_url"] = "https://127.0.0.1"
    if config["tokens_db"] is None:
        config["tokens_db"] = "~/.schwabdev/tokens.db"

    # Validate required fields
    missing = []
    if not config["app_key"]:
        missing.append("SCHWAB_APP_KEY")
    if not config["app_secret"]:
        missing.append("SCHWAB_APP_SECRET")
    if missing:
        raise ValueError(
            f"Missing required configuration: {', '.join(missing)}.\n"
            f"Set them as environment variables or in {CONFIG_FILE_PATH}.\n"
            f"See: python mcp_server.py --help"
        )

    return config


def _check_config_permissions():
    """Warn if the config file has overly permissive permissions."""
    try:
        file_stat = os.stat(CONFIG_FILE_PATH)
        mode = file_stat.st_mode
        if mode & (stat.S_IRGRP | stat.S_IROTH | stat.S_IWGRP | stat.S_IWOTH):
            print(
                f"[Schwabdev MCP] WARNING: {CONFIG_FILE_PATH} is readable by other users. "
                f"Run: chmod 600 {CONFIG_FILE_PATH}",
                file=sys.stderr,
            )
    except OSError:
        pass


# ---------------------------------------------------------------------------
# Client Lifecycle
# ---------------------------------------------------------------------------

_client: Client | None = None


def _handle_auth(auth_url: str) -> str:
    """
    Called by schwabdev when re-authentication is needed.
    Raises an error with clear instructions instead of blocking on input().
    """
    raise AuthenticationRequiredError(
        f"Schwab authentication required. Your refresh token has expired.\n"
        f"To re-authenticate:\n"
        f"1. Open this URL in your browser: {auth_url}\n"
        f"2. Log in and authorize the app.\n"
        f"3. Copy the full URL from the browser address bar after redirect.\n"
        f"4. Run: python mcp_server.py --auth <callback_url>\n"
        f"5. Restart the MCP server."
    )


def _get_client() -> Client:
    """Get or lazily initialize the schwabdev Client."""
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
            call_on_auth=_handle_auth,
            open_browser_for_auth=False,
        )
    return _client


# ---------------------------------------------------------------------------
# Response Handling
# ---------------------------------------------------------------------------


def _format_response(response) -> str:
    """Format an API response as pretty-printed JSON, with truncation for large payloads."""
    try:
        data = response.json()
        text = json.dumps(data, indent=2)
    except (json.JSONDecodeError, ValueError):
        text = response.text

    if len(text) > MAX_RESPONSE_SIZE:
        return _truncate_response(text)
    return text


def _truncate_response(text: str) -> str:
    """Truncate an oversized response with guidance."""
    truncated = text[:MAX_RESPONSE_SIZE]
    return (
        truncated
        + "\n\n"
        "... [RESPONSE TRUNCATED] ...\n"
        "The full response exceeded the size limit. "
        "To get more targeted results, try narrowing your query with additional parameters "
        "(e.g., strikeCount, contractType, fromDate, toDate for option chains)."
    )


def _parse_order_json(order_json: str) -> dict:
    """Parse and validate an order JSON string."""
    try:
        order = json.loads(order_json)
    except json.JSONDecodeError as e:
        raise json.JSONDecodeError(
            f"Could not parse order JSON. Ensure it is valid JSON. "
            f"Consider using build_equity_market_order or build_equity_limit_order "
            f"to generate the order payload. Parse error: {e.msg}",
            e.doc,
            e.pos,
        )
    if not isinstance(order, dict):
        raise ValueError(
            "Order JSON must be a JSON object (dict), not an array or primitive."
        )
    return order


def _call_api(method_name: str, *args, **kwargs) -> str:
    """
    Call a schwabdev Client method by name with standard error handling.
    The client is resolved inside the try/except so init errors are caught.

    Args:
        method_name: Name of the method on schwabdev.Client to call.
        *args, **kwargs: Arguments to pass to the method.

    Returns:
        Formatted response on success or error string on failure.
    """
    try:
        client = _get_client()
        func = getattr(client, method_name)
        response = func(*args, **kwargs)
        if response.ok:
            return _format_response(response)
        return f"Schwab API error (HTTP {response.status_code}): {response.text}"
    except AuthenticationRequiredError as e:
        return str(e)
    except json.JSONDecodeError as e:
        return f"Invalid JSON input: {e}"
    except ValueError as e:
        return f"Invalid input: {e}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# MCP Server Instance
# ---------------------------------------------------------------------------

mcp = FastMCP(
    "Schwabdev",
    instructions=(
        "MCP server for interacting with the Charles Schwab brokerage API. "
        "Provides tools for account information, market data, and order management. "
        "Use get_linked_accounts first to obtain account hashes needed by other tools. "
        "For placing orders, prefer using the build_* helper tools to construct order "
        "JSON, then pass the result to preview_order before place_order."
    ),
)

# ===========================================================================
# Account & Trading Tools (12)
# ===========================================================================


@mcp.tool()
def get_linked_accounts() -> str:
    """
    Get all linked Schwab account numbers and their encrypted hash values.
    Call this first — the encrypted account hash is required by most other tools.

    Returns:
        JSON array of objects with 'accountNumber' and 'hashValue' fields.
    """
    return _call_api("linked_accounts")


@mcp.tool()
def get_account_details(account_hash: str, fields: str | None = None) -> str:
    """
    Get details for a specific Schwab account including balances and optionally positions.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        fields: Optional. Set to "positions" to include position details.

    Returns:
        JSON object with account balances and optional position details.
    """
    return _call_api(
        "account_details", accountHash=account_hash, fields=fields
    )


@mcp.tool()
def get_all_account_details(fields: str | None = None) -> str:
    """
    Get details for all linked Schwab accounts including balances and optionally positions.

    Args:
        fields: Optional. Set to "positions" to include position details.

    Returns:
        JSON array of account detail objects.
    """
    return _call_api("account_details_all", fields=fields)


@mcp.tool()
def get_account_orders(
    account_hash: str,
    from_entered_time: str,
    to_entered_time: str,
    max_results: int | None = None,
    status: str | None = None,
) -> str:
    """
    Get orders for a specific account within a date range. Maximum date range is 1 year.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        from_entered_time: Start date in ISO 8601 format (e.g., "2026-01-01T00:00:00Z").
        to_entered_time: End date in ISO 8601 format.
        max_results: Maximum number of results (default: 3000).
        status: Filter by order status. Valid values: "AWAITING_PARENT_ORDER",
            "AWAITING_CONDITION", "AWAITING_STOP_CONDITION", "AWAITING_MANUAL_REVIEW",
            "ACCEPTED", "AWAITING_UR_OUT", "PENDING_ACTIVATION", "QUEUED", "WORKING",
            "REJECTED", "PENDING_CANCEL", "CANCELED", "PENDING_REPLACE", "REPLACED",
            "FILLED", "EXPIRED", "NEW", "AWAITING_RELEASE_TIME",
            "PENDING_ACKNOWLEDGEMENT", "PENDING_RECALL".

    Returns:
        JSON array of order objects.
    """
    return _call_api(
        "account_orders",
        accountHash=account_hash,
        fromEnteredTime=from_entered_time,
        toEnteredTime=to_entered_time,
        maxResults=max_results,
        status=status,
    )


@mcp.tool()
def get_all_orders(
    from_entered_time: str,
    to_entered_time: str,
    max_results: int | None = None,
    status: str | None = None,
) -> str:
    """
    Get orders across all linked accounts within a date range. Maximum date range is 1 year.

    Args:
        from_entered_time: Start date in ISO 8601 format (e.g., "2026-01-01T00:00:00Z").
        to_entered_time: End date in ISO 8601 format.
        max_results: Maximum number of results (default: 3000).
        status: Filter by order status (see get_account_orders for valid values).

    Returns:
        JSON array of order objects.
    """
    return _call_api(
        "account_orders_all",
        fromEnteredTime=from_entered_time,
        toEnteredTime=to_entered_time,
        maxResults=max_results,
        status=status,
    )


@mcp.tool()
def place_order(account_hash: str, order_json: str) -> str:
    """
    ⚠️ REAL TRADE: Place an order for a specific account. This executes a real trade.
    Review the order carefully before confirming.

    Prefer using build_equity_market_order, build_equity_limit_order, or
    build_option_order to construct the order JSON, and preview_order to
    validate it before placing.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        order_json: JSON string representing the order payload.

    Returns:
        Success message with order ID (if available), or error details.
    """
    try:
        order = _parse_order_json(order_json)
        response = _get_client().place_order(accountHash=account_hash, order=order)
        if response.ok:
            location = response.headers.get("Location", "")
            order_id = (
                location.split("/")[-1]
                if location
                else "N/A (possibly filled immediately)"
            )
            return f"Order placed successfully. Order ID: {order_id}"
        return f"Schwab API error (HTTP {response.status_code}): {response.text}"
    except AuthenticationRequiredError as e:
        return str(e)
    except json.JSONDecodeError as e:
        return f"Invalid JSON input: {e}"
    except ValueError as e:
        return f"Invalid input: {e}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def cancel_order(account_hash: str, order_id: str) -> str:
    """
    ⚠️ REAL TRADE: Cancel a specific order. This cancels a real pending order.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        order_id: The order ID to cancel.

    Returns:
        Success or error message.
    """
    try:
        response = _get_client().cancel_order(
            accountHash=account_hash, orderId=order_id
        )
        if response.ok:
            return f"Order {order_id} cancelled successfully."
        return f"Schwab API error (HTTP {response.status_code}): {response.text}"
    except AuthenticationRequiredError as e:
        return str(e)
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def replace_order(account_hash: str, order_id: str, order_json: str) -> str:
    """
    ⚠️ REAL TRADE: Replace an existing order with a new one. The old order is
    cancelled and a new order is created.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        order_id: The order ID to replace.
        order_json: JSON string representing the new order payload.

    Returns:
        Success or error message.
    """
    try:
        order = _parse_order_json(order_json)
        response = _get_client().replace_order(
            accountHash=account_hash, orderId=order_id, order=order
        )
        if response.ok:
            return f"Order {order_id} replaced successfully."
        return f"Schwab API error (HTTP {response.status_code}): {response.text}"
    except AuthenticationRequiredError as e:
        return str(e)
    except json.JSONDecodeError as e:
        return f"Invalid JSON input: {e}"
    except ValueError as e:
        return f"Invalid input: {e}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def preview_order(account_hash: str, order_json: str) -> str:
    """
    Preview an order without placing it. Use this to validate order parameters
    and see estimated costs before calling place_order.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        order_json: JSON string representing the order payload.

    Returns:
        JSON preview of the order including estimated costs and fees.
    """
    try:
        order = _parse_order_json(order_json)
        return _call_api(
            "preview_order",
            accountHash=account_hash,
            orderObject=order,
        )
    except AuthenticationRequiredError as e:
        return str(e)
    except json.JSONDecodeError as e:
        return f"Invalid JSON input: {e}"
    except ValueError as e:
        return f"Invalid input: {e}"
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def get_transactions(
    account_hash: str,
    start_date: str,
    end_date: str,
    types: str,
    symbol: str | None = None,
) -> str:
    """
    Get transactions for a specific account. Maximum 3000 transactions. Maximum date range is 1 year.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        start_date: Start date in ISO 8601 format (e.g., "2026-01-01T00:00:00Z").
        end_date: End date in ISO 8601 format.
        types: Transaction type. Valid values: "TRADE", "RECEIVE_AND_DELIVER",
            "DIVIDEND_OR_INTEREST", "ACH_RECEIPT", "ACH_DISBURSEMENT",
            "CASH_RECEIPT", "CASH_DISBURSEMENT", "ELECTRONIC_FUND",
            "WIRE_IN", "WIRE_OUT", "JOURNAL", "MEMORANDUM", "MARGIN_CALL",
            "MONEY_MARKET", "SMA_ADJUSTMENT".
        symbol: Optional ticker symbol to filter transactions.

    Returns:
        JSON array of transaction objects.
    """
    return _call_api(
        "transactions",
        accountHash=account_hash,
        startDate=start_date,
        endDate=end_date,
        types=types,
        symbol=symbol,
    )


@mcp.tool()
def get_transaction_details(account_hash: str, transaction_id: str) -> str:
    """
    Get details for a specific transaction.

    Args:
        account_hash: Encrypted account hash from get_linked_accounts.
        transaction_id: The transaction ID.

    Returns:
        JSON object with transaction details.
    """
    return _call_api(
        "transaction_details",
        accountHash=account_hash,
        transactionId=transaction_id,
    )


@mcp.tool()
def get_preferences() -> str:
    """
    Get user preference information for the logged-in user, including streaming configuration.

    Returns:
        JSON object with user preferences and streamer info.
    """
    return _call_api("preferences")


# ===========================================================================
# Market Data Tools (8)
# ===========================================================================


@mcp.tool()
def get_quotes(
    symbols: str, fields: str | None = None, indicative: bool = False
) -> str:
    """
    Get quotes for one or more symbols. Prefer this over get_quote for multiple
    symbols — pass comma-separated values (e.g., "AAPL,TSLA,NVDA") instead of
    making separate calls.

    Args:
        symbols: Comma-separated ticker symbols (e.g., "AAPL,TSLA,NVDA").
        fields: Optional. "all", "quote", or "fundamental".
        indicative: Whether to include indicative quotes (default: false).

    Returns:
        JSON object keyed by symbol with quote data.
    """
    return _call_api(
        "quotes", symbols=symbols, fields=fields, indicative=indicative
    )


@mcp.tool()
def get_quote(symbol: str, fields: str | None = None) -> str:
    """
    Get quote for a single symbol. For multiple symbols, use get_quotes instead.

    Args:
        symbol: Ticker symbol (e.g., "AAPL").
        fields: Optional. "all", "quote", or "fundamental".

    Returns:
        JSON object with quote data.
    """
    return _call_api("quote", symbol_id=symbol, fields=fields)


@mcp.tool()
def get_option_chains(
    symbol: str,
    contract_type: str | None = None,
    strike_count: int | None = None,
    include_underlying_quote: bool | None = None,
    strategy: str | None = None,
    interval: str | None = None,
    strike: float | None = None,
    range: str | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    volatility: float | None = None,
    underlying_price: float | None = None,
    interest_rate: float | None = None,
    days_to_expiration: int | None = None,
    exp_month: str | None = None,
    option_type: str | None = None,
    entitlement: str | None = None,
) -> str:
    """
    Get option chain for a symbol. Use parameters to filter results — unfiltered
    chains for popular symbols can be very large and may be truncated.

    Args:
        symbol: Underlying ticker symbol (e.g., "AAPL").
        contract_type: "CALL", "PUT", or "ALL".
        strike_count: Number of strikes above and below at-the-money.
        include_underlying_quote: Include underlying quote (true/false).
        strategy: "SINGLE", "ANALYTICAL", "COVERED", "VERTICAL", "CALENDAR",
            "STRANGLE", "STRADDLE", "BUTTERFLY", "CONDOR", "DIAGONAL",
            "COLLAR", or "ROLL".
        interval: Strike interval for spread strategies.
        strike: Specific strike price.
        range: "ITM", "NTM", "OTM", "SAK", "SBK", "SNK", or "ALL".
        from_date: Start expiration date (YYYY-MM-DD). Cannot be before today.
        to_date: End expiration date (YYYY-MM-DD).
        volatility: Volatility for analytical strategy.
        underlying_price: Underlying price for analytical strategy.
        interest_rate: Interest rate for analytical strategy.
        days_to_expiration: Days to expiration filter.
        exp_month: Expiration month (e.g., "JAN", "FEB", ..., "ALL").
        option_type: "ALL", "STANDARD", or "NON_STANDARD".
        entitlement: "ALL", "PAYING_PRO", or "NON_PRO".

    Returns:
        JSON object with option chain data.
    """
    return _call_api(
        "option_chains",
        symbol=symbol,
        contractType=contract_type,
        strikeCount=strike_count,
        includeUnderlyingQuote=include_underlying_quote,
        strategy=strategy,
        interval=interval,
        strike=strike,
        range=range,
        fromDate=from_date,
        toDate=to_date,
        volatility=volatility,
        underlyingPrice=underlying_price,
        interestRate=interest_rate,
        daysToExpiration=days_to_expiration,
        expMonth=exp_month,
        optionType=option_type,
        entitlement=entitlement,
    )


@mcp.tool()
def get_option_expiration_chain(symbol: str) -> str:
    """
    Get option expiration dates for a symbol. Useful for discovering available
    expirations before querying the full option chain.

    Args:
        symbol: Underlying ticker symbol (e.g., "AAPL").

    Returns:
        JSON object with available expiration dates.
    """
    return _call_api("option_expiration_chain", symbol=symbol)


@mcp.tool()
def get_price_history(
    symbol: str,
    period_type: str | None = None,
    period: int | None = None,
    frequency_type: str | None = None,
    frequency: int | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
    need_extended_hours_data: bool | None = None,
    need_previous_close: bool | None = None,
) -> str:
    """
    Get historical price candles for a symbol.

    Args:
        symbol: Ticker symbol (e.g., "AAPL").
        period_type: "day", "month", "year", or "ytd".
        period: Number of periods to show.
        frequency_type: "minute", "daily", "weekly", or "monthly".
        frequency: Frequency interval. For minute: 1, 5, 10, 15, 30.
            For daily/weekly/monthly: 1.
        start_date: Start date in ISO 8601 format (e.g., "2026-01-01T00:00:00Z").
        end_date: End date in ISO 8601 format.
        need_extended_hours_data: Include extended hours data (true/false).
        need_previous_close: Include previous close (true/false).

    Returns:
        JSON object with candle history data.
    """
    return _call_api(
        "price_history",
        symbol=symbol,
        periodType=period_type,
        period=period,
        frequencyType=frequency_type,
        frequency=frequency,
        startDate=start_date,
        endDate=end_date,
        needExtendedHoursData=need_extended_hours_data,
        needPreviousClose=need_previous_close,
    )


@mcp.tool()
def get_movers(
    symbol: str, sort: str | None = None, frequency: int | None = None
) -> str:
    """
    Get top movers in a specific index. Must be called during market hours.

    Args:
        symbol: Index symbol. Valid values: "$DJI", "$COMPX", "$SPX", "NYSE",
            "NASDAQ", "OTCBB", "INDEX_ALL", "EQUITY_ALL", "OPTION_ALL",
            "OPTION_PUT", "OPTION_CALL".
        sort: Sort direction. "VOLUME", "TRADES", "PERCENT_CHANGE_UP",
            or "PERCENT_CHANGE_DOWN".
        frequency: Time frequency. Valid values: 0, 1, 5, 10, 30, 60.

    Returns:
        JSON object with top movers data.
    """
    return _call_api(
        "movers", symbol=symbol, sort=sort, frequency=frequency
    )


@mcp.tool()
def get_market_hours(symbols: str, date: str | None = None) -> str:
    """
    Get market hours for specified markets on a given date.

    Args:
        symbols: Comma-separated market identifiers. Valid values: "equity",
            "option", "bond", "future", "forex".
        date: Date in YYYY-MM-DD format (default: today).

    Returns:
        JSON object with market hours for each specified market.
    """
    symbol_list = [s.strip() for s in symbols.split(",")]
    return _call_api("market_hours", symbols=symbol_list, date=date)


@mcp.tool()
def get_instruments(symbols: str, projection: str) -> str:
    """
    Search for instruments by symbol or description.

    Args:
        symbols: Search query string (symbol or description text).
        projection: Search type. Valid values:
            "symbol-search" - search by symbol prefix
            "symbol-regex" - search by symbol regex
            "desc-search" - search by description
            "desc-regex" - search by description regex
            "search" - search by both symbol and description
            "fundamental" - get fundamental data for exact symbol

    Returns:
        JSON object with matching instruments.
    """
    return _call_api(
        "instruments", symbols=symbols, projection=projection
    )


# ===========================================================================
# Diagnostic & Helper Tools (4)
# ===========================================================================


@mcp.tool()
def get_auth_status() -> str:
    """
    Check authentication status including token expiry times.
    Use this to proactively check if re-authentication will be needed soon.

    Note: All financial data returned by other tools is transmitted to your
    LLM provider as part of the conversation.

    Returns:
        JSON object with auth status, token expiry times, and warnings.
    """
    try:
        global _client
        status: dict = {"initialized": _client is not None}

        if _client is not None:
            now = datetime.datetime.now(datetime.timezone.utc)
            tokens = _client.tokens

            at_issued = tokens._access_token_issued
            rt_issued = tokens._refresh_token_issued
            at_timeout = tokens._access_token_timeout
            rt_timeout = tokens._refresh_token_timeout

            at_remaining = datetime.timedelta(seconds=at_timeout) - (now - at_issued)
            rt_remaining = datetime.timedelta(seconds=rt_timeout) - (now - rt_issued)

            # Clamp to zero
            at_remaining = max(at_remaining, datetime.timedelta(0))
            rt_remaining = max(rt_remaining, datetime.timedelta(0))

            status["access_token_expires_in"] = str(at_remaining).split(".")[0]
            status["refresh_token_expires_in"] = str(rt_remaining).split(".")[0]

            warnings = []
            if rt_remaining < datetime.timedelta(hours=24):
                warnings.append(
                    "Refresh token expires within 24 hours! "
                    "Re-authenticate soon using: python mcp_server.py --auth"
                )
            if at_remaining < datetime.timedelta(minutes=2):
                warnings.append(
                    "Access token is about to expire. It will be refreshed "
                    "automatically on the next API call."
                )
            if warnings:
                status["warnings"] = warnings
        else:
            status["message"] = (
                "Client not yet initialized. "
                "It will be initialized on the first API call."
            )

        return json.dumps(status, indent=2)
    except Exception as e:
        return f"Unexpected error: {type(e).__name__}: {e}"


@mcp.tool()
def build_equity_market_order(symbol: str, quantity: int, instruction: str) -> str:
    """
    Build an equity market order JSON payload. Does NOT place the order.
    Pass the returned JSON to preview_order to validate, then to place_order to execute.

    Args:
        symbol: Ticker symbol (e.g., "AAPL").
        quantity: Number of shares (must be positive).
        instruction: "BUY" or "SELL".

    Returns:
        JSON string representing the order payload.
    """
    instruction = instruction.upper()
    if instruction not in ("BUY", "SELL"):
        return "Error: instruction must be 'BUY' or 'SELL'."
    if quantity <= 0:
        return "Error: quantity must be a positive integer."

    order = {
        "orderType": "MARKET",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": instruction,
                "quantity": quantity,
                "instrument": {"symbol": symbol.upper(), "assetType": "EQUITY"},
            }
        ],
    }
    return json.dumps(order, indent=2)


@mcp.tool()
def build_equity_limit_order(
    symbol: str, quantity: int, price: float, instruction: str
) -> str:
    """
    Build an equity limit order JSON payload. Does NOT place the order.
    Pass the returned JSON to preview_order to validate, then to place_order to execute.

    Args:
        symbol: Ticker symbol (e.g., "AAPL").
        quantity: Number of shares (must be positive).
        price: Limit price per share.
        instruction: "BUY" or "SELL".

    Returns:
        JSON string representing the order payload.
    """
    instruction = instruction.upper()
    if instruction not in ("BUY", "SELL"):
        return "Error: instruction must be 'BUY' or 'SELL'."
    if quantity <= 0:
        return "Error: quantity must be a positive integer."
    if price <= 0:
        return "Error: price must be positive."

    order = {
        "orderType": "LIMIT",
        "session": "NORMAL",
        "price": str(price),
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": instruction,
                "quantity": quantity,
                "instrument": {"symbol": symbol.upper(), "assetType": "EQUITY"},
            }
        ],
    }
    return json.dumps(order, indent=2)


@mcp.tool()
def build_option_order(
    symbol: str,
    quantity: int,
    instruction: str,
    price: float | None = None,
) -> str:
    """
    Build a single-leg option order JSON payload. Does NOT place the order.
    Pass the returned JSON to preview_order to validate, then to place_order to execute.

    Args:
        symbol: Option symbol in OCC format (e.g., "AAPL  261218C00150000").
            Use get_option_chains to find valid option symbols.
        quantity: Number of contracts (must be positive).
        instruction: "BUY_TO_OPEN", "SELL_TO_OPEN", "BUY_TO_CLOSE", or "SELL_TO_CLOSE".
        price: Limit price per contract. If omitted, creates a market order.

    Returns:
        JSON string representing the order payload.
    """
    instruction = instruction.upper()
    valid_instructions = (
        "BUY_TO_OPEN",
        "SELL_TO_OPEN",
        "BUY_TO_CLOSE",
        "SELL_TO_CLOSE",
    )
    if instruction not in valid_instructions:
        return f"Error: instruction must be one of: {', '.join(valid_instructions)}."
    if quantity <= 0:
        return "Error: quantity must be a positive integer."

    order = {
        "orderType": "MARKET" if price is None else "LIMIT",
        "session": "NORMAL",
        "duration": "DAY",
        "orderStrategyType": "SINGLE",
        "orderLegCollection": [
            {
                "instruction": instruction,
                "quantity": quantity,
                "instrument": {"symbol": symbol, "assetType": "OPTION"},
            }
        ],
    }
    if price is not None:
        if price <= 0:
            return "Error: price must be positive."
        order["price"] = str(price)

    return json.dumps(order, indent=2)


# ===========================================================================
# CLI
# ===========================================================================


def _run_auth(callback_url: str | None = None):
    """Run the standalone authentication flow."""
    config = _load_config()

    if callback_url:
        # Non-interactive: use the provided callback URL
        print("[Schwabdev MCP] Using provided callback URL for authentication...")
        client = Client(
            app_key=config["app_key"],
            app_secret=config["app_secret"],
            callback_url=config["callback_url"],
            tokens_db=config["tokens_db"],
            encryption=config.get("encryption_key"),
            timeout=30,
            call_on_auth=lambda auth_url: callback_url,
            open_browser_for_auth=False,
        )
    else:
        # Interactive: use the default browser + input() flow
        print("[Schwabdev MCP] Starting interactive authentication flow...")
        client = Client(
            app_key=config["app_key"],
            app_secret=config["app_secret"],
            callback_url=config["callback_url"],
            tokens_db=config["tokens_db"],
            encryption=config.get("encryption_key"),
            timeout=30,
            open_browser_for_auth=True,
        )

    # Force token refresh to ensure new tokens are obtained
    client.update_tokens(force_refresh_token=True)
    print("[Schwabdev MCP] Tokens updated successfully.")
    client.close()


def main():
    parser = argparse.ArgumentParser(
        description="Schwabdev MCP Server — AI assistant interface to the Charles Schwab API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python mcp_server.py                  Start the MCP server\n"
            "  python mcp_server.py --auth            Interactive re-authentication\n"
            '  python mcp_server.py --auth "https://127.0.0.1?code=..."\n'
            "                                        Non-interactive re-authentication\n"
        ),
    )
    parser.add_argument(
        "--auth",
        nargs="?",
        const="__interactive__",
        default=None,
        metavar="CALLBACK_URL",
        help="Re-authenticate with Schwab. Optionally provide the callback URL "
        "for non-interactive mode. Without a URL, opens the browser for "
        "interactive authentication.",
    )

    args = parser.parse_args()

    # Configure logging
    log_level = os.environ.get("SCHWAB_LOG_LEVEL", "WARNING").upper()
    logging.getLogger("Schwabdev").setLevel(
        getattr(logging, log_level, logging.WARNING)
    )

    if args.auth is not None:
        # Auth mode
        callback = None if args.auth == "__interactive__" else args.auth
        try:
            _run_auth(callback)
        except Exception as e:
            print(f"[Schwabdev MCP] Authentication failed: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        # Server mode
        print("[Schwabdev MCP] Starting server...", file=sys.stderr)
        print(f"[Schwabdev MCP] {_PRIVACY_WARNING}", file=sys.stderr)
        print("[Schwabdev MCP] Transport: stdio", file=sys.stderr)
        print("[Schwabdev MCP] Ready.", file=sys.stderr)
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
