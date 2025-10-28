"""RecentTradesRequest - 최근 체결 내역 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class RecentTradesRequest(BaseRequest):
    """계정의 최근 체결 내역 조회를 요청한다."""

    pass
