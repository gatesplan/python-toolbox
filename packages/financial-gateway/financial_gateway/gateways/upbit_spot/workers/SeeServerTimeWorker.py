import time
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_gateway.structures.see_server_time import SeeServerTimeRequest, SeeServerTimeResponse


class SeeServerTimeWorker:
    """서버 시간 조회 Worker

    Upbit API:
    - Upbit은 서버 시간 전용 엔드포인트가 없음
    - 로컬 시간 사용
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeServerTimeRequest) -> SeeServerTimeResponse:
        send_when = self._utc_now_ms()

        try:
            # Upbit은 서버 시간 전용 엔드포인트가 없으므로 로컬 시간 사용
            server_time = self._utc_now_ms()

            receive_when = self._utc_now_ms()
            return self._decode_success(request, server_time, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeServerTimeWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeServerTimeRequest, server_time: int, send_when: int, receive_when: int
    ) -> SeeServerTimeResponse:
        timegaps = receive_when - send_when

        return SeeServerTimeResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=server_time,
            timegaps=timegaps,
            server_time=server_time,
        )

    def _decode_error(
        self, request: SeeServerTimeRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeServerTimeResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeServerTimeResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code="API_ERROR",
            error_message=str(error),
        )

    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
