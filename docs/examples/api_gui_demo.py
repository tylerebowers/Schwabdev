"""
Tkinter GUI demo for Schwabdev (Unofficial Schwab API Python Wrapper)

Requirements:
    pip install schwabdev python-dotenv

Environment:
    Create a .env file in the same directory with:
        app_key=YOUR_APP_KEY
        app_secret=YOUR_APP_SECRET
        callback_url=YOUR_CALLBACK_URL
"""

import os
import json
import logging
import datetime
import tkinter as tk
from tkinter import ttk, messagebox

from dotenv import load_dotenv
import schwabdev

# ------------------ Client setup ------------------ #

logging.basicConfig(level=logging.INFO)
load_dotenv()

APP_KEY = os.getenv("app_key")
APP_SECRET = os.getenv("app_secret")
CALLBACK_URL = os.getenv("callback_url")

if not APP_KEY or not APP_SECRET or not CALLBACK_URL:
    print("WARNING: app_key, app_secret, or callback_url missing from .env")

client = schwabdev.Client(APP_KEY, APP_SECRET, CALLBACK_URL)


def default_days_back():
    return 30


def now_utc():
    return datetime.datetime.now(datetime.timezone.utc)


# Example order used as default JSON for orderDict params
EXAMPLE_ORDER = {
    "orderType": "LIMIT",
    "session": "NORMAL",
    "duration": "DAY",
    "orderStrategyType": "SINGLE",
    "price": "10.00",
    "orderLegCollection": [
        {
            "instruction": "BUY",
            "quantity": 1,
            "instrument": {
                "symbol": "AMD",
                "assetType": "EQUITY",
            },
        }
    ],
}
EXAMPLE_ORDER_JSON = json.dumps(EXAMPLE_ORDER, indent=2)


# ------------------ API configuration ------------------ #

