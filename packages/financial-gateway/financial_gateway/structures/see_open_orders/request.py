"""see_open_orders Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeOpenOrdersRequest(BaseRequest):
    # 특정 마켓만 조회 (None이면 전체)
    address: Optional[StockAddress] = None

    # 개수 제한
    limit: Optional[int] = None
