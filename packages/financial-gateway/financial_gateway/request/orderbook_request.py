"""OrderbookRequest - 호가창 조회 요청."""

from dataclasses import dataclass

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class OrderbookRequest(BaseRequest):
    """현재 호가창 스냅샷 조회를 요청한다."""

    address: StockAddress
