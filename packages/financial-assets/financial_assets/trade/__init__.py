"""Trade module for financial assets.

This module provides data structures for representing completed trade records.

- SpotTrade: Immediate asset exchange (spot trading)
- FuturesTrade: Leveraged positions with PnL tracking (futures trading)
- Trade: Type alias for all trade types
"""

from .spot_trade import SpotTrade
from .futures_trade import FuturesTrade

Trade = SpotTrade | FuturesTrade

__all__ = ["SpotTrade", "FuturesTrade", "Trade"]
