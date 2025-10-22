"""Spot trade direction enumeration."""

from enum import Enum


class SpotSide(Enum):
    """현물 거래 방향 (BUY, SELL)."""

    BUY = "buy"
    SELL = "sell"
