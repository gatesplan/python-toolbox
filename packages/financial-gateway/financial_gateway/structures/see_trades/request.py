"""see_trades Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_assets.order import SpotOrder
from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeTradesRequest(BaseRequest):
    # 조회 대상 마켓
    address: StockAddress

    # 특정 주문의 체결만 조회 (None이면 마켓 전체)
    order: Optional[SpotOrder] = None

    # 시간 범위
    start_time: Optional[int] = None
    end_time: Optional[int] = None

    # 개수 제한
    limit: Optional[int] = None
