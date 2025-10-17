"""Trade module for financial assets.

This module provides data structures for representing completed trade records.

The Trade dataclass encapsulates information about executed trades from either
trading simulations or real trading API responses.
"""

from .trade import Trade
from .trade_side import TradeSide

__all__ = ["Trade", "TradeSide"]
