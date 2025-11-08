"""SpotLimitWorker - 지정가 주문 체결 시뮬레이션."""

from __future__ import annotations
from typing import TYPE_CHECKING, List
import random
from simple_logger import func_logging

if TYPE_CHECKING:
    from financial_assets.order import SpotOrder
    from financial_assets.price import Price
    from ..trade_params import TradeParams

from ..calculation_tool import CalculationTool


class SpotLimitWorker:
    """지정가 주문 체결 워커 (BUY/SELL 통합).

    체결 조건:
    - 매수(BUY): 시장 가격(close) <= 주문 가격
    - 매도(SELL): 시장 가격(close) >= 주문 가격

    체결 확률:
    - body 범위: 100% 전량 체결
    - head/tail 범위: 30% 실패, 30% 전량, 40% 부분 체결 (1~3개)
    - none: 체결 없음
    """

    @func_logging(level="DEBUG")
    def __call__(
        self,
        order: SpotOrder,
        price: Price,
    ) -> List[TradeParams]:
        """지정가 주문 체결 파라미터 생성.

        Args:
            order: 체결할 주문
            price: 현재 시장 가격

        Returns:
            체결 파라미터 리스트 (빈 리스트 가능)
        """
        from financial_assets.constants import Side

        params_list = []

        # 가격 범위 판단
        price_range = CalculationTool.get_price_range(price, order.price)

        # Body 범위: 100% 전량 체결
        if price_range == "body":
            from ..trade_params import TradeParams

            params_list.append(
                TradeParams(
                    fill_amount=order.remaining_asset(),
                    fill_price=order.price,
                    fill_index=1,
                )
            )

        # Head/Tail 범위: 확률적 체결 (30% 실패, 30% 전량, 40% 부분)
        elif price_range in ("head", "tail"):
            rand = random.random()

            if rand < 0.3:
                # 30%: 체결 실패
                pass
            elif rand < 0.6:
                # 30%: 전량 체결
                from ..trade_params import TradeParams

                params_list.append(
                    TradeParams(
                        fill_amount=order.remaining_asset(),
                        fill_price=order.price,
                        fill_index=1,
                    )
                )
            else:
                # 40%: 부분 체결 (1~3개)
                from ..trade_params import TradeParams

                total_amount = order.remaining_asset()
                min_trade_amount = order.min_trade_amount or (total_amount * 0.01)
                split_count = random.randint(1, 3)

                amounts = CalculationTool.get_separated_amount_sequence(
                    total_amount, min_trade_amount, split_count
                )

                for idx, amount in enumerate(amounts, 1):
                    params_list.append(
                        TradeParams(
                            fill_amount=amount,
                            fill_price=order.price,
                            fill_index=idx,
                        )
                    )

        return params_list
