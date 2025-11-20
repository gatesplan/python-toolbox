"""cancel_order Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.constants import OrderStatus
from financial_gateway.structures.base import BaseResponse


@dataclass
class CancelOrderResponse(BaseResponse):

    # 성공 시 응답 데이터
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None

    # 취소 시점 체결 정보
    filled_amount: Optional[float] = None
    remaining_amount: Optional[float] = None
