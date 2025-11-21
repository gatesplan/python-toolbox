"""see_available_markets Response structure."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from financial_gateway.structures.base import BaseResponse
from .market_info import MarketInfo


@dataclass
class SeeAvailableMarketsResponse(BaseResponse):
    # 성공 시 응답 데이터
    markets: List[MarketInfo] = field(default_factory=list)
