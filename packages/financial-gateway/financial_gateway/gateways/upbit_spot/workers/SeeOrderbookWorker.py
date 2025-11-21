import time
from typing import List, Tuple
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_gateway.structures.see_orderbook import SeeOrderbookRequest, SeeOrderbookResponse


class SeeOrderbookWorker:
    """호가창 조회 Worker

    Upbit API:
    - GET /v1/orderbook
    - Weight: Quotation (초당 10회, 분당 600회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeOrderbookRequest) -> SeeOrderbookResponse:
        send_when = self._utc_now_ms()

        try:
            market = f"{request.address.quote}-{request.address.base}"
            api_response = await self.throttler.get_orderbook(markets=[market])

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeOrderbookWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeOrderbookRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeOrderbookResponse:
        # Upbit orderbook 응답 (리스트)
        if not api_response:
            raise ValueError("Empty orderbook response")

        orderbook_data = api_response[0]

        # Upbit 응답 구조:
        # {
        #   "market": "KRW-BTC",
        #   "timestamp": 1234567890000,
        #   "total_ask_size": 100.5,
        #   "total_bid_size": 200.3,
        #   "orderbook_units": [
        #     {
        #       "ask_price": 50001000,
        #       "bid_price": 50000000,
        #       "ask_size": 1.2,
        #       "bid_size": 1.5
        #     },
        #     ...
        #   ]
        # }

        orderbook_units = orderbook_data.get("orderbook_units", [])

        from financial_assets.orderbook import OrderbookLevel, Orderbook

        # bids: 매수 호가 (높은 가격부터)
        bids = []
        # asks: 매도 호가 (낮은 가격부터)
        asks = []

        for unit in orderbook_units:
            bid_price = float(unit.get("bid_price", 0))
            bid_size = float(unit.get("bid_size", 0))
            ask_price = float(unit.get("ask_price", 0))
            ask_size = float(unit.get("ask_size", 0))

            if bid_price > 0 and bid_size > 0:
                bids.append(OrderbookLevel(price=bid_price, size=bid_size))
            if ask_price > 0 and ask_size > 0:
                asks.append(OrderbookLevel(price=ask_price, size=ask_size))

        # Upbit은 이미 정렬되어 있음 (bids: 높은 가격부터, asks: 낮은 가격부터)

        # Orderbook 객체 생성
        orderbook = Orderbook(asks=asks, bids=bids)

        processed_when = orderbook_data.get("timestamp") or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeOrderbookResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            orderbook=orderbook,
        )

    def _decode_error(
        self, request: SeeOrderbookRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeOrderbookResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeOrderbookResponse(
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
