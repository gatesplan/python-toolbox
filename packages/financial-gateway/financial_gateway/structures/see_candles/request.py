"""see_candles Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_assets.stock_address import StockAddress
from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeCandlesRequest(BaseRequest):
    # 조회 대상 마켓
    address: StockAddress

    # 캔들 간격 (Binance 형식: "1m", "5m", "1h", "1d" 등)
    interval: str

    # 시간 범위
    start_time: Optional[int] = None
    end_time: Optional[int] = None

    # 개수 제한
    limit: Optional[int] = None
