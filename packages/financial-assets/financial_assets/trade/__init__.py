"""Spot trade module for financial assets.

This module provides data structures for representing completed spot trade records.
Spot trading involves immediate exchange of assets.

The SpotTrade dataclass encapsulates information about executed spot trades from
either trading simulations or real trading API responses.
"""

from .spot_trade import SpotTrade
from .spot_side import SpotSide

__all__ = ["SpotTrade", "SpotSide"]
