"""Trade side enumeration.

This module defines the trading direction/side for executed trades.
"""

from enum import Enum


class TradeSide(Enum):
    """
    거래 방향을 나타내는 Enum.

    Attributes:
        BUY: 매수 (Buy)
        SELL: 매도 (Sell)
        LONG: 롱 포지션 진입
        SHORT: 숏 포지션 진입

    Examples:
        >>> side = TradeSide.BUY
        >>> side == TradeSide.BUY
        True
        >>> side.name
        'BUY'
        >>> side.value
        'buy'
    """

    BUY = "buy"
    SELL = "sell"
    LONG = "long"
    SHORT = "short"
