"""RecentTradesResponse - 최근 체결 내역 조회 응답."""

from dataclasses import dataclass, field

from financial_assets.trade import SpotTrade

from .base_response import BaseResponse


@dataclass
class RecentTradesResponse(BaseResponse):
    """최근 체결 내역 조회 요청에 대한 응답.

    특정 심볼에 대한 계정 체결 내역을 시간 순으로 제공한다.
    """

    # 결과 데이터
    trades: list[SpotTrade] = field(default_factory=list)
