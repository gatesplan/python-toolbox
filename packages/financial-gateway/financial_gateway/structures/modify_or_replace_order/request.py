"""modify_or_replace_order Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.order import SpotOrder
from financial_assets.constants import OrderSide, OrderType, TimeInForce, SelfTradePreventionMode
from financial_gateway.structures.base import BaseRequest


@dataclass
class ModifyOrReplaceOrderRequest(BaseRequest):
    # 기존 주문
    original_order: SpotOrder

    # 새 주문 파라미터 (None이면 변경 안 함)
    side: Optional[OrderSide] = None
    order_type: Optional[OrderType] = None
    asset_quantity: Optional[float] = None
    price: Optional[float] = None
    quote_quantity: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: Optional[TimeInForce] = None
    post_only: Optional[bool] = None
    self_trade_prevention: Optional[SelfTradePreventionMode] = None
    client_order_id: Optional[str] = None
