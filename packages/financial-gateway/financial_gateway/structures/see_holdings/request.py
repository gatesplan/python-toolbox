# see_holdings Request structure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from financial_assets.symbol import Symbol
from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeHoldingsRequest(BaseRequest):
    # 필터링
    symbols: Optional[List[Symbol]] = None
