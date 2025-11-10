# Trade 생성 서비스

from __future__ import annotations
from typing import TYPE_CHECKING, List
from simple_logger import func_logging

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.trade import SpotTrade
    from ...InternalStruct import TradeParams


class SpotTradeFactoryService:

    @func_logging(level="INFO")
    def create_trades(
        self,
        order: SpotOrder,
        params_list: List[TradeParams],
        timestamp: int,
    ) -> List[SpotTrade]:
        # TradeParams 리스트로부터 SpotTrade 리스트 생성
        from financial_assets.trade import SpotTrade
        from financial_assets.pair import Pair
        from financial_assets.token import Token

        trades = []
        for params in params_list:
            trade_value = params.fill_price * params.fill_amount

            fee_token = None
            if order.fee_rate > 0:
                fee_amount = trade_value * order.fee_rate
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
