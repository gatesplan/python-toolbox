import time
from typing import List, Tuple
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.structures.see_orderbook import SeeOrderbookRequest, SeeOrderbookResponse


class SeeOrderbookWorker:
    """호가창 조회 Worker
    
    Binance API:
    - GET /api/v3/depth
    - Weight: 조정 가능 (limit에 따라 1-10)
    """
    
    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler
    
    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeOrderbookRequest) -> SeeOrderbookResponse:
        send_when = self._utc_now_ms()
        
        try:
            symbol = request.address.to_symbol().to_compact()
            limit = request.limit if request.limit else 100
            
            # MarketDataMixin의 get_orderbook 메서드 사용
            from throttled_api.providers.binance.mixins import MarketDataMixin
            if hasattr(self.throttler, 'get_orderbook'):
                api_response = await self.throttler.get_orderbook(symbol=symbol, limit=limit)
            else:
                await self.throttler._check_and_wait(5)
                api_response = self.throttler.client.depth(symbol=symbol, limit=limit)
            
            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeOrderbookWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)
    
    def _decode_success(
        self, request: SeeOrderbookRequest, api_response: dict, send_when: int, receive_when: int
    ) -> SeeOrderbookResponse:
        # Binance depth response:
        # {
        #   "lastUpdateId": 123456,
        #   "bids": [["50000.00", "1.5"], ["49999.00", "2.0"], ...],
        #   "asks": [["50001.00", "1.2"], ["50002.00", "0.8"], ...]
        # }

        from financial_assets.orderbook import OrderbookLevel, Orderbook

        # bids: 매수 호가 (높은 가격부터 - 이미 정렬됨)
        bids_raw = api_response.get("bids", [])
        bids = [OrderbookLevel(price=float(price), size=float(qty)) for price, qty in bids_raw]

        # asks: 매도 호가 (낮은 가격부터 - 이미 정렬됨)
        asks_raw = api_response.get("asks", [])
        asks = [OrderbookLevel(price=float(price), size=float(qty)) for price, qty in asks_raw]

        # Orderbook 객체 생성
        orderbook = Orderbook(asks=asks, bids=bids)

        processed_when = (send_when + receive_when) // 2
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
