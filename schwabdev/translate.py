"""
These fields are available to stream through the Schwab Streamer.
This dict is meant for use in translating the numerical fields to a human-readable name.
Access as field_maps[service][field] (for most)
"""

import datetime

stream_fields = {
    "LEVELONE_EQUITIES": ["Symbol", "Bid Price", "Ask Price", "Last Price", "Bid Size", "Ask Size", "Ask ID", "Bid ID",
                          "Total Volume", "Last Size", "High Price", "Low Price", "Close Price", "Exchange ID",
                          "Marginable", "Description", "Last ID", "Open Price", "Net Change", "52 Week High",
                          "52 Week Low", "PE Ratio", "Annual Dividend Amount", "Dividend Yield", "NAV",
                          "Exchange Name", "Dividend Date", "Regular Market Quote", "Regular Market Trade",
                          "Regular Market Last Price", "Regular Market Last Size", "Regular Market Net Change",
                          "Security Status", "Mark Price", "Quote Time in Long", "Trade Time in Long",
                          "Regular Market Trade Time in Long", "Bid Time", "Ask Time", "Ask MIC ID",
                          "Bid MIC ID", "Last MIC ID", "Net Percent Change", "Regular Market Percent Change",
                          "Mark Price Net Change", "Mark Price Percent Change", "Hard to Borrow Quantity",
                          "Hard To Borrow Rate", "Hard to Borrow", "shortable", "Post-Market Net Change",
                          "Post-Market Percent Change"],
    "LEVELONE_OPTIONS": ["Symbol", "Description", "Bid Price", "Ask Price", "Last Price", "High Price",
                         "Low Price", "Close Price", "Total Volume", "Open Interest", "Volatility",
                         "Money Intrinsic Value", "Expiration Year", "Multiplier", "Digits", "Open Price",
                         "Bid Size", "Ask Size", "Last Size", "Net Change", "Strike Price", "Contract Type",
                         "Underlying", "Expiration Month", "Deliverables", "Time Value", "Expiration Day",
                         "Days to Expiration", "Delta", "Gamma", "Theta", "Vega", "Rho", "Security Status",
                         "Theoretical Option Value", "Underlying Price", "UV Expiration Type", "Mark Price",
                         "Quote Time in Long", "Trade Time in Long", "Exchange", "Exchange Name",
                         "Last Trading Day", "Settlement Type", "Net Percent Change", "Mark Price Net Change",
                         "Mark Price Percent Change", "Implied Yield", "isPennyPilot", "Option Root",
                         "52 Week High", "52 Week Low", "Indicative Ask Price", "Indicative Bid Price",
                         "Indicative Quote Time", "Exercise Type"],
    "LEVELONE_FUTURES": ["Symbol", "Bid Price", "Ask Price", "Last Price", "Bid Size", "Ask Size", "Bid ID",
                         "Ask ID", "Total Volume", "Last Size", "Quote Time ", "Trade Time ", "High Price",
                         "Low Price", "Close Price", "Exchange ID", "Description", "Last ID", "Open Price",
                         "Net Change", "Future Percent Change", "Exchange Name", "Security Status",
                         "Open Interest", "Mark", "Tick", "Tick Amount", "Product", "Future Price Format",
                         "Future Trading Hours", "Future Is Tradable", "Future Multiplier", "Future Is Active",
                         "Future Settlement Price", "Future Active Symbol", "Future Expiration Date",
                         "Expiration Style", "Ask Time", "Bid Time", "Quoted In Session", "Settlement Date"],
    "LEVELONE_FUTURES_OPTIONS": ["Symbol", "Bid Price", "Ask Price", "Last Price", "Bid Size", "Ask Size",
                                 "Bid ID", "Ask ID", "Total Volume", "Last Size", "Quote Time", "Trade Time",
                                 "High Price", "Low Price", "Close Price", "Last ID", "Description",
                                 "Open Price", "Open Interest", "Mark", "Tick", "Tick Amount",
                                 "Future Multiplier", "Future Settlement Price", "Underlying Symbol",
                                 "Strike Price", "Future Expiration Date", "Expiration Style", "Contract Type",
                                 "Security Status", "Exchange", "Exchange Name"],
    "LEVELONE_FOREX": ["Symbol", "Bid Price", "Ask Price", "Last Price", "Bid Size", "Ask Size",
                       "Total Volume", "Last Size", "Quote Time", "Trade Time", "High Price", "Low Price",
                       "Close Price", "Exchange", "Description", "Open Price", "Net Change", "Percent Change",
                       "Exchange Name", "Digits", "Security Status", "Tick", "Tick Amount", "Product",
                       "Trading Hours", "Is Tradable", "Market Maker", "52 Week High", "52 Week Low", "Mark"],
    "NYSE_BOOK": {0: "Symbol", 1: "Market Snapshot Time", 2: "Bid Side Levels", 3: "Ask Side Levels",
                  "Price Levels": ["Price", "Aggregate Size", "Market Maker Count" "Array of Market Makers"],
                  "Market Makers": ["Market Maker ID", "Size", "Quote Time"]},
    "NASDAQ_BOOK": {0: "Symbol", 1: "Market Snapshot Time", 2: "Bid Side Levels", 3: "Ask Side Levels",
                    "Price Levels": ["Price", "Aggregate Size", "Market Maker Count" "Array of Market Makers"],
                    "Market Makers": ["Market Maker ID", "Size", "Quote Time"]},
    "OPTIONS_BOOK": {0: "Symbol", 1: "Market Snapshot Time", 2: "Bid Side Levels", 3: "Ask Side Levels",
                     "Price Levels": ["Price", "Aggregate Size", "Market Maker Count" "Array of Market Makers"],
                     "Market Makers": ["Market Maker ID", "Size", "Quote Time"]},
    #"CHART_EQUITY": ["key", "Open Price", "High Price", "Low Price", "Close Price", "Volume", "Sequence", "Chart Time", "Chart Day"], # from schwab docs (wrong)
    "CHART_EQUITY": ["key", "Sequence", "Open Price", "High Price", "Low Price", "Close Price", "Volume", "Chart Time", "Chart Day"], # corrected
    "CHART_FUTURES": ["key", "Chart Time", "Open Price", "High Price", "Low Price", "Close Price", "Volume"],
    "SCREENER_EQUITY": ["symbol", "timestamp", "sortField", "frequency", "Items"],
    "SCREENER_OPTION": ["symbol", "timestamp", "sortField", "frequency", "Items"],
    "ACCT_ACTIVITY": {"seq": "Sequence", "key": "Key", 1: "Account", 2: "Message Type", 3: "Message Data"}}

