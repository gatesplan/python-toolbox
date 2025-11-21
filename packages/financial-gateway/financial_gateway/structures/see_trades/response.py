"""see_trades Response structure."""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from financial_assets.trade import SpotTrade
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeTradesResponse(BaseResponse):
    # 성공 시 응답 데이터
    trades: List[SpotTrade] = field(default_factory=list)
