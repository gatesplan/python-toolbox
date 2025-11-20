# see_ticker Response structure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeTickerResponse(BaseResponse):

    # 성공 시 응답 데이터
    current: Optional[float] = None
    open: Optional[float] = None
    high: Optional[float] = None
    low: Optional[float] = None
    volume: Optional[float] = None
