# see_balance Request structure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, List

from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeBalanceRequest(BaseRequest):
    # 필터링
    currencies: Optional[List[str]] = None
