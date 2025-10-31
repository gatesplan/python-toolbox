"""Trade side enumeration."""

from enum import Enum


class Side(Enum):
    """거래 방향.

    현물 거래와 선물 거래에서 사용되는 거래 방향을 표현합니다.
    - 현물: BUY(매수), SELL(매도)
    - 선물: LONG(롱 포지션), SHORT(숏 포지션)
    """

    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"