API_CONFIG = {
    # -------------- Accounts & Orders -------------- #
    "linked_accounts": {
        "label": "Linked Accounts",
        "description": (
            "Account numbers in plain text cannot be used outside of headers or request/response bodies.\n"
            "Invoke this service first to retrieve the list of plain text/encrypted value pairs, and use\n"
            "encrypted account values for all subsequent calls for any accountNumber request.\n\n"
            "Returns all linked account numbers and hashes."
        ),
        "params": [],
        "call": lambda c, p: c.linked_accounts(),
    },
    "account_details_all": {
        "label": "Account Details (All)",
        "description": (
            "All the linked account information for the user logged in.\n"
            "Balances are displayed by default; positions will be displayed based on the 'positions' flag."
        ),
        "params": [
            {
                "name": "fields",
                "label": "Fields",
                "widget": "dropdown",
                "options": ["", "positions"],  # from docstring
            },
        ],
        "call": lambda c, p: c.account_details_all(
            fields=p.get("fields") or None
        ),
    },
    "account_details": {
        "label": "Account Details (Single)",
        "description": (
            "Specific account information with balances and positions.\n"
            "Balance information is displayed by default; positions will be returned based on the 'positions' flag."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "fields",
                "label": "Fields",
                "widget": "dropdown",
                "options": ["", "positions"],
            },
        ],
        "call": lambda c, p: c.account_details(
            p.get("accountHash"),
            fields=p.get("fields") or None,
        ),
    },
    "account_orders": {
        "label": "Account Orders",
        "description": (
            "All orders for a specific account. Orders retrieved can be filtered based on input parameters.\n"
            "Maximum date range is 1 year."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "days_back",
                "label": "Days Back",
                "widget": "entry",
                "dtype": "int",
                "default": "30",
            },
            {
                "name": "maxResults",
                "label": "Max Results (default 3000)",
                "widget": "entry",
                "dtype": "int",
            },
            {
                "name": "status",
                "label": "Status (optional)",
                "widget": "entry",
            },
        ],
        "call": lambda c, p: c.account_orders(
            p.get("accountHash"),
            now_utc() - datetime.timedelta(days=p.get("days_back") or default_days_back()),
            now_utc(),
            maxResults=p.get("maxResults"),
            status=p.get("status") or None,
        ),
    },
    "place_order": {
        "label": "Place Order",
        "description": (
            "Place an order for a specific account.\n\n"
            "The order JSON should match the Schwab order schema (see Schwabdev documentation)."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "orderDict",
                "label": "Order JSON (dict)",
                "widget": "text",
                "dtype": "json",
                "required": True,
                "default": EXAMPLE_ORDER_JSON,
            },
        ],
        "call": lambda c, p: c.place_order(
            p.get("accountHash"),
            p.get("orderDict"),
        ),
    },
    "order_details": {
        "label": "Order Details",
        "description": (
            "Get a specific order by its ID for a specific account."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "orderId",
                "label": "Order ID",
                "widget": "entry",
                "required": True,
            },
        ],
        "call": lambda c, p: c.order_details(
            p.get("accountHash"),
            p.get("orderId"),
        ),
    },
    "cancel_order": {
        "label": "Cancel Order",
        "description": (
            "Cancel a specific order by its ID for a specific account."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "orderId",
                "label": "Order ID",
                "widget": "entry",
                "required": True,
            },
        ],
        "call": lambda c, p: c.cancel_order(
            p.get("accountHash"),
            p.get("orderId"),
        ),
    },
    "replace_order": {
        "label": "Replace Order",
        "description": (
            "Replace an existing order for an account.\n"
            "The existing order will be replaced by the new order. Once replaced, the old order will be\n"
            "canceled and a new order will be created."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "orderId",
                "label": "Order ID",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "orderDict",
                "label": "Order JSON (dict)",
                "widget": "text",
                "dtype": "json",
                "required": True,
                "default": EXAMPLE_ORDER_JSON,
            },
        ],
        "call": lambda c, p: c.replace_order(
            p.get("accountHash"),
            p.get("orderId"),
            p.get("orderDict"),
        ),
    },
    "account_orders_all": {
        "label": "Account Orders (All Accounts)",
        "description": (
            "Get all orders for all accounts.\n"
            "Maximum date range is 1 year; maximum of 3000 orders returned by default."
        ),
        "params": [
            {
                "name": "days_back",
                "label": "Days Back",
                "widget": "entry",
                "dtype": "int",
                "default": "30",
            },
            {
                "name": "maxResults",
                "label": "Max Results (default 3000)",
                "widget": "entry",
                "dtype": "int",
            },
            {
                "name": "status",
                "label": "Status (optional)",
                "widget": "entry",
            },
        ],
        "call": lambda c, p: c.account_orders_all(
            now_utc() - datetime.timedelta(days=p.get("days_back") or default_days_back()),
            now_utc(),
            maxResults=p.get("maxResults"),
            status=p.get("status") or None,
        ),
    },
    "preview_order": {
        "label": "Preview Order",
        "description": (
            "Preview an order for a specific account without actually placing it.\n"
            "The order JSON should match the Schwab order schema."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "orderDict",
                "label": "Order JSON (dict)",
                "widget": "text",
                "dtype": "json",
                "required": True,
                "default": EXAMPLE_ORDER_JSON,
            },
        ],
        "call": lambda c, p: c.preview_order(
            p.get("accountHash"),
            p.get("orderDict"),
        ),
    },
    "transactions": {
        "label": "Transactions",
        "description": (
            "All transactions for a specific account.\n"
            "Maximum number of transactions in response is 3000. Maximum date range is 1 year."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "days_back",
                "label": "Days Back",
                "widget": "entry",
                "dtype": "int",
                "default": "30",
            },
            {
                "name": "types",
                "label": "Types (e.g. TRADE)",
                "widget": "entry",
                "default": "TRADE",
            },
            {
                "name": "symbol",
                "label": "Symbol (optional)",
                "widget": "entry",
            },
        ],
        "call": lambda c, p: c.transactions(
            p.get("accountHash"),
            now_utc() - datetime.timedelta(days=p.get("days_back") or default_days_back()),
            now_utc(),
            p.get("types") or "TRADE",
            symbol=p.get("symbol") or None,
        ),
    },
    "transaction_details": {
        "label": "Transaction Details",
        "description": (
            "Get specific transaction information for a specific account."
        ),
        "params": [
            {
                "name": "accountHash",
                "label": "Account Hash",
                "widget": "entry",
                "required": True,
            },
            {
                "name": "transactionId",
                "label": "Transaction ID",
                "widget": "entry",
                "required": True,
            },
        ],
        "call": lambda c, p: c.transaction_details(
            p.get("accountHash"),
            p.get("transactionId"),
        ),
    },
    "preferences": {
        "label": "User Preferences",
        "description": (
            "Get user preference information for the logged in user.\n"
            "Returns user preferences and streaming info."
        ),
        "params": [],
        "call": lambda c, p: c.preferences(),
    },

    # -------------- Market Data -------------- #
    "quotes": {
        "label": "Quotes (Multiple Symbols)",
        "description": (
            "Get quotes for a list of tickers."
        ),
        "params": [
            {
                "name": "symbols",
                "label": "Symbols (comma-separated)",
                "widget": "entry",
                "default": "AAPL,AMD",
                "dtype": "list_str",
            },
            {
                "name": "fields",
                "label": "Fields",
                "widget": "dropdown",
                "options": ["", "all", "quote", "fundamental"],
            },
            {
                "name": "indicative",
                "label": "Indicative",
                "widget": "checkbox",
                "default": False,
            },
        ],
        "call": lambda c, p: c.quotes(
            p.get("symbols") or [],
            fields=p.get("fields") or None,
            indicative=p.get("indicative") or False,
        ),
    },
    "quote": {
        "label": "Quote (Single Symbol)",
        "description": (
            "Get quote for a single symbol."
        ),
        "params": [
            {
                "name": "symbol_id",
                "label": "Symbol",
                "widget": "entry",
                "default": "INTC",
            },
            {
                "name": "fields",
                "label": "Fields",
                "widget": "dropdown",
                "options": ["", "all", "quote", "fundamental"],
            },
        ],
        "call": lambda c, p: c.quote(
            p.get("symbol_id"),
            fields=p.get("fields") or None,
        ),
    },
    "option_chains": {
        "label": "Option Chains",
        "description": (
            "Get option chain information including options contracts associated with each expiration for a ticker.\n"
            "Note: Some calls can exceed data limits, requiring additional parameters to narrow results."
        ),
        "params": [
            {
                "name": "symbol",
                "label": "Symbol",
                "widget": "entry",
                "default": "AAPL",
            },
            {
                "name": "contractType",
                "label": "Contract Type",
                "widget": "dropdown",
                "options": ["", "CALL", "PUT", "ALL"],
            },
            {
                "name": "range",
                "label": "Range",
                "widget": "dropdown",
                "options": ["", "ITM", "NTM", "OTM"],
            },
            {
                "name": "includeUnderlyingQuote",
                "label": "Include Underlying Quote",
                "widget": "checkbox",
                "default": False,
            },
            {
                "name": "optionType",
                "label": "Option Type",
                "widget": "dropdown",
                "options": ["", "ALL", "CALL", "PUT"],
            },
            {
                "name": "entitlement",
                "label": "Entitlement",
                "widget": "dropdown",
                "options": ["", "ALL", "AMERICAN", "EUROPEAN"],
            },
        ],
        "call": lambda c, p: c.option_chains(
            p.get("symbol"),
            contractType=p.get("contractType") or None,
            strikeCount=None,
            includeUnderlyingQuote=p.get("includeUnderlyingQuote") or None,
            strategy=None,
            interval=None,
            strike=None,
            range=p.get("range") or None,
            fromDate=None,
            toDate=None,
            volatility=None,
            underlyingPrice=None,
            interestRate=None,
            daysToExpiration=None,
            expMonth=None,
            optionType=p.get("optionType") or None,
            entitlement=p.get("entitlement") or None,
        ),
    },
    "option_expiration_chain": {
        "label": "Option Expiration Chain",
        "description": (
            "Get an option expiration chain for a ticker."
        ),
        "params": [
            {
                "name": "symbol",
                "label": "Symbol",
                "widget": "entry",
                "default": "AAPL",
            },
        ],
        "call": lambda c, p: c.option_expiration_chain(
            p.get("symbol"),
        ),
    },
    "price_history": {
        "label": "Price History",
        "description": (
            "Get price history for a ticker."
        ),
        "params": [
            {
                "name": "symbol",
                "label": "Symbol",
                "widget": "entry",
                "default": "AAPL",
            },
            {
                "name": "periodType",
                "label": "Period Type",
                "widget": "dropdown",
                "options": ["", "day", "month", "year", "ytd"],
            },
            {
                "name": "period",
                "label": "Period (int)",
                "widget": "entry",
                "dtype": "int",
            },
            {
                "name": "frequencyType",
                "label": "Frequency Type",
                "widget": "dropdown",
                "options": ["", "minute", "daily", "weekly", "monthly"],
            },
            {
                "name": "frequency",
                "label": "Frequency (int)",
                "widget": "entry",
                "dtype": "int",
            },
            {
                "name": "needExtendedHoursData",
                "label": "Need Extended Hours",
                "widget": "checkbox",
                "default": False,
            },
            {
                "name": "needPreviousClose",
                "label": "Need Previous Close",
                "widget": "checkbox",
                "default": False,
            },
        ],
        "call": lambda c, p: c.price_history(
            p.get("symbol"),
            periodType=p.get("periodType") or None,
            period=p.get("period"),
            frequencyType=p.get("frequencyType") or None,
            frequency=p.get("frequency"),
            startDate=None,
            endDate=None,
            needExtendedHoursData=p.get("needExtendedHoursData") or None,
            needPreviousClose=p.get("needPreviousClose") or None,
        ),
    },
    "movers": {
        "label": "Movers",
        "description": (
            "Get movers in a specific index and direction.\n"
            "Must be called within market hours."
        ),
        "params": [
            {
                "name": "symbol",
                "label": "Index Symbol",
                "widget": "dropdown",
                "options": [
                    "$DJI",
                    "$COMPX",
                    "$SPX",
                    "NYSE",
                    "NASDAQ",
                    "OTCBB",
                    "INDEX_ALL",
                    "EQUITY_ALL",
                    "OPTION_ALL",
                    "OPTION_PUT",
                    "OPTION_CALL",
                ],
                "default": "$DJI",
            },
            {
                "name": "sort",
                "label": "Sort",
                "widget": "dropdown",
                "options": [
                    "",
                    "VOLUME",
                    "TRADES",
                    "PERCENT_CHANGE_UP",
                    "PERCENT_CHANGE_DOWN",
                ],
            },
            {
                "name": "frequency",
                "label": "Frequency (minutes)",
                "widget": "dropdown",
                "options": ["", "0", "1", "5", "10", "30", "60"],
                "dtype": "int",
            },
        ],
        "call": lambda c, p: c.movers(
            p.get("symbol"),
            sort=p.get("sort") or None,
            frequency=p.get("frequency"),
        ),
    },
    "market_hours": {
        "label": "Market Hours (Multiple Markets)",
        "description": (
            "Get market hours for dates in the future across different markets."
        ),
        "params": [
            {
                "name": "symbols",
                "label": "Markets (comma-separated)",
                "widget": "entry",
                "default": "equity,option",
                "dtype": "list_str",
            },
        ],
        "call": lambda c, p: c.market_hours(
            p.get("symbols") or [],
            date=None,
        ),
    },
    "market_hour": {
        "label": "Market Hours (Single Market)",
        "description": (
            "Get market hours for dates in the future for a single market."
        ),
        "params": [
            {
                "name": "market_id",
                "label": "Market",
                "widget": "dropdown",
                "options": ["equity", "option", "bond", "future", "forex"],
                "default": "equity",
            },
        ],
        "call": lambda c, p: c.market_hour(
            p.get("market_id"),
            date=None,
        ),
    },
    "instruments": {
        "label": "Instruments (Search)",
        "description": (
            "Get instruments for a list of symbols or search text with a given projection."
        ),
        "params": [
            {
                "name": "symbol",
                "label": "Symbol / Search Text",
                "widget": "entry",
                "default": "AAPL",
            },
            {
                "name": "projection",
                "label": "Projection",
                "widget": "dropdown",
                "options": [
                    "symbol-search",
                    "symbol-regex",
                    "desc-search",
                    "desc-regex",
                    "search",
                    "fundamental",
                ],
                "default": "fundamental",
            },
        ],
        "call": lambda c, p: c.instruments(
            p.get("symbol"),
            p.get("projection"),
        ),
    },
    "instrument_cusip": {
        "label": "Instrument by CUSIP",
        "description": (
            "Get instrument for a single CUSIP."
        ),
        "params": [
            {
                "name": "cusip_id",
                "label": "CUSIP",
                "widget": "entry",
                "default": "037833100",  # AAPL
            },
        ],
        "call": lambda c, p: c.instrument_cusip(
            p.get("cusip_id"),
        ),
    },
}


