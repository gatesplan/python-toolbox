import time
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_gateway.structures.see_candles import SeeCandlesRequest, SeeCandlesResponse


class SeeCandlesWorker:
    """캔들 데이터 조회 Worker

    Upbit API:
    - GET /v1/candles/minutes/{unit}
    - GET /v1/candles/days
    - GET /v1/candles/weeks
    - GET /v1/candles/months
    - Weight: Quotation (초당 10회, 분당 600회)
    """

    # Interval 매핑
    INTERVAL_MAP = {
        "1m": ("minutes", 1),
        "3m": ("minutes", 3),
        "5m": ("minutes", 5),
        "10m": ("minutes", 10),
        "15m": ("minutes", 15),
        "30m": ("minutes", 30),
        "1h": ("minutes", 60),
        "4h": ("minutes", 240),
        "1d": ("days", None),
        "1w": ("weeks", None),
        "1M": ("months", None),
    }

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True)
    async def execute(self, request: SeeCandlesRequest) -> SeeCandlesResponse:
        send_when = self._utc_now_ms()

        try:
            # Upbit API 제약: start_time은 지원하지 않음 (to 파라미터만 지원)
            if request.start_time:
                raise ValueError(
                    "업비트 API는 start_time 파라미터를 지원하지 않습니다. "
                    "업비트는 'to'(end_time) 파라미터만 지원하며, 특정 시점부터 과거 방향으로 캔들을 조회합니다. "
                    "end_time과 limit를 사용해주세요."
                )

            market = f"{request.address.quote}-{request.address.base}"
            interval_type, unit = self._parse_interval(request.interval)
            count = request.limit if request.limit else 200

            # end_time을 ISO 8601 포맷으로 변환 (업비트 'to' 파라미터)
            to = self._convert_timestamp_to_iso(request.end_time) if request.end_time else None

            # Upbit API 호출
            if interval_type == "minutes":
                api_response = await self.throttler.get_candles_minutes(
                    unit=unit, market=market, to=to, count=count
                )
            elif interval_type == "days":
                api_response = await self.throttler.get_candles_days(
                    market=market, to=to, count=count
                )
            elif interval_type == "weeks":
                api_response = await self.throttler.get_candles_weeks(
                    market=market, to=to, count=count
                )
            elif interval_type == "months":
                api_response = await self.throttler.get_candles_months(
                    market=market, to=to, count=count
                )
            else:
                raise ValueError(f"Invalid interval type: {interval_type}")

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeCandlesWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _parse_interval(self, interval: str) -> tuple:
        """Interval을 Upbit API 형식으로 변환

        Returns:
            (interval_type, unit)
        """
        if interval in self.INTERVAL_MAP:
            return self.INTERVAL_MAP[interval]
        else:
            # 기본값: 1분봉
            return ("minutes", 1)

    def _decode_success(
        self, request: SeeCandlesRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeCandlesResponse:
        # Upbit candles 응답:
        # [
        #   {
        #     "market": "KRW-BTC",
        #     "candle_date_time_utc": "2024-01-01T00:00:00",
        #     "candle_date_time_kst": "2024-01-01T09:00:00",
        #     "opening_price": 50000000,
        #     "high_price": 51000000,
        #     "low_price": 49500000,
        #     "trade_price": 50500000,
        #     "timestamp": 1234567890000,
        #     "candle_acc_trade_volume": 100.5
        #   },
        #   ...
        # ]

        candles = []
        # 업비트 API는 최신→과거 순서로 반환하므로, 과거→최신으로 통일
        for candle_data in reversed(api_response):
            timestamp = candle_data.get("timestamp", 0)
            open_price = float(candle_data.get("opening_price", 0))
            high = float(candle_data.get("high_price", 0))
            low = float(candle_data.get("low_price", 0))
            close = float(candle_data.get("trade_price", 0))
            volume = float(candle_data.get("candle_acc_trade_volume", 0))

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

        error_str = str(error).lower()

        if "invalid" in error_str and "interval" in error_str:
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

    def _convert_timestamp_to_iso(self, timestamp_ms: int) -> str:
        """밀리초 타임스탬프를 ISO 8601 포맷으로 변환 (업비트 'to' 파라미터용)

        Args:
            timestamp_ms: 밀리초 단위 타임스탬프

        Returns:
            ISO 8601 포맷 문자열 (예: "2024-01-01T00:00:00Z")
        """
        from datetime import datetime
        dt = datetime.utcfromtimestamp(timestamp_ms / 1000)
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")

    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
