"""CloseOrderRequest - 주문 취소 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class CloseOrderRequest(BaseRequest):
    """주문 취소를 요청한다."""

    order_id: str
