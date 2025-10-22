"""TradeFactory - SpotTrade 생성 전담 팩토리."""

from __future__ import annotations
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.trade import SpotTrade, SpotSide
    from .calculation_tool import CalculationTool


class TradeFactory:
    """
    SpotTrade 생성 전담 팩토리.
    책임: Trade/Fill ID 생성, Token 생성, 수수료 자동 계산.
    """

    def create_spot_trade(
        self,
        order: SpotOrder,
        side: SpotSide,
        fill_amount: float,
        fill_price: float,
        fill_index: int,
        timestamp: int,
    ) -> SpotTrade:
        """단일 SpotTrade 생성 (수수료 자동 계산)."""
        from financial_assets.trade import SpotTrade
        from financial_assets.pair import Pair
        from financial_assets.token import Token

        # 거래 금액 계산
        trade_value = fill_price * fill_amount

        # 수수료 계산 (quote currency 기준)
        fee_token = None
        if order.fee_rate > 0:
            fee_amount = trade_value * order.fee_rate
            fee_token = Token(order.stock_address.quote.upper(), fee_amount)

        return SpotTrade(
            stock_address=order.stock_address,
            trade_id=f"{order.order_id}-fill",
            fill_id=f"{order.order_id}-fill-{fill_index}",
            side=side,
            pair=Pair(
                asset=Token(order.stock_address.base.upper(), fill_amount),
                value=Token(order.stock_address.quote.upper(), trade_value),
            ),
            timestamp=timestamp,
            fee=fee_token,
        )

    def create_spot_trades_from_amounts(
        self,
        order: SpotOrder,
        side: SpotSide,
        amounts: List[float],
        fill_price: float,
        timestamp: int,
    ) -> List[SpotTrade]:
        """분할 수량으로 여러 Trade 생성 (각각 수수료 계산)."""
        trades = []
        for idx, amount in enumerate(amounts, 1):
            trade = self.create_spot_trade(
                order, side, amount, fill_price, idx, timestamp
            )
            trades.append(trade)
        return trades

    def create_market_trades_with_slippage(
        self,
        calc_tool: CalculationTool,
        order: SpotOrder,
        side: SpotSide,
        amounts: List[float],
        price_min: float,
        price_max: float,
        price_mean: float,
        price_std: float,
        timestamp: int,
    ) -> List[SpotTrade]:
        """시장가 주문용 - 각 Trade마다 다른 가격 및 수수료 계산."""
        trades = []
        for idx, amount in enumerate(amounts, 1):
            # 각 Trade마다 가격 재샘플링
            sampled_price = calc_tool.get_price_sample(
                price_min, price_max, price_mean, price_std
            )
            trade = self.create_spot_trade(
                order, side, amount, sampled_price, idx, timestamp
            )
            trades.append(trade)
        return trades

    def __repr__(self) -> str:
        return "TradeFactory()"
