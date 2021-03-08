from decimal import Decimal
import pandas as pd
import threading
import asyncio
import time
from typing import (
    TYPE_CHECKING,
    List,
)
from datetime import datetime
from datetime import timezone
from hummingbot.core.utils.async_utils import safe_ensure_future
from hummingbot.core.data_type.common import OpenOrder
from hummingbot.core.utils.market_price import usd_value
from hummingbot.user.user_balances import UserBalances
from hummingbot.strategy.market_trading_pair_tuple import MarketTradingPairTuple
from hummingbot.connector.derivative.binance_perpetual.binance_perpetual_derivative import get_client_order_id
from hummingbot.connector.derivative.binance_perpetual.binance_perpetual_api_order_book_data_source import \
    BinancePerpetualAPIOrderBookDataSource
from hummingbot.client.config.global_config_map import global_config_map
#review
from hummingbot.core.event.events import (
    OrderType,
    TradeType,
    MarketOrderFailureEvent,
    MarketEvent,
    OrderCancelledEvent,
    BuyOrderCompletedEvent,
    BuyOrderCreatedEvent,
    SellOrderCreatedEvent,
    OrderFilledEvent,
    SellOrderCompletedEvent, PositionSide, PositionMode, PositionAction)
NaN = float("nan")
s_decimal_nan = Decimal("NaN")
s_decimal_0 = Decimal("0")
s_float_0 = float(0)
s_decimal_0 = Decimal("0")

if TYPE_CHECKING:
    from hummingbot.client.hummingbot_application import HummingbotApplication

OPTIONS = [
    "leverage",
    "long",
    "short",
    "help"
]