# ------------------ GUI logic ------------------ #

class SchwabGuiApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Schwabdev Tkinter Demo")

        self.current_param_widgets = {}  # name -> (meta, var, widget)

        self.create_widgets()
        self.build_param_form("linked_accounts")

    def create_widgets(self):
        # Layout: left (endpoint + description) and right (params + result)
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Left pane
        left_frame = ttk.Frame(self.root, padding=5)
        left_frame.grid(row=0, column=0, sticky="ns")
        left_frame.columnconfigure(0, weight=1)

        ttk.Label(left_frame, text="API Call").grid(row=0, column=0, sticky="w")

        self.endpoint_var = tk.StringVar()
        endpoint_names = list(API_CONFIG.keys())
        self.endpoint_combo = ttk.Combobox(
            left_frame,
            textvariable=self.endpoint_var,
            values=endpoint_names,
            state="readonly",
            width=28,
        )
        self.endpoint_combo.grid(row=1, column=0, sticky="ew", pady=4)
        self.endpoint_combo.bind("<<ComboboxSelected>>", self.on_endpoint_change)
        if endpoint_names:
            self.endpoint_var.set(endpoint_names[0])

        # Call title
        self.endpoint_title_label = ttk.Label(
            left_frame,
            text="",
            font=("TkDefaultFont", 9, "bold"),
            wraplength=240,
            justify="left",
        )
        self.endpoint_title_label.grid(row=2, column=0, sticky="w", pady=(4, 2))

        # Docstring-based description
        self.endpoint_desc_label = ttk.Label(
            left_frame,
            text="",
            wraplength=240,
            justify="left",
        )
        self.endpoint_desc_label.grid(row=3, column=0, sticky="w", pady=(0, 2))

        # Right pane
        right_frame = ttk.Frame(self.root, padding=5)
        right_frame.grid(row=0, column=1, sticky="nsew")
        right_frame.rowconfigure(2, weight=1)
        right_frame.columnconfigure(0, weight=1)

        # Params frame
        self.params_frame = ttk.LabelFrame(right_frame, text="Parameters")
        self.params_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))
        self.params_frame.columnconfigure(1, weight=1)

        # Call button
        button_frame = ttk.Frame(right_frame)
        button_frame.grid(row=1, column=0, sticky="ew")
        button_frame.columnconfigure(0, weight=1)

        self.call_button = ttk.Button(button_frame, text="Call API", command=self.call_api)
        self.call_button.grid(row=0, column=0, sticky="w", pady=5)

        # Result text
        result_frame = ttk.LabelFrame(right_frame, text="Result")
        result_frame.grid(row=2, column=0, sticky="nsew")
        result_frame.rowconfigure(0, weight=1)
        result_frame.columnconfigure(0, weight=1)

        self.result_text = tk.Text(result_frame, wrap="none", height=20)
        self.result_text.grid(row=0, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(result_frame, orient="vertical", command=self.result_text.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        x_scroll = ttk.Scrollbar(result_frame, orient="horizontal", command=self.result_text.xview)
        x_scroll.grid(row=1, column=0, sticky="ew")

        self.result_text.configure(yscrollcommand=y_scroll.set, xscrollcommand=x_scroll.set)

    def on_endpoint_change(self, event=None):
        name = self.endpoint_var.get()
        self.build_param_form(name)

    def build_param_form(self, endpoint_name: str):
        # Clear old widgets
        for child in self.params_frame.winfo_children():
            child.destroy()
        self.current_param_widgets.clear()

        config = API_CONFIG.get(endpoint_name)
        if not config:
            return

        # Title + description (from docstring)
        pretty_label = config.get("label", endpoint_name)
        self.endpoint_title_label.config(text=pretty_label)

        desc = config.get("description", "")
        self.endpoint_desc_label.config(text=desc)

        # Build parameter widgets
        params = config.get("params", [])
        for row, meta in enumerate(params):
            label = ttk.Label(self.params_frame, text=meta.get("label", meta["name"]))
            label.grid(row=row, column=0, sticky="nw", padx=4, pady=2)

            widget_type = meta.get("widget", "entry")

            if widget_type == "entry":
                var = tk.StringVar()
                default = meta.get("default", "")
                if default is not None:
                    var.set(str(default))
                entry = ttk.Entry(self.params_frame, textvariable=var)
                entry.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
                self.current_param_widgets[meta["name"]] = (meta, var, entry)

            elif widget_type == "dropdown":
                var = tk.StringVar()
                options = meta.get("options", [])
                default = meta.get("default", options[0] if options else "")
                var.set(default)
                combo = ttk.Combobox(
                    self.params_frame,
                    textvariable=var,
                    values=options,
                    state="readonly",
                )
                combo.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
                self.current_param_widgets[meta["name"]] = (meta, var, combo)

            elif widget_type == "checkbox":
                var = tk.BooleanVar(value=bool(meta.get("default", False)))
                chk = ttk.Checkbutton(self.params_frame, variable=var)
                chk.grid(row=row, column=1, sticky="w", padx=4, pady=2)
                self.current_param_widgets[meta["name"]] = (meta, var, chk)

            elif widget_type == "text":
                text_widget = tk.Text(self.params_frame, height=6, width=40)
                default = meta.get("default")
                if default:
                    text_widget.insert("1.0", default)
                text_widget.grid(row=row, column=1, sticky="ew", padx=4, pady=2)
                self.current_param_widgets[meta["name"]] = (meta, None, text_widget)

        self.params_frame.update_idletasks()

    def call_api(self):
        endpoint_name = self.endpoint_var.get()
        config = API_CONFIG.get(endpoint_name)
        if not config:
            messagebox.showerror("Error", f"Unknown endpoint: {endpoint_name}")
            return

        params_dict = {}
        # Collect values from widgets
        for name, (meta, var, widget) in self.current_param_widgets.items():
            widget_type = meta.get("widget", "entry")
            dtype = meta.get("dtype", "string")

            if widget_type in ("entry", "dropdown"):
                raw = var.get().strip()
                if raw == "":
                    if meta.get("required"):
                        messagebox.showerror("Missing parameter", f"{meta.get('label', name)} is required.")
                        return
                    value = None
                else:
                    if dtype == "int":
                        try:
                            value = int(raw)
                        except ValueError:
                            messagebox.showerror("Invalid value", f"{meta.get('label', name)} must be an integer.")
                            return
                    elif dtype == "float":
                        try:
                            value = float(raw)
                        except ValueError:
                            messagebox.showerror("Invalid value", f"{meta.get('label', name)} must be a number.")
                            return
                    elif dtype == "list_str":
                        value = [s.strip() for s in raw.split(",") if s.strip()]
                    else:
                        value = raw

            elif widget_type == "checkbox":
                value = bool(var.get())

            elif widget_type == "text":
                raw = widget.get("1.0", "end-1c").strip()
                if raw == "":
                    if meta.get("required"):
                        messagebox.showerror("Missing parameter", f"{meta.get('label', name)} is required.")
                        return
                    value = None
                else:
                    if dtype == "json":
                        try:
                            value = json.loads(raw)
                        except json.JSONDecodeError as e:
                            messagebox.showerror(
                                "Invalid JSON",
                                f"{meta.get('label', name)} must be valid JSON.\n\n{e}",
                            )
                            return
                    else:
                        value = raw
            else:
                value = var.get() if var is not None else None

            params_dict[name] = value

        # Call API
        try:
            resp = config["call"](client, params_dict)
            try:
                data = resp.json()
                text = json.dumps(data, indent=2)
            except ValueError:
                text = resp.text
        except Exception as e:
            text = f"Error during API call:\n{e!r}"

        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)


def main():
    root = tk.Tk()
    app = SchwabGuiApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
