# see_server_time Request structure.

from __future__ import annotations
from dataclasses import dataclass

from financial_gateway.structures.base import BaseRequest


@dataclass
class SeeServerTimeRequest(BaseRequest):
    # 서버 시간 조회는 추가 파라미터 없음
    pass
