import time
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.structures.see_server_time import SeeServerTimeRequest, SeeServerTimeResponse


class SeeServerTimeWorker:
    """서버 시간 조회 Worker

    Binance API:
    - GET /api/v3/time
    - Response: {"serverTime": 1499827319559}
    - Weight: 1
    """

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeServerTimeRequest) -> SeeServerTimeResponse:
        """서버 시간 조회 실행"""
        try:
            # send_when 기록
            send_when = self._utc_now_ms()

            # API 호출 (via Throttler)
            api_response = await self.throttler.get_server_time()

            # receive_when 기록
            receive_when = self._utc_now_ms()

            # Decode: API response → Response 객체
            return self._decode_success(request, api_response, send_when, receive_when)

        except Exception as e:
            # 에러 처리
            logger.error(f"SeeServerTimeWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self,
        request: SeeServerTimeRequest,
        api_response: dict,
        send_when: int,
        receive_when: int,
    ) -> SeeServerTimeResponse:
        """성공 응답 디코딩

        Binance Response:
        {
            "serverTime": 1499827319559
        }
        """
        # serverTime 추출 (UTC ms)
        server_time = api_response.get("serverTime")

        # processed_when: 서버 타임스탬프 사용
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
            server_time=server_time,
        )

    def _decode_error(
        self,
        request: SeeServerTimeRequest,
        error: Exception,
        send_when: int,
        receive_when: int,
    ) -> SeeServerTimeResponse:
        """에러 응답 디코딩"""
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        # 에러 코드 분류
        error_code = self._classify_error(error)

        return SeeServerTimeResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=str(error),
        )

    def _classify_error(self, error: Exception) -> str:
        """에러 분류 후 표준 에러 코드 반환"""
        error_str = str(error).lower()

        # 네트워크 에러
        if "network" in error_str or "connection" in error_str or "timeout" in error_str:
            return "NETWORK_ERROR"

        # Rate limit 에러
        if "rate limit" in error_str or "429" in error_str:
            return "RATE_LIMIT_EXCEEDED"

        # 기본: API 에러
        return "API_ERROR"

    def _utc_now_ms(self) -> int:
        """현재 UTC 시각을 밀리초 단위로 반환"""
        return int(time.time() * 1000)
