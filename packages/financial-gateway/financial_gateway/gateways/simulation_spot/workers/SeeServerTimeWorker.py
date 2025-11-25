# SeeServerTimeWorker - Simulation Spot Gateway

from simple_logger import init_logging, func_logging
from financial_gateway.structures.see_server_time.request import SeeServerTimeRequest
from financial_gateway.structures.see_server_time.response import SeeServerTimeResponse


class SeeServerTimeWorker:
    # 서버 시간 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeServerTimeRequest) -> SeeServerTimeResponse:
        # 서버 시간 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # Exchange에서 현재 타임스탬프 조회
            server_time = self.exchange.get_current_timestamp() * 1000  # 초 → 밀리초
            receive_when = self._get_timestamp_ms()

            # Decode: → Response
            return self._decode_success(request, server_time, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _decode_success(
        self,
        request: SeeServerTimeRequest,
        server_time: int,
        send_when: int,
        receive_when: int
    ) -> SeeServerTimeResponse:
        # 성공 응답 디코딩
        # processed_when은 server_time과 동일
        processed_when = server_time

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeServerTimeResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            server_time=server_time
        )

    def _decode_error(
        self,
        request: SeeServerTimeRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeServerTimeResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeServerTimeResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=error_message
        )

    def _get_timestamp_ms(self) -> int:
        # 현재 시뮬레이션 타임스탬프 (초 → 밀리초 변환)
        return self.exchange.get_current_timestamp() * 1000
