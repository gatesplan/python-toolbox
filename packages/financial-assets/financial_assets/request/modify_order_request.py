"""ModifyOrderRequest - 주문 수정 요청."""

from dataclasses import dataclass
from typing import Optional

from .base_request import BaseRequest


@dataclass
class ModifyOrderRequest(BaseRequest):
    """기존 주문 수정을 요청한다.

    Note:
        new_price와 new_volume 중 최소 하나는 None이 아니어야 한다.
        거래소에 따라 주문 수정을 지원하지 않을 수 있다.
    """

    order_id: str
    new_price: Optional[float] = None
    new_volume: Optional[float] = None