def translate_data(response) -> list[str]:
    """
    Translate field numbers to field names

    Returns:
        list[str]: list of field names
    """
    if isinstance(response, dict) and "data" in response:
        response = response.get("data", response)
    if isinstance(response, list):
        for item in response:
            if isinstance(item, dict):
                service = item.get("service", None)
                timestamp = item.get("timestamp", None)
                content = item.get("content", None)
                if timestamp:
                    item["timestamp"] = datetime.datetime.fromtimestamp(timestamp / 1000)

                if service and content and service.startswith("LEVELONE_"):
                    if isinstance(content, list):
                        for quote in content:
                            for field, value in quote.copy().items():
                                if field.isdigit():
                                    new_field = translate_field(service, field)
                                    quote[new_field] = quote.pop(field)
    return response
    
    
def translate_field(service: str, field: str|int) -> str:
    """
    Translate field number to field name

    Args:
        field (str|int): field number
    Returns:
        str: field name
    """
    mapping = stream_fields.get(service.upper(), None)
    if mapping is None:
        return str(field)
    try:
        if isinstance(mapping, dict):
            return mapping.get(field, str(field))
        elif isinstance(mapping, list):
            index = int(field)
            if 0 <= index < len(mapping):
                return mapping[index]
            else:
                return str(field)
        else:
            return str(field)
    except Exception:
        return str(field)