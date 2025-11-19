"""create_order Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from financial_assets.constants import OrderStatus
from financial_assets.trade import Trade


@dataclass
class CreateOrderResponse:
    """주문 생성 응답.

    거래소의 주문 생성 결과를 담는 응답 구조.
    """

    # 공통 필드 (항상 존재)
    request_id: str
    is_success: bool
    send_when: int  # UTC ms
    receive_when: int  # UTC ms
    processed_when: int  # UTC ms (서버 처리 시각)
    timegaps: int  # ms

    # 실패 시 필드
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # 성공 시 응답 데이터
    order_id: Optional[str] = None
    client_order_id: Optional[str] = None
    status: Optional[OrderStatus] = None
    created_at: Optional[int] = None  # UTC ms, from server
    fee_ratio: Optional[float] = None

    # 체결 정보 (전체 또는 일부 체결 시)
    trades: Optional[List[Trade]] = None
