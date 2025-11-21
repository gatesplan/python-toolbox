"""Market status enumeration."""

from enum import Enum


class MarketStatus(Enum):
    """마켓 거래 상태.

    거래소에서 제공하는 마켓의 거래 가능 여부 및 상태를 정의합니다.
    """

    TRADING = "trading"              # 정상 거래 중
    HALT = "halt"                    # 일시 정지 (거래소 점검, 긴급 정지 등)
    BREAK = "break"                  # 휴장 (장 시작 전, 장 마감 후)
    CLOSED = "closed"                # 폐쇄 (상장폐지, 영구 종료)
    PRE_TRADING = "pre_trading"      # 거래 시작 전 (프리마켓, 프리런칭)
    POST_TRADING = "post_trading"    # 거래 종료 후 (포스트마켓)
    AUCTION = "auction"              # 경매 모드
    UNKNOWN = "unknown"              # 알 수 없음 (상태 정보 없음)
