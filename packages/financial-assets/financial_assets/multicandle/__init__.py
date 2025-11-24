"""MultiCandle module for multi-symbol candle data management.

This module provides efficient query interface for multiple symbols' candle data.
Designed as a building block for simulation and backtesting.

Usage:
    from financial_assets.multicandle import MultiCandle
    from financial_assets.candle import Candle

    candles = [Candle.load(addr1), Candle.load(addr2)]
    mc = MultiCandle(candles)

    # Time-based query (optimized for simulation loops)
    snapshot = mc.get_snapshot(timestamp)

    # Symbol-based query
    btc_data = mc.get_symbol_range("BTC/USDT", start_ts, end_ts)
"""

from .API.MultiCandle import MultiCandle

__all__ = ['MultiCandle']
