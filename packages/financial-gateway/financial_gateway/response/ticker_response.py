"""TickerResponse - 시세 정보 조회 응답."""

from dataclasses import dataclass, field

from .base_response import BaseResponse


@dataclass
class TickerResponse(BaseResponse):
    """시세 정보 조회 요청에 대한 응답.

    심볼별 24시간 시세 정보를 제공한다.
    """

    # 고유 상태 플래그
    is_invalid_market: bool = False

    # 결과 데이터
    result: dict[str, dict[str, float]] = field(default_factory=dict)  # {symbol: {timestamp, open, high, low, current, volume}}
