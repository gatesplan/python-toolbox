"""see_available_markets Request structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeAvailableMarketsRequest(BaseRequest):
    # 조회 개수 제한 (None이면 게이트웨이 기본값 또는 전체 조회)
    limit: Optional[int] = None
