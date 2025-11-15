"""OrderListRequest - 미체결 주문 목록 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class OrderListRequest(BaseRequest):
    """현재 active/live 상태인 미체결 주문 목록 조회를 요청한다."""

    pass
