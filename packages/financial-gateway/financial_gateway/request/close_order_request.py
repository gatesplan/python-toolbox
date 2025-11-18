"""CloseOrderRequest - 주문 취소 요청."""

from dataclasses import dataclass

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class CloseOrderRequest(BaseRequest):
    """주문 취소를 요청한다."""

    address: StockAddress
    order_id: str
