"""CurrentBalanceRequest - 계정 잔고 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class CurrentBalanceRequest(BaseRequest):
    """현재 계정 잔고 조회를 요청한다."""

    pass
