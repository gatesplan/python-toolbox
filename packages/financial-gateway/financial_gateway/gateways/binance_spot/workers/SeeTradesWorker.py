import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.structures.see_trades import SeeTradesRequest, SeeTradesResponse


class SeeTradesWorker:
    """최근 체결 내역 조회 Worker

    Binance API:
    - GET /api/v3/trades
    - Weight: 25
    """

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeTradesRequest) -> SeeTradesResponse:
        send_when = self._utc_now_ms()

        try:
            symbol = request.address.to_symbol().to_compact()
            limit = request.limit if request.limit else 500

            # MarketDataMixin의 get_recent_trades 메서드 사용
            await self.throttler._check_and_wait(25)
            api_response = self.throttler.client.trades(symbol=symbol, limit=limit)

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeTradesWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeTradesRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeTradesResponse:
        trades = []
        for trade_data in api_response:
            price = float(trade_data.get("price", 0))
            qty = float(trade_data.get("qty", 0))
            timestamp = trade_data.get("time", send_when)

            # side 정보 (isBuyerMaker: true면 매도, false면 매수)
            is_buyer_maker = trade_data.get("isBuyerMaker", False)
            side = "SELL" if is_buyer_maker else "BUY"

            trades.append({
                "price": price,
                "quantity": qty,
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
