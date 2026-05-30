# Model Context Protocol (MCP) Server

Schwabdev includes a first-class local **MCP (Model Context Protocol) Server**. This allows you to integrate your Charles Schwab developer account with AI assistants (such as **Claude Desktop**, **Cursor IDE**, and others) using a local standard protocol. 

The AI assistant can inspect account details, look up quotes/option chains, build orders, and execute trades securely under your direct terminal supervision.

---

## What is MCP?

The Model Context Protocol (MCP) is an open-standard protocol that enables LLM clients to securely read data from and execute actions in local tools/databases. By running the Schwabdev MCP server locally on your machine, your AI assistant can invoke Schwab API endpoints on demand as part of your conversation.

---

## 1. Quick Start

### Installation
Ensure you have the virtual environment activated and the required `fastmcp` package installed:
```bash
pip install fastmcp
```

### Configuration
The MCP server uses a two-tier configuration loader. Environment variables take precedence over config file values.

#### Option A: Environment Variables
Configure these in your terminal profile (e.g., `~/.bashrc` or `~/.zshrc`):
```bash
export SCHWAB_APP_KEY="your_developer_app_key"
export SCHWAB_APP_SECRET="your_developer_app_secret"
export SCHWAB_CALLBACK_URL="https://127.0.0.1"      # Matches Schwab developer portal callback
export SCHWAB_TOKENS_DB="~/.schwabdev/tokens.db"     # Token database location
export SCHWAB_ENCRYPTION_KEY=""                     # Optional Fernet key for token DB encryption
```

#### Option B: Configuration File Fallback
Create the configuration directory and file:
```bash
mkdir -p ~/.schwabdev
touch ~/.schwabdev/mcp_config.json
chmod 600 ~/.schwabdev/mcp_config.json
```
Populate `~/.schwabdev/mcp_config.json` with your credentials:
```json
{
  "app_key": "your_developer_app_key",
  "app_secret": "your_developer_app_secret",
  "callback_url": "https://127.0.0.1",
  "tokens_db": "~/.schwabdev/tokens.db",
  "encryption_key": null
}
```
*Note: If the configuration file exists and has permissions more permissive than `0600`, the server logs a warning on startup for security reasons.*

---

## 2. The 7-Day Token Expiry Solution

Schwab API refresh tokens expire every **7 days**. When they expire, standard headless processes normally deadlock waiting for keyboard inputs (`input()`). 

To prevent this, the Schwabdev MCP Server runs headless by default: if a tool call determines authentication is needed, it yields an `AuthenticationRequiredError` containing full instructions and a login URL back to the AI assistant (which presents it to you).

### Standalone Re-Authentication

#### Method A: Interactive Browser Mode
Run the following in your terminal to complete browser login and save tokens:
```bash
python mcp_server.py --auth
```
This opens your browser, logins to Schwab, prompts you to select accounts, and redirects to your callback URL (e.g., `https://127.0.0.1?code=...`). Copy this callback URL, paste it into the terminal prompt, and press Enter.

#### Method B: Headless Update Mode
If your MCP client alerts you that auth is required, copy the redirect URL from your browser and update the token DB directly:
```bash
python mcp_server.py --auth "PASTE_THE_FULL_REDIRECT_URL_HERE"
```

---

## 3. Integration with LLM Clients

### Claude Desktop
Add this config block to your Claude Desktop configuration file:
* **MacOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
* **Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
* **Linux:** `~/.config/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "schwabdev": {
      "command": "python",
      "args": [
        "/absolute/path/to/your/Schwabdev/mcp_server.py"
      ],
      "env": {
        "SCHWAB_APP_KEY": "YOUR_APP_KEY",
        "SCHWAB_APP_SECRET": "YOUR_APP_SECRET",
        "SCHWAB_CALLBACK_URL": "https://127.0.0.1",
        "SCHWAB_TOKENS_DB": "/absolute/path/to/your/tokens.db"
      }
    }
  }
}
```

### Cursor IDE
1. Open Cursor Settings -> **Features** -> **MCP**.
2. Click **+ Add New MCP Server**.
3. Fill in details:
   - **Name:** `schwabdev`
   - **Type:** `command`
   - **Command:** `python /absolute/path/to/your/Schwabdev/mcp_server.py`
4. Provide environment variables in your terminal profile, or configure them using the fallback `~/.schwabdev/mcp_config.json` file.

---

## 4. Exposed Tools (24 Tools)

The server exposes 24 tools categorised into four functional areas:

### Accounts & Portfolio (9 Tools)
* **`get_linked_accounts`**: Retrieves Schwab account numbers and encrypted hash values. **Call this tool first.** The resulting account hash is required by almost all other tools.
* **`get_account_details`**: Retrieves details including balances and optionally position details (use `fields="positions"`).
* **`get_all_account_details`**: Gets details across all linked accounts.
* **`get_account_orders`**: Gets orders for a specific account within a date range.
* **`get_all_orders`**: Retrieves orders across all accounts.
* **`get_transactions`**: Returns transaction ledger records.
* **`get_transaction_details`**: Inspects a specific ledger transaction.
* **`get_preferences`**: Returns Schwab account preferences.
* **`get_auth_status`**: Diagnostic check showing access and refresh token expiry times.

### Market Data (8 Tools)
* **`get_quotes`**: Gets quotes for multiple comma-separated symbols (e.g. `AAPL,MSFT`). **Prefer this over get_quote.**
* **`get_quote`**: Real-time quote for a single symbol.
* **`get_option_chains`**: Option contracts, expirations, and pricing chains.
* **`get_option_expiration_chain`**: Available expiration dates for a symbol.
* **`get_price_history`**: Historical daily/intraday candles.
* **`get_movers`**: Lists index movers ($SPX, NYSE, COMPX) during market hours.
* **`get_market_hours`**: Hours of operations.
* **`get_instruments`**: Search by prefix/regex or get fundamentals.

### Safety Order Builders (3 Tools)
* **`build_equity_market_order`**: Helper to construct standard Market order payloads.
* **`build_equity_limit_order`**: Helper to construct standard Limit order payloads.
* **`build_option_order`**: Helper to construct Option orders using OCC symbols.

### Live Order Execution (4 Tools)
* **`preview_order`**: Validates a constructed order JSON without executing it. Returns costs and fees.
* **`place_order`**: ⚠️ **REAL TRADE.** Sends order JSON to Schwab for execution.
* **`cancel_order`**: ⚠️ **REAL CANCEL.** Cancels an active working order.
* **`replace_order`**: ⚠️ **REAL REPLACE.** Modifies an active order.

---

## 5. Order Safety Protocol

To prevent accidental trade executions, AI assistants are instructed to enforce a strict **Order Safety Protocol**:

1. **Safety Builders First**: The assistant must always use `build_*` tools to generate the correct JSON payload.
2. **Preview Before Placing**: The assistant must pass the generated payload to `preview_order` to check commissions, fees, and buying power effects.
3. **Explicit Consent**: The assistant must print the preview results and wait for your explicit confirmation before calling `place_order`.

---

## 6. Privacy & Safety Warning

All financial data returned by tools is processed locally, but it is transmitted to your third-party LLM provider (e.g., Anthropic, OpenAI, or Google) as part of your conversation history. Do not use this server if you do not want your account numbers (masked), balances, positions, and trades sent to these providers.
