"""see_open_orders Response structure."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from financial_assets.order import SpotOrder
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeOpenOrdersResponse(BaseResponse):
    # 성공 시 응답 데이터
    orders: List[SpotOrder] = field(default_factory=list)
