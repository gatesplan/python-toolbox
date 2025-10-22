"""TradeSimulation - Order를 적절한 워커로 라우팅하는 코어 클래스."""

from __future__ import annotations
from typing import List
from simple_logger import init_logging, func_logging

from .spot_limit_buy import SpotLimitBuyWorker
from .spot_limit_sell import SpotLimitSellWorker
from .spot_market_buy import SpotMarketBuyWorker
from .spot_market_sell import SpotMarketSellWorker


class TradeSimulation:
    """
    거래 시뮬레이션 코어 클래스.

    Order의 타입(limit/market)과 side(buy/sell)를 검사하여
    적절한 워커로 라우팅합니다.
    """

    @init_logging(level="INFO")
    def __init__(self):
        """TradeSimulation 초기화 - 4개 워커 인스턴스 생성."""
        self._limit_buy_worker = SpotLimitBuyWorker()
        self._limit_sell_worker = SpotLimitSellWorker()
        self._market_buy_worker = SpotMarketBuyWorker()
        self._market_sell_worker = SpotMarketSellWorker()

    @func_logging(level="DEBUG")
    def process(self, order, price) -> List:
        """
        Order를 처리하여 Trade 리스트 반환.

        Args:
            order: Order 객체 (SpotOrder 등)
            price: Price 객체

        Returns:
            List[SpotTrade]: 체결된 거래 리스트

        Raises:
            ValueError: 파라미터 검증 실패 시
        """
        from financial_assets.trade import SpotSide

        # 파라미터 검증
        if not self._validate_process_param(order, price):
            raise ValueError("Invalid parameters")

        # 라우팅 로직
        order_type = order.order_type
        side = order.side

        if order_type == "limit":
            if side == SpotSide.BUY:
                return self._limit_buy_worker(order, price)
            elif side == SpotSide.SELL:
                return self._limit_sell_worker(order, price)
        elif order_type == "market":
            if side == SpotSide.BUY:
                return self._market_buy_worker(price)
            elif side == SpotSide.SELL:
                return self._market_sell_worker(price)

        raise ValueError(f"Unknown order_type or side: {order_type}, {side}")

    def _validate_process_param(self, order, price) -> bool:
        """
        파라미터 타입 검증.

        Args:
            order: Order 객체
            price: Price 객체

        Returns:
            bool: 검증 통과 여부
        """
        from financial_assets.price import Price

        # Price 타입 검증
        if not isinstance(price, Price):
            return False

        # Order 기본 속성 검증
        if not hasattr(order, 'order_type') or not hasattr(order, 'side'):
            return False

        return True

    def __repr__(self) -> str:
        return "TradeSimulation(workers=4)"
