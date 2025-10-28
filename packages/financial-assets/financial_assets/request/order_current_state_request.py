"""OrderCurrentStateRequest - 주문 상태 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class OrderCurrentStateRequest(BaseRequest):
    """특정 주문의 현재 상태 조회를 요청한다."""

    order_id: str
