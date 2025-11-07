"""SpotExecutionDirector - Spot 주문 체결 조율."""

from __future__ import annotations
from typing import TYPE_CHECKING, List
from simple_logger import init_logging, func_logging

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.price import Price
    from ..trade_params import TradeParams

from .spot_limit_worker import SpotLimitWorker
from .spot_market_buy_worker import SpotMarketBuyWorker
from .spot_market_sell_worker import SpotMarketSellWorker


class SpotExecutionDirector:
    """Spot 주문 전담 Director.

    책임:
    - Order 타입/Side에 따라 Worker 라우팅
    - Worker 결과 수집
    - 체결 파라미터 리스트 반환
    """

    @init_logging(level="INFO")
    def __init__(self):
        """Worker 인스턴스 생성."""
        self._limit_worker = SpotLimitWorker()
        self._market_buy_worker = SpotMarketBuyWorker()
        self._market_sell_worker = SpotMarketSellWorker()

    @func_logging(level="DEBUG")
    def execute(
        self,
        order: SpotOrder,
        price: Price,
    ) -> List[TradeParams]:
        """Spot 주문 체결 파라미터 생성.

        Args:
            order: 체결할 Spot 주문
            price: 현재 시장 가격

        Returns:
            체결 파라미터 리스트 (빈 리스트 가능)

        Raises:
            ValueError: 파라미터 검증 실패 또는 알 수 없는 order_type/side
        """
        from financial_assets.constants import Side, OrderType

        # 파라미터 검증
        if not self._validate_params(order, price):
            raise ValueError("Invalid parameters")

        # 라우팅 로직
        order_type = order.order_type
        side = order.side

        if order_type == OrderType.LIMIT:
            return self._limit_worker(order, price)
        elif order_type == OrderType.MARKET:
            if side == Side.BUY:
                return self._market_buy_worker(order, price)
            elif side == Side.SELL:
                return self._market_sell_worker(order, price)

        raise ValueError(f"Unknown order_type or side: {order_type}, {side}")

    def _validate_params(self, order: SpotOrder, price) -> bool:
        """파라미터 타입 검증.

        Args:
            order: 주문 객체
            price: 가격 객체

        Returns:
            검증 통과 여부
        """
        from financial_assets.price import Price

        # Price 타입 검증
        if not isinstance(price, Price):
            return False

        # Order 기본 속성 검증
        if not hasattr(order, "order_type") or not hasattr(order, "side"):
            return False

        return True
