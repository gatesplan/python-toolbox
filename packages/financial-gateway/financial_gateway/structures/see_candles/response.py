"""see_candles Response structure."""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

import pandas as pd
from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeCandlesResponse(BaseResponse):
    # 성공 시 응답 데이터
    candles: Optional[pd.DataFrame] = None
