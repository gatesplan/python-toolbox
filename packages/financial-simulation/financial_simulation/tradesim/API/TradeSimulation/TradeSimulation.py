# 거래 시뮬레이션 API (진입점)

from __future__ import annotations
from typing import List

from simple_logger import init_logging, func_logging
from financial_assets.order import Order, SpotOrder
from financial_assets.price import Price
from financial_assets.trade import Trade
from financial_assets.constants import OrderType, OrderSide

from ...Service import (
    SpotLimitFillService,
    SpotMarketBuyFillService,
    SpotMarketSellFillService,
    SpotTradeFactoryService,
)


class TradeSimulation:

    @init_logging(level="INFO")
    def __init__(self, maker_fee_ratio: float, taker_fee_ratio: float):
        # 수수료 비율 저장
        self._maker_fee_ratio = maker_fee_ratio
        self._taker_fee_ratio = taker_fee_ratio

        # Service 인스턴스 생성
        self._limit_fill_service = SpotLimitFillService()
        self._market_buy_fill_service = SpotMarketBuyFillService()
        self._market_sell_fill_service = SpotMarketSellFillService()
        self._trade_factory_service = SpotTradeFactoryService(
            maker_fee_ratio=maker_fee_ratio,
            taker_fee_ratio=taker_fee_ratio
        )

    @func_logging(level="INFO")
    def process(
        self,
        order: Order,
        price: Price,
    ) -> List[Trade]:
        # 주문 체결 시뮬레이션 실행
        if isinstance(order, SpotOrder):
            # 1. 적절한 FillService 선택 및 호출
            if order.order_type == OrderType.LIMIT:
                params_list = self._limit_fill_service.execute(order, price)
            elif order.order_type == OrderType.MARKET:
                if order.side == OrderSide.BUY:
                    params_list = self._market_buy_fill_service.execute(order, price)
                elif order.side == OrderSide.SELL:
                    params_list = self._market_sell_fill_service.execute(order, price)
                else:
                    raise ValueError(f"Unknown side: {order.side}")
            else:
                raise ValueError(f"Unknown order_type: {order.order_type}")

            # 2. TradeFactoryService 호출하여 Trade 생성
            trades = self._trade_factory_service.create_trades(
                order, params_list, price.t
            )

            return trades

        raise ValueError(f"Unknown order type: {type(order)}")
