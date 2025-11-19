"""Self-trade prevention mode enumeration."""

from enum import Enum


class SelfTradePreventionMode(Enum):
    """자전거래 방지 모드.

    동일 계정 내 주문 간 체결을 방지하는 정책을 정의합니다.
    """

    NONE = "none"                # 자전거래 방지 안함
    CANCEL_MAKER = "cancel_maker"  # Maker 주문 취소
    CANCEL_TAKER = "cancel_taker"  # Taker 주문 취소
    CANCEL_BOTH = "cancel_both"    # 양쪽 모두 취소
