"""OrderCurrentStateResponse - 주문 상태 조회 응답."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.order import SpotOrder

from .base_response import BaseResponse


@dataclass
class OrderCurrentStateResponse(BaseResponse):
    """주문 상태 조회 요청에 대한 응답."""

    # 고유 상태 플래그
    is_order_not_found: bool = False

    # 결과 데이터
    current_order: Optional[SpotOrder] = None
