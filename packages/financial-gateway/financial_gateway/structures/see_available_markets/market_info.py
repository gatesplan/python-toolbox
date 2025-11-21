# Market information data structure.

from __future__ import annotations
from dataclasses import dataclass

from financial_assets.symbol import Symbol
from financial_assets.constants import MarketStatus


@dataclass
class MarketInfo:
    symbol: Symbol
    status: MarketStatus
