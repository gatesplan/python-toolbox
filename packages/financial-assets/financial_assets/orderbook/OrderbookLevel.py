from __future__ import annotations
from dataclasses import dataclass


@dataclass
class OrderbookLevel:
    price: float
    size: float
