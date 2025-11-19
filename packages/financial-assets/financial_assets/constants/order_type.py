"""Order type enumeration."""

from enum import Enum


class OrderType(Enum):
    """주문 유형.

    주문의 체결 방식을 정의합니다.
    """

    LIMIT = "limit"                      # 지정가 주문 - 특정 가격에 주문
    MARKET = "market"                    # 시장가 주문 - 현재 시장가로 즉시 체결
    STOP_LOSS = "stop_loss"              # 스탑 로스 - 손절 시장가 주문
    STOP_LOSS_LIMIT = "stop_loss_limit"  # 스탑 로스 리밋 - 손절 지정가 주문
    TAKE_PROFIT = "take_profit"          # 테이크 프로핏 - 익절 시장가 주문
    TAKE_PROFIT_LIMIT = "take_profit_limit"  # 테이크 프로핏 리밋 - 익절 지정가 주문
    STOP_LIMIT = "stop_limit"            # 스탑 리밋 - 트리거 가격 도달 시 지정가 주문
    STOP_MARKET = "stop_market"          # 스탑 마켓 - 트리거 가격 도달 시 시장가 주문
