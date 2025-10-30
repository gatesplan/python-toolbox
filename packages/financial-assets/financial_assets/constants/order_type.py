"""Order type enumeration."""

from enum import Enum


class OrderType(Enum):
    """주문 유형.

    주문의 체결 방식을 정의합니다.
    """

    LIMIT = "limit"          # 지정가 주문 - 특정 가격에 주문
    MARKET = "market"        # 시장가 주문 - 현재 시장가로 즉시 체결
    STOP_LIMIT = "stop_limit"    # 스탑 리밋 - 트리거 가격 도달 시 지정가 주문
    STOP_MARKET = "stop_market"  # 스탑 마켓 - 트리거 가격 도달 시 시장가 주문
