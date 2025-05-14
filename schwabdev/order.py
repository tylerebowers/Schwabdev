"""
This file contains functions to create an order object for the Schwab API.
It includes methods to create a market order, limit order, and stop order.
This is a work in progress and is not yet complete.
Coded by Tyler Bowers.
Github: https://github.com/tylerebowers/Schwab-API-Python
"""
import json


class presets:  


    @staticmethod
    def _simple_assembler(orderType, duration, instruction, quantity, symbol, assetType ,price=None):
        toRet = {
            "orderType": orderType,
            "session": "NORMAL",
            "duration": duration,
            "orderStrategyType": "SINGLE",
            "orderLegCollection": [
                {
                    "instruction": instruction,
                    "quantity": quantity,
                    "instrument": {
                        "symbol": symbol,
                        "assetType": assetType
                    }
                }
            ]
        }
        if price is not None: toRet['price'] = price
        return toRet


    @staticmethod
    def trigger_assembler(*args):
        args[0]["orderStrategyType"] = "TRIGGER"
        return json.dumps({
            **args[0],
            "childOrderStrategies": [arg for arg in args[1:]]
        })


    class equity:

        @staticmethod
        def buy_market(symbol, quantity, duration="DAY"):
            return presets._simple_assembler("MARKET", duration, "BUY", quantity, symbol, "EQUITY")

        @staticmethod
        def sell_market(symbol, quantity, duration="DAY"):
            return presets._simple_assembler("MARKET", duration, "SELL", quantity, symbol, "EQUITY")

        @staticmethod
        def buy_limited(symbol, quantity, limit_price, duration="DAY"):
            return presets._simple_assembler("LIMIT", duration, "BUY", quantity, symbol, "EQUITY", limit_price)

        @staticmethod
        def sell_limited(symbol, quantity, limit_price, duration="DAY"):
            return presets._simple_assembler("LIMIT", duration, "SELL", quantity, symbol, "EQUITY", limit_price)

        @staticmethod
        def sell_trailing_stop(symbol, quantity, stop_price_offset):
            return {
                "complexOrderStrategyType": "NONE",
                "orderType": "TRAILING_STOP",
                "session": "NORMAL",
                "stopPriceLinkBasis": "BID",
                "stopPriceLinkType": "VALUE",
                "stopPriceOffset": stop_price_offset,
                "duration": "DAY",
                "orderStrategyType": "SINGLE",
                "orderLegCollection": [
                    {
                        "instruction": "SELL",
                        "quantity": quantity,
                        "instrument": {
                            "symbol": symbol,
                            "assetType": "EQUITY"
                        }
                    }
                ]
            }


    class option:
        @staticmethod
        def buy_limited(symbol, quantity, limit_price, duration="DAY"):
            return presets._simple_assembler("LIMIT", duration, "BUY", quantity, symbol, "OPTION", limit_price)

        @staticmethod
        def sell_limited(symbol, quantity, limit_price, duration="DAY"):
            return presets._simple_assembler("LIMIT", duration, "SELL", quantity, symbol, "OPTION", limit_price)

        @staticmethod
        def buy_vertical_call_spread(buySymbol, sellSymbol, buyQuantity, sellQuantity, price):
            return {
                "orderType": "NET_DEBIT",
                "session": "NORMAL",
                "price": price,
                "duration": "DAY",
                "orderStrategyType": "SINGLE",
                "orderLegCollection": [
                    {
                        "instruction": "BUY_TO_OPEN",
                        "quantity": buyQuantity,
                        "instrument": {
                            "symbol": buySymbol,
                            "assetType": "OPTION"
                        }
                    },
                    {
                        "instruction": "SELL_TO_OPEN",
                        "quantity": sellQuantity,
                        "instrument": {
                            "symbol": sellSymbol,
                            "assetType": "OPTION"
                        }
                    }
                ]
            }
