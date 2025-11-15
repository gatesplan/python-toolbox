"""StopLimitBuyOrderRequest - 스톱 리밋 매수 주문 요청."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_assets.constants import TimeInForce

from .base_request import BaseRequest


@dataclass
class StopLimitBuyOrderRequest(BaseRequest):
    """스톱 리밋 매수 주문 생성을 요청한다.

    stop_price에 도달하면 price로 지정가 매수 주문이 실행된다.
    """

    address: StockAddress
    stop_price: float       # 트리거 가격
    price: float            # 실행될 지정가
    volume: float
    time_in_force: Optional[TimeInForce] = None
    post_only: bool = False
