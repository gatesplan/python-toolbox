"""ServerStatusResponse - 서버 상태 조회 응답."""

from dataclasses import dataclass

from .base_response import BaseResponse


@dataclass
class ServerStatusResponse(BaseResponse):
    """서버 상태 조회 요청에 대한 응답."""

    # 결과 데이터
    server: bool = False  # True: 정상, False: 장애/점검
