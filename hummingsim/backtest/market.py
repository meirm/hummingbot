
from hummingbot.market.market_base import MarketBase
from typing import (
    List,
    Tuple,
)
from decimal import Decimal

class QuantizationParams:
    def __init__(self,
                  trading_pair,
                  price_precision,
                  price_decimals,
                  order_size_precision,
                  order_size_decimals):
        self.trading_pair = trading_pair
        self.price_precision = price_precision
        self.price_decimals = price_decimals
        self.order_size_precision = order_size_precision
        self.order_size_decimals = order_size_decimals
    
    def __repr__(self):
        return (f"QuantizationParams('{self.trading_pair}', {self.price_precision}, {self.price_decimals}, "
                f"{self.order_size_precision}, {self.order_size_decimals})")

class BacktestMarket(MarketBase):
    def __init__(self):
        super().__init__()
        self._mock = True
        self._balance = list()
        self._price = list()
        self._listener = list()
    
    def config(self, base_currency, fee_base_currency, quote_currency, fee_quote_currency, kargs):
        self._base_currency = base_currency
        self._quote_currency = quote_currency
        self._fee_base_currency = fee_base_currency
        self._fee_quote_currency = fee_quote_currency
        self._config = kargs

    def add_data(self, loader):
        raise("Implementation pending")

    def set_quantization_param(self, something):
        raise("Implementation pending")

    def set_balance(self, currency, amount):
        self._balance[currency]= amount

    def get_balance(self, currency):
        return self._balance[currency]

    def get_price(self, currency, somethingBool):
        return self._price[currency]

    def get_all_balances(self):
        return f"{self._base_currency}: {self._balance[self._base_currency]}\n" f"{self._quote_currency}: {self._balance[self._quote_currency]}\n"

    def add_listener(self, event_tag, listener):
        self._listener[event_tag] = listener

    def remove_listener(self, event_tag, listener):
        self._listener.pop(event_tag)
    
    def buy(self, trading_pair, amount, order_type, kwargs):
        raise("Implementation pending")

    def sell(self, trading_pair, amount, order_type, kwargs):
        raise("Implementation pending")

    def cancel(trading_pair, order_id):
        raise("Implementation pending")

    def stop(self, current_tick):
        raise("Implementation pending")

    def start(self, current_tick):
        raise("Implementation pending")

    def tick(self, current_tick):
        raise("Implementation pending")