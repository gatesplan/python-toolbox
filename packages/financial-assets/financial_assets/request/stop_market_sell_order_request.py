"""StopMarketSellOrderRequest - 스톱 마켓 매도 주문 요청."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_assets.constants import TimeInForce

from .base_request import BaseRequest


@dataclass
class StopMarketSellOrderRequest(BaseRequest):
    """스톱 마켓 매도 주문 생성을 요청한다.

    stop_price에 도달하면 시장가로 즉시 매도한다.
    """

    address: StockAddress
    stop_price: float       # 트리거 가격
    volume: float
    time_in_force: Optional[TimeInForce] = None
