"""PriceDataResponse - 캔들 데이터 조회 응답."""

from dataclasses import dataclass
from typing import Optional

from financial_assets.candle import Candle

from .base_response import BaseResponse


@dataclass
class PriceDataResponse(BaseResponse):
    """캔들 데이터 조회 요청에 대한 응답."""

    # 고유 상태 플래그
    is_invalid_market: bool = False
    is_invalid_interval: bool = False
    is_invalid_time_range: bool = False
    is_data_not_available: bool = False

    # 결과 데이터
    candle: Optional[Candle] = None
