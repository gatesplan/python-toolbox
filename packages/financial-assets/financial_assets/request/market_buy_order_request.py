"""MarketBuyOrderRequest - 시장가 매수 주문 요청."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress

from .base_request import BaseRequest


@dataclass
class MarketBuyOrderRequest(BaseRequest):
    """시장가 매수 주문 생성을 요청한다."""

    address: StockAddress
    volume: float
    order_type: Optional[str] = None
