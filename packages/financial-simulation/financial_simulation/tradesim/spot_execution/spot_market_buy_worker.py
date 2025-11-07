"""SpotMarketBuyWorker - 시장가 매수 체결 시뮬레이션."""

from __future__ import annotations
from typing import TYPE_CHECKING, List
import random
from simple_logger import func_logging

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.price import Price
    from ..trade_params import TradeParams

from ..calculation_tool import CalculationTool


class SpotMarketBuyWorker:
    """시장가 매수 주문 워커.

    특징:
    - 항상 체결됨
    - 슬리피지 반영: head 범위(bodytop ~ h)에서 불리한 가격으로 체결
    - 1~3개로 분할 체결 (각 조각마다 다른 가격)
    """

    @func_logging(level="DEBUG")
    def __call__(
        self,
        order: SpotOrder,
        price: Price,
    ) -> List[TradeParams]:
        """시장가 매수 체결 파라미터 생성.

        Args:
            order: 체결할 주문
            price: 현재 시장 가격

        Returns:
            체결 파라미터 리스트 (1~3개)
        """
        from ..trade_params import TradeParams

        # 슬리피지 범위: head (bodytop ~ h)
        head_min = price.bodytop()
        head_max = price.h
        head_mean = (head_min + head_max) / 2
        head_std = (head_max - head_min) / 4  # 95% 범위를 커버

        # 분할 개수: 1~3개
        split_count = random.randint(1, 3)

        # 총 수량 분할
        total_amount = order.remaining_asset()
        min_trade_amount = order.min_trade_amount or (total_amount * 0.01)

        amounts = CalculationTool.get_separated_amount_sequence(
            total_amount, min_trade_amount, split_count
        )

        # 각 조각마다 파라미터 생성 (가격은 개별 샘플링)
        params_list = []
        for idx, amount in enumerate(amounts, 1):
            sampled_price = CalculationTool.get_price_sample(
                head_min, head_max, head_mean, head_std
            )
            params_list.append(
                TradeParams(
                    fill_amount=amount,
                    fill_price=sampled_price,
                    fill_index=idx,
                )
            )

        return params_list
