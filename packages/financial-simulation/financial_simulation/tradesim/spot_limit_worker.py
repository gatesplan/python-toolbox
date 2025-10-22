"""Spot Limit Worker - 지정가 주문 워커 (BUY/SELL 통합)."""

from __future__ import annotations
from typing import TYPE_CHECKING, List
import random
from simple_logger import func_logging

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.price import Price
    from financial_assets.trade import SpotTrade
    from .calculation_tool import CalculationTool
    from .trade_factory import TradeFactory


class SpotLimitWorker:
    """
    지정가 주문 워커 (BUY/SELL 통합).
    매수: 시장 가격이 주문 가격 이하일 때 체결, 매도: 시장 가격이 주문 가격 이상일 때 체결.
    """

    @func_logging(level="DEBUG")
    def __call__(
        self,
        calc_tool: CalculationTool,
        trade_factory: TradeFactory,
        order: SpotOrder,
        price: Price,
    ) -> List[SpotTrade]:
        """지정가 주문 체결."""
        from financial_assets.trade import SpotSide

        trades = []
        side = order.side

        # 체결 조건 확인 (side에 따라 분기)
        if side == SpotSide.BUY:
            # 매수: 시장 가격(close) <= 주문 가격
            if price.c > order.price:
                return trades
        else:  # SpotSide.SELL
            # 매도: 시장 가격(close) >= 주문 가격
            if price.c < order.price:
                return trades

        # 가격 범위 판단
        price_range = calc_tool.get_price_range(price, order.price)

        # Body 범위: 100% 전량 체결
        if price_range == "body":
            trade = trade_factory.create_spot_trade(
                order,
                side,
                order.remaining_asset(),
                order.price,
                1,
                price.t,
            )
            trades.append(trade)

        # Head/Tail 범위: 확률적 체결 (30% 실패, 30% 전량, 40% 부분)
        elif price_range in ("head", "tail"):
            rand = random.random()

            if rand < 0.3:
                # 30%: 체결 실패
                pass
            elif rand < 0.6:
                # 30%: 전량 체결
                trade = trade_factory.create_spot_trade(
                    order,
                    side,
                    order.remaining_asset(),
                    order.price,
                    1,
                    price.t,
                )
                trades.append(trade)
            else:
                # 40%: 부분 체결 (1~3개 Trade)
                total_amount = order.remaining_asset()

                # min_trade_amount: order에서 가져오거나 기본값 사용
                min_trade_amount = order.min_trade_amount or (total_amount * 0.01)

                split_count = random.randint(1, 3)
                amounts = calc_tool.get_separated_amount_sequence(
                    total_amount, min_trade_amount, split_count
                )

                trades = trade_factory.create_spot_trades_from_amounts(
                    order, side, amounts, order.price, price.t
                )

        return trades
