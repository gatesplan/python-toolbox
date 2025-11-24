# Trade 생성 서비스

from __future__ import annotations
from typing import TYPE_CHECKING, List

from simple_logger import init_logging, func_logging
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_assets.constants import OrderType

if TYPE_CHECKING:
    from ...InternalStruct import TradeParams


class SpotTradeFactoryService:

    @init_logging(level="INFO")
    def __init__(self, maker_fee_ratio: float, taker_fee_ratio: float):
        # 거래소 수수료 정책 저장
        self._maker_fee_ratio = maker_fee_ratio
        self._taker_fee_ratio = taker_fee_ratio

    @func_logging(level="INFO")
    def create_trades(
        self,
        order: SpotOrder,
        params_list: List[TradeParams],
        timestamp: int,
    ) -> List[SpotTrade]:
        # TradeParams 리스트로부터 SpotTrade 리스트 생성
        # 주문 타입에 따라 적절한 수수료 비율 선택
        fee_ratio = self._maker_fee_ratio if order.order_type == OrderType.LIMIT else self._taker_fee_ratio

        trades = []
        for params in params_list:
            trade_value = params.fill_price * params.fill_amount

            fee_token = None
            if fee_ratio > 0:
                fee_amount = trade_value * fee_ratio
                fee_token = Token(order.stock_address.quote.upper(), fee_amount)

            trade_id = f"{order.order_id}-fill-{params.fill_index}"

            trade = SpotTrade(
                trade_id=trade_id,
                order=order,
                pair=Pair(
                    asset=Token(order.stock_address.base.upper(), params.fill_amount),
                    value=Token(order.stock_address.quote.upper(), trade_value),
                ),
                timestamp=timestamp,
                fee=fee_token,
            )
            trades.append(trade)

        return trades
