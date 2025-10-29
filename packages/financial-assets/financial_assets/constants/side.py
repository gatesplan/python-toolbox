"""Trade side enumeration."""

from enum import Enum


class Side(Enum):
    """거래 방향 (매수, 매도).

    현물 거래뿐만 아니라 선물 거래 등 모든 거래 유형에서 사용 가능한 공통 상수입니다.
    """

    BUY = "buy"
    SELL = "sell"
