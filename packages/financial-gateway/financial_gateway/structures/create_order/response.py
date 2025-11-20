"""create_order Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from financial_assets.constants import OrderStatus
from financial_assets.trade import Trade
from financial_gateway.structures.base import BaseResponse


@dataclass
class CreateOrderResponse(BaseResponse):

    # 성공 시 응답 데이터
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    created_at: Optional[int] = None  # UTC ms, from server
    fee_ratio: Optional[float] = None

    # 체결 정보 (전체 또는 일부 체결 시)
    trades: Optional[List[Trade]] = None
