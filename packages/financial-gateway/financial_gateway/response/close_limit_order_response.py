"""CloseLimitOrderResponse - 주문 취소 응답."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.order import SpotOrder

from .base_response import BaseResponse


@dataclass
class CloseLimitOrderResponse(BaseResponse):
    """주문 취소 요청에 대한 응답."""

    # 고유 상태 플래그
    is_order_not_found: bool = False
    is_already_filled: bool = False
    is_already_cancelled: bool = False

    # 결과 데이터
    cancelled_order: Optional[SpotOrder] = None
