"""create_order Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, TimeInForce, SelfTradePreventionMode
from financial_gateway.structures.base import BaseRequest


@dataclass
class CreateOrderRequest(BaseRequest):

    # 거래 대상
    address: StockAddress

    # 주문 기본 정보
    side: OrderSide
    order_type: OrderType

    # 수량/가격 (Optional)
    asset_quantity: Optional[float] = None
    price: Optional[float] = None
    quote_quantity: Optional[float] = None
    stop_price: Optional[float] = None

    # 체결 조건
    time_in_force: Optional[TimeInForce] = None
    post_only: bool = False

    # 자전거래 방지
    self_trade_prevention: Optional[SelfTradePreventionMode] = None

    # 클라이언트 주문 ID
    client_order_id: Optional[str] = None
