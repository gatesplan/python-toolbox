"""Trade module for financial assets.

This module provides data structures for representing completed trade records.

- Trade: Abstract base class for all trade types
- SpotTrade: Immediate asset exchange (spot trading)
- FuturesTrade: Leveraged positions with PnL tracking (futures trading)
"""

from .trade import Trade
from .spot_trade import SpotTrade
from .futures_trade import FuturesTrade

__all__ = ["Trade", "SpotTrade", "FuturesTrade"]
