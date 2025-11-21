from __future__ import annotations
from dataclasses import dataclass
from typing import List

from .OrderbookLevel import OrderbookLevel


@dataclass
class Orderbook:
    asks: List[OrderbookLevel]
    bids: List[OrderbookLevel]
