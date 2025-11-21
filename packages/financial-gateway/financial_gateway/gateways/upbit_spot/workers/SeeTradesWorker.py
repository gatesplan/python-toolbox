import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_gateway.structures.see_trades import SeeTradesRequest, SeeTradesResponse


class SeeTradesWorker:
    """최근 체결 내역 조회 Worker

    Upbit API:
    - GET /v1/trades/ticks
    - Weight: Quotation (초당 10회, 분당 600회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeTradesRequest) -> SeeTradesResponse:
        send_when = self._utc_now_ms()

        try:
            market = f"{request.address.quote}-{request.address.base}"
            count = request.limit if request.limit else 100

            api_response = await self.throttler.get_trades_ticks(market=market, count=count)

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeTradesWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeTradesRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeTradesResponse:
        # Upbit trades 응답:
        # [
        #   {
        #     "market": "KRW-BTC",
        #     "trade_price": 50000000,
        #     "trade_volume": 0.1,
        #     "ask_bid": "ASK",  # ASK(매도), BID(매수)
        #     "timestamp": 1234567890000
        #   },
        #   ...
        # ]

        trades = []
        for trade_data in api_response:
            price = float(trade_data.get("trade_price", 0))
            volume = float(trade_data.get("trade_volume", 0))
            timestamp = trade_data.get("timestamp", send_when)

            # ask_bid → side 매핑
            ask_bid = trade_data.get("ask_bid", "ASK")
            side = "SELL" if ask_bid == "ASK" else "BUY"

            trades.append({
                "price": price,
                "quantity": volume,
                "timestamp": timestamp,
                "side": side,
            })

        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeTradesResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            trades=trades,
        )

    def _decode_error(
        self, request: SeeTradesRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeTradesResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeTradesResponse(
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
