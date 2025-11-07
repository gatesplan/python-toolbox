"""TradeSimulation - 거래 시뮬레이션 Service."""

from __future__ import annotations
from typing import TYPE_CHECKING, List
from simple_logger import init_logging, func_logging

if TYPE_CHECKING:
    from financial_assets.order import Order, SpotOrder
    from financial_assets.price import Price
    from financial_assets.trade import Trade

from .spot_execution import SpotExecutionDirector
from .trade_factory import TradeFactoryDirector


class TradeSimulation:
    """거래 시뮬레이션 Service.

    책임:
    - 외부 인터페이스 제공
    - 모든 Director 조율 (Director 간 의존성 없음)
    - ExecutionDirector → 파라미터 획득
    - FactoryDirector → Trade 생성

    Stateless 설계:
    - 내부 상태 없음
    - 입력(Order, Price)만으로 출력(Trade 리스트) 생성
    """

    @init_logging(level="INFO")
    def __init__(self):
        """Director 인스턴스 생성."""
        self._factory_director = TradeFactoryDirector()
        self._spot_director = SpotExecutionDirector()
        # self._futures_director = FuturesExecutionDirector()  # 미구현

    @func_logging(level="DEBUG")
    def process(
        self,
        order: Order,
        price: Price,
    ) -> List[Trade]:
        """주문 체결 시뮬레이션 실행.

        Args:
            order: 체결할 주문 객체 (SpotOrder 또는 FuturesOrder)
            price: 현재 시장 가격 (OHLCV)

        Returns:
            체결된 Trade 목록 (빈 리스트 가능)

        Raises:
            ValueError: 알 수 없는 Order 타입
        """
        from financial_assets.order import SpotOrder

        # Order 타입 확인 및 라우팅
        if isinstance(order, SpotOrder):
            # 1. ExecutionDirector에서 체결 파라미터 획득
            params_list = self._spot_director.execute(order, price)

            # 2. FactoryDirector에서 Trade 생성
            trades = self._factory_director.create_spot_trades(
                order, params_list, price.t
            )

            return trades

        # elif isinstance(order, FuturesOrder):
        #     params_list = self._futures_director.execute(order, price)
        #     trades = self._factory_director.create_futures_trades(
        #         order, params_list, price.t
        #     )
        #     return trades

        raise ValueError(f"Unknown order type: {type(order)}")
