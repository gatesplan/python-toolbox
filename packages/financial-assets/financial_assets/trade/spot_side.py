"""Spot trade side enumeration.

This module defines the trading direction/side for executed spot trades.
Spot trading involves immediate exchange of assets (buy/sell).
For futures trading, see FuturesSide (LONG/SHORT).
"""

from enum import Enum


class SpotSide(Enum):
    """
    현물 거래 방향을 나타내는 Enum.

    Spot trading only supports immediate buy and sell of assets.
    For futures trading with leverage and positions, use FuturesSide.

    Attributes:
        BUY: 매수 (Buy) - 자산을 구매
        SELL: 매도 (Sell) - 자산을 판매

    Examples:
        >>> side = SpotSide.BUY
        >>> side == SpotSide.BUY
        True
        >>> side.name
        'BUY'
        >>> side.value
        'buy'
    """

    BUY = "buy"
    SELL = "sell"
