"""AvailableMarketsResponse - 거래 가능 마켓 조회 응답."""

from dataclasses import dataclass, field

from .base_response import BaseResponse


@dataclass
class AvailableMarketsResponse(BaseResponse):
    """거래 가능 마켓 조회 요청에 대한 응답.

    거래소에서 거래 가능한 모든 심볼 목록을 제공한다.
    """

    # 결과 데이터
    markets: list[str] = field(default_factory=list)
