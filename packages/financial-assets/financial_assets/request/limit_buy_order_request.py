"""LimitBuyOrderRequest - 지정가 매수 주문 요청."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class LimitBuyOrderRequest(BaseRequest):
    """지정가 매수 주문 생성을 요청한다."""

    address: StockAddress
    price: float
    volume: float
    order_type: Optional[str] = None
    post_only: bool = False
