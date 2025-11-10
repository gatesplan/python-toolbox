# 시장가 매수 체결 서비스

from __future__ import annotations
from typing import TYPE_CHECKING, List
import random
from simple_logger import func_logging

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.price import Price

from ...InternalStruct import TradeParams
from ...Constants import SplitConfig
from ...Core import PriceSampler, AmountSplitter, SlippageCalculator


class SpotMarketBuyFillService:

    @func_logging(level="INFO")
    def execute(
        self,
        order: SpotOrder,
        price: Price,
    ) -> List[TradeParams]:
        # 시장가 매수 체결 파라미터 생성
        if not order.min_trade_amount or order.min_trade_amount <= 0:
            raise ValueError(
                f"Order must have valid min_trade_amount: {order.min_trade_amount}"
            )

        from financial_assets.constants import Side

        slippage_min, slippage_max = SlippageCalculator.calculate_range(
            price, Side.BUY
        )

        mean, std = PriceSampler.calculate_normal_params(
            slippage_min, slippage_max, SplitConfig.STD_CALCULATION_FACTOR
        )

        split_count = random.randint(
            SplitConfig.MIN_SPLIT_COUNT,
            SplitConfig.MAX_SPLIT_COUNT
        )

        total_amount = order.remaining_asset()
        amounts = AmountSplitter.split_with_dirichlet(
            total_amount, order.min_trade_amount, split_count
        )

        params_list = []
        for idx, amount in enumerate(amounts, 1):
            sampled_price = PriceSampler.sample_from_normal(
                slippage_min, slippage_max, mean, std
            )
            params_list.append(
                TradeParams(
                    fill_amount=amount,
                    fill_price=sampled_price,
                    fill_index=idx,
                )
            )

        return params_list
