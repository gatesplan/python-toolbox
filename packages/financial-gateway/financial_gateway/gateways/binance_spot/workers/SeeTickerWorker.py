import time
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_gateway.structures.see_ticker import SeeTickerRequest, SeeTickerResponse


class SeeTickerWorker:
    """시세 조회 Worker
    
    Binance API:
    - GET /api/v3/ticker/24hr
    - Weight: 2
    """
    
    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler
    
    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeTickerRequest) -> SeeTickerResponse:
        send_when = self._utc_now_ms()
        
        try:
            symbol = request.address.to_symbol().to_compact()
            
            # MarketDataMixin의 get_24hr_ticker 메서드 사용
            from throttled_api.providers.binance.mixins import MarketDataMixin
            if hasattr(self.throttler, 'get_24hr_ticker'):
                api_response = await self.throttler.get_24hr_ticker(symbol=symbol)
            else:
                await self.throttler._check_and_wait(2)
                api_response = self.throttler.client.ticker_24hr(symbol=symbol)
            
            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeTickerWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)
    
    def _decode_success(
        self, request: SeeTickerRequest, api_response: dict, send_when: int, receive_when: int
    ) -> SeeTickerResponse:
        # Binance 24hr ticker response:
        # {
        #   "symbol": "BTCUSDT",
        #   "lastPrice": "50000.00",
        #   "openPrice": "48000.00",
        #   "highPrice": "51000.00",
        #   "lowPrice": "47500.00",
        #   "volume": "12345.67",
        #   "closeTime": 1234567890000
        # }
        
        current = float(api_response.get("lastPrice", 0))
        open_price = float(api_response.get("openPrice", 0))
        high = float(api_response.get("highPrice", 0))
        low = float(api_response.get("lowPrice", 0))
        volume = float(api_response.get("volume", 0))
        
        processed_when = api_response.get("closeTime") or (send_when + receive_when) // 2
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
