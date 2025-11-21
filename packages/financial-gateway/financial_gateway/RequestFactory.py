from uuid import uuid4
from typing import Optional, List
from simple_logger import init_logging

from financial_assets.stock_address import StockAddress
from financial_assets.symbol import Symbol
from financial_assets.order import SpotOrder
from financial_assets.constants import (
    OrderSide,
    OrderType,
    TimeInForce,
    SelfTradePreventionMode
)

from financial_gateway.structures.create_order import CreateOrderRequest
from financial_gateway.structures.cancel_order import CancelOrderRequest
from financial_gateway.structures.modify_or_replace_order import ModifyOrReplaceOrderRequest
from financial_gateway.structures.see_order import SeeOrderRequest
from financial_gateway.structures.see_open_orders import SeeOpenOrdersRequest
from financial_gateway.structures.see_holdings import SeeHoldingsRequest
from financial_gateway.structures.see_balance import SeeBalanceRequest
from financial_gateway.structures.see_available_markets import SeeAvailableMarketsRequest
from financial_gateway.structures.see_ticker import SeeTickerRequest
from financial_gateway.structures.see_orderbook import SeeOrderbookRequest
from financial_gateway.structures.see_trades import SeeTradesRequest
from financial_gateway.structures.see_candles import SeeCandlesRequest
from financial_gateway.structures.see_server_time import SeeServerTimeRequest


class RequestFactory:
    # Request 생성 통합 진입점

    @init_logging(level="INFO", log_params=True)
    def __init__(self, gateway_name: str):
        self.gateway_name = gateway_name

    def create_order(
        self,
        address: StockAddress,
        side: OrderSide,
        order_type: OrderType,
        asset_quantity: Optional[float] = None,
        price: Optional[float] = None,
        quote_quantity: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: Optional[TimeInForce] = None,
        post_only: bool = False,
        self_trade_prevention: Optional[SelfTradePreventionMode] = None,
        client_order_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> CreateOrderRequest:
        return CreateOrderRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            address=address,
            side=side,
            order_type=order_type,
            asset_quantity=asset_quantity,
            price=price,
            quote_quantity=quote_quantity,
            stop_price=stop_price,
            time_in_force=time_in_force,
            post_only=post_only,
            self_trade_prevention=self_trade_prevention,
            client_order_id=client_order_id
        )

    def cancel_order(
        self,
        order: SpotOrder,
        request_id: Optional[str] = None
    ) -> CancelOrderRequest:
        return CancelOrderRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            order=order
        )

    def modify_or_replace_order(
        self,
        original_order: SpotOrder,
        side: Optional[OrderSide] = None,
        order_type: Optional[OrderType] = None,
        asset_quantity: Optional[float] = None,
        price: Optional[float] = None,
        quote_quantity: Optional[float] = None,
        stop_price: Optional[float] = None,
        time_in_force: Optional[TimeInForce] = None,
        post_only: Optional[bool] = None,
        self_trade_prevention: Optional[SelfTradePreventionMode] = None,
        client_order_id: Optional[str] = None,
        request_id: Optional[str] = None
    ) -> ModifyOrReplaceOrderRequest:
        return ModifyOrReplaceOrderRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            original_order=original_order,
            side=side,
            order_type=order_type,
            asset_quantity=asset_quantity,
            price=price,
            quote_quantity=quote_quantity,
            stop_price=stop_price,
            time_in_force=time_in_force,
            post_only=post_only,
            self_trade_prevention=self_trade_prevention,
            client_order_id=client_order_id
        )

    def see_order(
        self,
        order: SpotOrder,
        request_id: Optional[str] = None
    ) -> SeeOrderRequest:
        return SeeOrderRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            order=order
        )

    def see_open_orders(
        self,
        address: Optional[StockAddress] = None,
        limit: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> SeeOpenOrdersRequest:
        return SeeOpenOrdersRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            address=address,
            limit=limit
        )

    def see_holdings(
        self,
        symbols: Optional[List[Symbol]] = None,
        request_id: Optional[str] = None
    ) -> SeeHoldingsRequest:
        return SeeHoldingsRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            symbols=symbols
        )

    def see_balance(
        self,
        currencies: Optional[List[str]] = None,
        request_id: Optional[str] = None
    ) -> SeeBalanceRequest:
        return SeeBalanceRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            currencies=currencies
        )

    def see_available_markets(
        self,
        limit: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> SeeAvailableMarketsRequest:
        return SeeAvailableMarketsRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            limit=limit
        )

    def see_ticker(
        self,
        address: StockAddress,
        request_id: Optional[str] = None
    ) -> SeeTickerRequest:
        return SeeTickerRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            address=address
        )

    def see_orderbook(
        self,
        address: StockAddress,
        limit: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> SeeOrderbookRequest:
        return SeeOrderbookRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            address=address,
            limit=limit
        )

    def see_trades(
        self,
        address: StockAddress,
        order: Optional[SpotOrder] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> SeeTradesRequest:
        return SeeTradesRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            address=address,
            order=order,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

    def see_candles(
        self,
        address: StockAddress,
        interval: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: Optional[int] = None,
        request_id: Optional[str] = None
    ) -> SeeCandlesRequest:
        return SeeCandlesRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name,
            address=address,
            interval=interval,
            start_time=start_time,
            end_time=end_time,
            limit=limit
        )

    def see_server_time(
        self,
        request_id: Optional[str] = None
    ) -> SeeServerTimeRequest:
        return SeeServerTimeRequest(
            request_id=request_id or str(uuid4()),
            gateway_name=self.gateway_name
        )
