import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.stock_address import StockAddress
from financial_assets.constants import MarketStatus
from financial_gateway.structures.see_available_markets import SeeAvailableMarketsRequest, SeeAvailableMarketsResponse


class SeeAvailableMarketsWorker:
    """거래 가능 마켓 목록 조회 Worker

    Upbit API:
    - GET /v1/market/all
    - Weight: Quotation (초당 10회, 분당 600회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeAvailableMarketsRequest) -> SeeAvailableMarketsResponse:
        send_when = self._utc_now_ms()

        try:
            api_response = await self.throttler.get_market_all(is_details=True)

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeAvailableMarketsWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeAvailableMarketsRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeAvailableMarketsResponse:
        # Upbit 응답 구조:
        # [
        #   {
        #     "market": "KRW-BTC",
        #     "korean_name": "비트코인",
        #     "english_name": "Bitcoin",
        #     "market_warning": "NONE"  # NONE, CAUTION
        #   }
        # ]

        markets = []

        for market_data in api_response:
            market_code = market_data.get("market", "")

            # 마켓 코드 파싱 (KRW-BTC → quote=KRW, base=BTC)
            if "-" in market_code:
                quote, base = market_code.split("-", 1)
            else:
                continue  # 잘못된 형식 스킵

            # market_warning → MarketStatus 매핑
            warning = market_data.get("market_warning", "NONE")
            if warning == "CAUTION":
                market_status = MarketStatus.HALT
            else:
                market_status = MarketStatus.TRADING

            # StockAddress 생성
            address = StockAddress(
                archetype="crypto",
                exchange="UPBIT",
                tradetype="SPOT",
                base=base,
                quote=quote,
                timeframe="1d",
            )

            # Upbit은 필터 정보 미제공 → 0으로 설정
            market_info = {
                "address": address,
                "status": market_status,
                "min_quantity": 0.0,
                "max_quantity": 0.0,
                "min_price": 0.0,
                "max_price": 0.0,
            }
            markets.append(market_info)

        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeAvailableMarketsResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            markets=markets,
        )

    def _decode_error(
        self, request: SeeAvailableMarketsRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeAvailableMarketsResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeAvailableMarketsResponse(
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
