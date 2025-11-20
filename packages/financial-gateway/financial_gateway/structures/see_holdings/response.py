# see_holdings Response structure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Union

from financial_assets.pair import Pair
from financial_assets.token import Token
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeHoldingsResponse(BaseResponse):
    # 성공 시 응답 데이터
    # Dict[symbol, Dict["balance"|"available"|"promised", Pair|float]]
    holdings: Optional[Dict[str, Dict[str, Union[Pair, float]]]] = None
