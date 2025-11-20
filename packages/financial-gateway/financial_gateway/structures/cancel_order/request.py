"""cancel_order Request structure."""

from __future__ import annotations
from dataclasses import dataclass

from financial_assets.order import SpotOrder
from financial_gateway.structures.base import BaseRequest


@dataclass
class CancelOrderRequest(BaseRequest):
    # 취소할 주문
    order: SpotOrder
