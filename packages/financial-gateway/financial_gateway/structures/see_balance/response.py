# see_balance Response structure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Dict, Union

from financial_assets.token import Token
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeBalanceResponse(BaseResponse):
    # 성공 시 응답 데이터
    # Dict[currency, Dict["balance"|"available"|"promised", Token|float]]
    balances: Optional[Dict[str, Dict[str, Union[Token, float]]]] = None