class MacroCommand:
    def macro(self,  # type: HummingbotApplication
            option: str = None,
                args: List[str] = None
                ):
        if option is None:
            return
        if threading.current_thread() != threading.main_thread():
            self.ev_loop.call_soon_threadsafe(self.macro, option, args) # FIXME: add option to cancel open trades.
            return
        # if threading.current_thread() != threading.main_thread():
        if option in ["long","short"]:
            safe_ensure_future(self.open_position(option, args)) # FIXME: add option to cancel open trades.
        elif option == "leverage":
            safe_ensure_future(self.macro_set_leverage( args)) # FIXME: add option to cancel open trades.
        elif option == "help":
            self._notify(f"macro leverage <new_leverage value>")
            self._notify(f"macro long [amount] [price]")
            self._notify(f"macro short [amount] [price]")
            self._notify(f"macro help")
        

    async def macro_set_leverage(self,  # type: HummingbotApplication
                                 args: List[str] = None):
        if args is not  None and len(args) == 1:
             leverage = args[0]
        else:
            return
        # Fixme: in the future add command get so we can retrieve individual key values from the config.
        data = dict()
        if self.strategy_name is not None:
            for cv in self.strategy_config_map.values():
                if not cv.is_secure:
                    data[cv.key] = cv.value
        else:
            self._notify("This command supports only binance and perpetual_market_making strategy (for now), please first connect to binance and import/create a perpetual_market_making strategy instance.")
            return
        if self.strategy_name != "perpetual_market_making": 
            self._notify("This command supports only binance and perpetual_market_making strategy (for now), please first connect to binance and import/create a perpetual_market_making strategy instance.")
            return
        
        exchange = "binance_perpetual" # FIXME: add support for papertrade
        trading_pair = data["market"]
        base, quote = trading_pair.split("-")
        market = self.markets[exchange]
        try:
            market.set_margin(trading_pair,leverage)
        except Exception as e:
            self._notify(f"Careful, got error setting Leverage, it may be a false alarm if the leverage was already x{leverage}")
            self._notify(e)

    async def open_position(self,  # type: HummingbotApplication
                                option: str = None,
                                 args: List[str] = None):
        if option == "long":
            trade_type = TradeType.BUY
        else:
            trade_type = TradeType.SELL # short

        # Fixme: in the future add command get so we can retrieve individual key values from the config.
        data = dict()
        if self.strategy_name is not None:
            for cv in self.strategy_config_map.values():
                if not cv.is_secure:
                    data[cv.key] = cv.value
        else:
            self._notify("This command supports only binance and perpetual_market_making strategy (for now), please first connect to binance and import/create a perpetual_market_making strategy instance.")
            return
        if self.strategy_name != "perpetual_market_making": 
            self._notify("This command supports only binance and perpetual_market_making strategy (for now), please first connect to binance and import/create a perpetual_market_making strategy instance.")
            return
        
        exchange = "binance_perpetual" # FIXME: add support for papertrade
        #all_ex_bals = UserBalances.instance()._balances
        #all_ex_avai_bals = UserBalances.instance()._avai_balances
        self._notify("Updating balances, please wait...")
        all_ex_bals = await UserBalances.instance().all_balances_all_exchanges()
        all_ex_avai_bals = UserBalances.instance().all_avai_balances_all_exchanges()
        if all_ex_bals is None or all_ex_avai_bals is None:
            self._notify("No cache data from exchanges, can't place order.")
            return
        if exchange not in all_ex_bals.keys() or exchange not in all_ex_avai_bals.keys():
            self._notify(f"No balance data for exchange {exchange}, can't place order.")
            return

        all_ex_limits: Optional[Dict[str, Dict[str, str]]] = global_config_map["balance_asset_limit"].value

        
        trading_pair = data["market"]
        base, quote = trading_pair.split("-")
        
        quote_balance = all_ex_avai_bals[exchange][quote]
        
        # if args is None or len(args) < 3:
        #     sensitivity =  data["order_amount_prc"] if data["order_amount_prc"] > 0 else data["order_amount"]
        # else:
        #     sensitivity = Decimal(args[3]) / Decimal("100")
        if args is None or len(args) < 2:
            base_price = BinancePerpetualAPIOrderBookDataSource.get_mid_price(trading_pair,exchange) # FIXME: may be we should use: top bid 
        else:
            base_price = Decimal(args[1])
        
        if args is None or len(args) < 1:
            amount = (data["order_amount"] * data["order_amount_prc"]) if data["order_amount_prc"] > 0 else data["order_amount"]
        else:
            amount = min(Decimal(args[0]), quote_balance / base_price)
       
        
        market = self.markets[exchange]
        # try:
        #     market.set_margin(trading_pair,leverage)
        # except Exception as e:
        #     self._notify(f"Careful, got error setting Leverage, it may be a false alarm if the leverage was already x{leverage}")
        #     self._notify(e)
        # await asyncio.sleep(0.5)
        # while market.get_margin() != leverage:
        #     await asyncio.sleep(0.5)
        #     self._notify("Waiting to set leverage")
        
        price = base_price
        order_type = OrderType.LIMIT_MAKER # FIXME: ?
        position_action = PositionAction.OPEN
        #position_side = PositionSide.LONG
        #position_mode = PositionMode.HEDGE
        #size_usd = await usd_value(base, amount)
        order_id = get_client_order_id("LONG",trading_pair)
        self._notify(f"\nOpening {option} order:")
        lines = list()
        lines.append("    " + f"Order ID: {order_id}")
        lines.append("    " + f"Trading_pair: {trading_pair}")
        lines.append("    " + f"Amount: {amount}") # FIXME: get these values from result.
        lines.append("    " + f"Price: {price}")
        #lines.append("    " + f"Leverage: x{leverage}")
        
        self._notify("\n".join(lines))
        order_result = await market.create_order(
                            trade_type,
                            order_id,
                            trading_pair,
                            amount,
                            order_type,
                            position_action,
                            price)
        #expiration_seconds = s_decimal_nan
        #base, quote = trading_pair.split("-")
        

        #market_info = MarketTradingPairTuple(self.markets[exchange], trading_pair, base, quote)
        # order_id = self.strategy.buy_with_specific_market(
        #             market_info,
        #             amount,
        #             order_type=order_type,
        #             price=price,
        #             expiration_seconds=expiration_seconds,
        #             position_action=position_action
        #         )
        
        if order_result is not None:
            exchange_order_id = str(order_result["orderId"])
            self._notify(f"\nOrder ID: {exchange_order_id} successfully opened")
            
            self._notify("\n".join(lines))
        else:
            self._notify("\nCould not open {option} order.")
        
