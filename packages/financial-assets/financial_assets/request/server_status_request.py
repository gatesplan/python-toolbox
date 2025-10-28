"""ServerStatusRequest - 서버 상태 조회 요청."""

from dataclasses import dataclass

from .base_request import BaseRequest


@dataclass
class ServerStatusRequest(BaseRequest):
    """거래소 서버 상태 및 점검 여부 조회를 요청한다."""

    pass
