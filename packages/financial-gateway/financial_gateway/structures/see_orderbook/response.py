"""see_orderbook Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.orderbook import Orderbook
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeOrderbookResponse(BaseResponse):
    # 성공 시 응답 데이터
    orderbook: Optional[Orderbook] = None
