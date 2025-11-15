"""TradeInfoRequest - 주문 체결 내역 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class TradeInfoRequest(BaseRequest):
    """특정 주문의 체결 내역 조회를 요청한다."""

    order_id: str
