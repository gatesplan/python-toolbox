"""AvailableMarketsRequest - 거래 가능 마켓 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class AvailableMarketsRequest(BaseRequest):
    """거래 가능한 마켓 목록 조회를 요청한다."""

    pass
