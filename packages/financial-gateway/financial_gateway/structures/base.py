# Base Request/Response structures.

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass
class BaseRequest:
    # 공통 필드
    request_id: str
    gateway_name: str


@dataclass
class BaseResponse:
    # 공통 필드 (항상 존재)
    request_id: str
    is_success: bool
    send_when: int  # UTC ms
    receive_when: int  # UTC ms
    processed_when: int  # UTC ms (서버 처리 시각)
    timegaps: int  # ms

    # 실패 시 필드
    error_code: Optional[str] = None
    error_message: Optional[str] = None
