"""Order module for managing trade orders.

This module provides order classes for different trading types:
- SpotOrder: Immediate asset exchange orders
- FuturesOrder: Leveraged position orders (not yet implemented)
- Order: Type alias for all order types
"""

from .spot_order import SpotOrder
from .spot_order_validator import SpotOrderValidator

# Type alias for all order types
# TODO: Add FuturesOrder when implemented
Order = SpotOrder

__all__ = ["SpotOrder", "SpotOrderValidator", "Order"]
