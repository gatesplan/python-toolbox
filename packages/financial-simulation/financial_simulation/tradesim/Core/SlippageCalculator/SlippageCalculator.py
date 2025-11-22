# 슬리피지 범위 계산

from __future__ import annotations
from typing import TYPE_CHECKING
from simple_logger import func_logging

if TYPE_CHECKING:
    from financial_assets.constants import OrderSide


class SlippageCalculator:

    @staticmethod
    @func_logging(level="DEBUG")
    def calculate_range(price, side: OrderSide) -> tuple[float, float]:
        # 주문 방향에 따른 슬리피지 범위 계산 (side.value: "buy" or "sell")
        side_value = side.value

        if side_value == "buy":
            return price.bodytop(), price.h
        elif side_value == "sell":
            return price.l, price.bodybottom()
        else:
            raise ValueError(f"Unknown side: {side}")
