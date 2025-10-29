"""Time In Force enumeration."""

from enum import Enum


class TimeInForce(Enum):
    """주문 유효 기간 정책 (Time In Force).

    주문이 거래소에서 얼마나 오래 유효하게 유지될지 결정합니다.
    """

    GTC = "GTC"  # Good Till Cancel - 취소할 때까지 유효
    IOC = "IOC"  # Immediate Or Cancel - 즉시 체결 가능한 부분만 체결, 나머지 취소
    FOK = "FOK"  # Fill Or Kill - 전량 즉시 체결되지 않으면 전체 거부
    GTD = "GTD"  # Good Till Date - 특정 시각까지 유효
