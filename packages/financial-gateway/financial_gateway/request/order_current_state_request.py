"""OrderCurrentStateRequest - 주문 상태 조회 요청."""

from dataclasses import dataclass

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class OrderCurrentStateRequest(BaseRequest):
    """특정 주문의 현재 상태 조회를 요청한다."""

    address: StockAddress
    order_id: str
