import time
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_gateway.structures.see_ticker import SeeTickerRequest, SeeTickerResponse


class SeeTickerWorker:
    """시세 조회 Worker

    Upbit API:
    - GET /v1/ticker
    - Weight: Quotation (초당 10회, 분당 600회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeTickerRequest) -> SeeTickerResponse:
        send_when = self._utc_now_ms()

        try:
            market = f"{request.address.quote}-{request.address.base}"
            api_response = await self.throttler.get_ticker(markets=[market])

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeTickerWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeTickerRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeTickerResponse:
        # Upbit ticker 응답 (리스트)
        if not api_response:
            raise ValueError("Empty ticker response")

        ticker_data = api_response[0]

        # Upbit 응답 구조:
        # {
        #   "market": "KRW-BTC",
        #   "trade_price": 50000000,
        #   "opening_price": 48000000,
        #   "high_price": 51000000,
        #   "low_price": 47500000,
        #   "acc_trade_volume_24h": 12345.67,
        #   "timestamp": 1234567890000
        # }

        current = float(ticker_data.get("trade_price", 0))
        open_price = float(ticker_data.get("opening_price", 0))
        high = float(ticker_data.get("high_price", 0))
        low = float(ticker_data.get("low_price", 0))
        volume = float(ticker_data.get("acc_trade_volume_24h", 0))

        processed_when = ticker_data.get("timestamp") or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeTickerResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            current=current,
            open=open_price,
            high=high,
            low=low,
            volume=volume,
        )

    def _decode_error(
        self, request: SeeTickerRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeTickerResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeTickerResponse(
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
