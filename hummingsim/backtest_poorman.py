#!/usr/bin/env python
import faulthandler; faulthandler.enable()
import sys
import os; sys.path.insert(0, os.path.realpath(os.path.join(__file__, "../../")))
import logging; logging.basicConfig(level=logging.INFO)
import pandas as pd
import hummingsim
from typing import (
    List,
    Tuple,
)

from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.strategy.pure_market_making import (
    PureMarketMakingStrategy,
    OrderBookAssetPriceDelegate,
    APIAssetPriceDelegate,
    InventoryCostPriceDelegate,
)
from hummingbot.strategy.pure_market_making.pure_market_making_config_map import pure_market_making_config_map as c_map
from hummingbot.connector.exchange.paper_trade import create_paper_trade_market
from hummingbot.core.clock import (
    Clock,
    ClockMode
)

from hummingsim.backtest.market import (
    BacktestMarket,
    QuantizationParams
)

from hummingsim.config_loader import ConfigLoader

# Define the data cache path.
data_path = os.path.join(os.environ["PWD"], "data")

#Define strategy path
strategy_yml_path = os.path.join(os.environ['PWD'], "conf", "backtest_strategy.yml")

# Define the parameters for the backtest.
start = pd.Timestamp("2018-12-21-00:29:06", tz="UTC")
end = pd.Timestamp("2019-12-24-00:43:00", tz="UTC")
backtest_trading_pair = ("ETHUSDT", "ETH", "USDT")

backtest_market = BacktestMarket()


backtest_market.config(backtest_trading_pair[1], 0.001, backtest_trading_pair[2], 0.001,{})

backtest_market.add_data(data_path)

backtest_market.set_quantization_param(QuantizationParams("ETHUSDT", 5, 3, 5, 3))

configLoader = ConfigLoader(strategy_yml_path)

strategy = configLoader.start()

clock = Clock(ClockMode.BACKTEST, start_time=start.timestamp(), end_time=end.timestamp())
clock.add_iterator(backtest_market)
clock.add_iterator(strategy)


backtest_market.set_balance("ETH", 100.0)
backtest_market.set_balance("USDT", 10000.0)

clock.backtest_til(start.timestamp() + 1)
backtest_eth_price = backtest_market.get_price("ETHUSDT", False)
start_backtest_portfolio_value = backtest_market.get_balance("USDT") + backtest_market.get_balance("ETH") * backtest_eth_price
print(f"start Backtest portfolio value: {start_backtest_portfolio_value}")

clock.backtest_til(end.timestamp())

backtest_eth_price = backtest_market.get_price("ETHUSDT", False)
backtest_portfolio_value = backtest_market.get_balance("USDT") + backtest_market.get_balance("ETH") * backtest_eth_price
print(f"Backtest portfolio value: {backtest_portfolio_value}\n")
print(f"Backtest balances: {backtest_market.get_all_balances()}")

print("start Backtest portfolio value: {start_backtest_portfolio_value}")

print(f"Profit Backtest {backtest_portfolio_value/start_backtest_portfolio_value}\n")
