"""FeeInfoRequest - 거래 수수료 정보 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class FeeInfoRequest(BaseRequest):
    """현재 거래 수수료율 정보 조회를 요청한다."""

    pass
