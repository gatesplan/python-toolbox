"""TradeFactoryDirector - Factory 조율 및 Trade 생성 전담."""

from __future__ import annotations
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.trade import SpotTrade
    from ..trade_params import TradeParams

from .spot_trade_factory import SpotTradeFactory


class TradeFactoryDirector:
    """Factory 관리 전담 Director.

    책임:
    - Spot/Futures Factory 소유 및 관리
    - 체결 파라미터를 Trade 객체로 변환
    """

    def __init__(self):
        """Factory 인스턴스 생성."""
        self._spot_factory = SpotTradeFactory()
        # self._futures_factory = FuturesTradeFactory()  # 미구현

    def create_spot_trades(
        self,
        order: SpotOrder,
        params_list: List[TradeParams],
        timestamp: int,
    ) -> List[SpotTrade]:
        """SpotTrade 리스트 생성.

        Args:
            order: 원본 주문 객체
            params_list: Worker가 생성한 체결 파라미터 리스트
            timestamp: 체결 시각

        Returns:
            생성된 SpotTrade 리스트
        """
        trades = []
        for params in params_list:
            trade = self._spot_factory.create_spot_trade(order, params, timestamp)
            trades.append(trade)
        return trades

    # def create_futures_trades(
    #     self,
    #     order: FuturesOrder,
    #     params_list: List[TradeParams],
    #     timestamp: int,
    # ) -> List[FuturesTrade]:
    #     """FuturesTrade 리스트 생성 (미구현)."""
    #     pass
