"""Spot order module for managing spot trade orders.

This module provides the SpotOrder class for representing pending spot trade orders
and managing their fill status. Spot orders involve immediate asset exchange.
"""

from .spot_order import SpotOrder

__all__ = ["SpotOrder"]
