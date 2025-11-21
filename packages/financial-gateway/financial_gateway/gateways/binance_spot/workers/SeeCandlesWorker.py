import time
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.structures.see_candles import SeeCandlesRequest, SeeCandlesResponse


class SeeCandlesWorker:
    """캔들 데이터 조회 Worker

    Binance API:
    - GET /api/v3/klines
    - Weight: 2
    """

    # Interval 매핑
    INTERVAL_MAP = {
        "1m": "1m",
        "3m": "3m",
        "5m": "5m",
        "15m": "15m",
        "30m": "30m",
        "1h": "1h",
        "2h": "2h",
        "4h": "4h",
        "6h": "6h",
        "8h": "8h",
        "12h": "12h",
        "1d": "1d",
        "3d": "3d",
        "1w": "1w",
        "1M": "1M",
    }

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeCandlesRequest) -> SeeCandlesResponse:
        send_when = self._utc_now_ms()

        try:
            symbol = request.address.to_symbol().to_compact()
            interval = self.INTERVAL_MAP.get(request.interval, request.interval)

            params = {
                "symbol": symbol,
                "interval": interval,
            }

            if request.start_time:
                params["startTime"] = request.start_time
            if request.end_time:
                params["endTime"] = request.end_time
            if request.limit:
                params["limit"] = request.limit

            # API 호출
            await self.throttler._check_and_wait(2)
            api_response = self.throttler.client.klines(**params)

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeCandlesWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeCandlesRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeCandlesResponse:
        candles = []
        for candle_data in api_response:
            timestamp = candle_data[0]
            open_price = float(candle_data[1])
            high = float(candle_data[2])
            low = float(candle_data[3])
            close = float(candle_data[4])
            volume = float(candle_data[5])

            candles.append({
                "timestamp": timestamp,
                "open": open_price,
                "high": high,
                "low": low,
                "close": close,
                "volume": volume,
            })

        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeCandlesResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            candles=candles,
        )

    def _decode_error(
        self, request: SeeCandlesRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeCandlesResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        error_str = str(error)
        if "invalid" in error_str.lower() and "interval" in error_str.lower():
            error_code = "INVALID_INTERVAL"
        else:
            error_code = "API_ERROR"

        return SeeCandlesResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=str(error),
        )

    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
