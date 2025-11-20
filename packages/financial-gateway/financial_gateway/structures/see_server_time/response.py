# see_server_time Response structure.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from financial_gateway.structures.base import BaseResponse


@dataclass
class SeeServerTimeResponse(BaseResponse):

    # 성공 시 응답 데이터
    server_time: Optional[int] = None  # UTC ms
