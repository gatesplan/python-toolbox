"""Order status enumeration."""

from enum import Enum


class OrderStatus(Enum):
    """주문 상태.

    주문의 생명주기에서 발생하는 상태를 정의합니다.
    """

    NEW = "new"                      # 신규 주문 접수
    PENDING = "pending"              # 대기 중 (미체결)
    PARTIALLY_FILLED = "partially_filled"  # 부분 체결
    FILLED = "filled"                # 전체 체결
    CANCELED = "canceled"            # 취소됨
    REJECTED = "rejected"            # 거부됨
