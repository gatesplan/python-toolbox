"""see_order Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.order import SpotOrder
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeOrderResponse(BaseResponse):
    # 성공 시 응답 데이터
    order: Optional[SpotOrder] = None
