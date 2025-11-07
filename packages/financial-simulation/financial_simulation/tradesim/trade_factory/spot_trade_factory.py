"""SpotTradeFactory - SpotTrade 생성 전담."""

from __future__ import annotations
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.trade import SpotTrade
    from ..trade_params import TradeParams


class SpotTradeFactory:
    """SpotTrade 생성 전담 팩토리.

    책임:
    - Trade ID 생성
    - Pair 구성 (asset, value Token)
    - 수수료 계산 (quote currency 기준)
    - Order 객체 연결
    """

    def create_spot_trade(
        self,
        order: SpotOrder,
        params: TradeParams,
        timestamp: int,
    ) -> SpotTrade:
        """단일 SpotTrade 생성.

        Args:
            order: 원본 주문 객체
            params: 체결 파라미터 (fill_amount, fill_price, fill_index)
            timestamp: 체결 시각

        Returns:
            생성된 SpotTrade 객체
        """
        from financial_assets.trade import SpotTrade
        from financial_assets.pair import Pair
        from financial_assets.token import Token

        # 거래 금액 계산
        trade_value = params.fill_price * params.fill_amount

        # 수수료 계산 (quote currency 기준)
        fee_token = None
        if order.fee_rate > 0:
            fee_amount = trade_value * order.fee_rate
            fee_token = Token(order.stock_address.quote.upper(), fee_amount)

        # Trade ID 생성: {order_id}-fill-{fill_index}
        trade_id = f"{order.order_id}-fill-{params.fill_index}"

        return SpotTrade(
            trade_id=trade_id,
            order=order,
            pair=Pair(
                asset=Token(order.stock_address.base.upper(), params.fill_amount),
                value=Token(order.stock_address.quote.upper(), trade_value),
            ),
            timestamp=timestamp,
            fee=fee_token,
        )
