"""Spot Market Sell Worker - 시장가 매도 워커."""

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


class SpotMarketSellWorker:
    """
    시장가 매도 주문 워커.
    항상 체결되며 슬리피지를 반영합니다 (tail 범위 내 불리한 가격).
    """

    @func_logging(level="DEBUG")
    def __call__(
        self,
        calc_tool: CalculationTool,
        trade_factory: TradeFactory,
        order: SpotOrder,
        price: Price,
    ) -> List[SpotTrade]:
        """시장가 매도 체결."""
        from financial_assets.trade import SpotSide

        # 슬리피지 범위: tail (l ~ bodybottom)
        tail_min = price.l
        tail_max = price.bodybottom()
        tail_mean = (tail_min + tail_max) / 2
        tail_std = (tail_max - tail_min) / 4  # 95% 범위를 커버

        # 분할 개수: 1~3개
        split_count = random.randint(1, 3)

        # 총 수량 분할
        total_amount = order.remaining_asset()

        # min_trade_amount: order에서 가져오거나 기본값 사용
        min_trade_amount = order.min_trade_amount or (total_amount * 0.01)

        amounts = calc_tool.get_separated_amount_sequence(
            total_amount, min_trade_amount, split_count
        )

        # 각 조각마다 Trade 생성 (가격은 개별 샘플링)
        trades = trade_factory.create_market_trades_with_slippage(
            calc_tool,
            order,
            SpotSide.SELL,
            amounts,
            tail_min,
            tail_max,
            tail_mean,
            tail_std,
            price.t,
        )

        return trades
