"""see_orderbook Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeOrderbookRequest(BaseRequest):
    # 조회 대상
    address: StockAddress

    # 호가 레벨 수 (기본값: 10)
    limit: Optional[int] = None
