"""TickerRequest - 시세 정보 조회 요청."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class TickerRequest(BaseRequest):
    """현재 시세 정보 조회를 요청한다."""

    address: Optional[StockAddress] = None
