"""modify_or_replace_order Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from financial_assets.constants import OrderStatus
from financial_assets.trade import Trade
from financial_gateway.structures.base import BaseResponse


@dataclass
class ModifyOrReplaceOrderResponse(BaseResponse):
    # 성공 시 응답 데이터
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None

    # 체결 정보 (replace 시 기존 체결 내역)
    trades: Optional[List[Trade]] = None
