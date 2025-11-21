import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.symbol import Symbol
from financial_assets.constants import MarketStatus
from financial_assets.market_info import MarketInfo
from financial_gateway.structures.see_available_markets import SeeAvailableMarketsRequest, SeeAvailableMarketsResponse
from financial_gateway.gateways.upbit_spot.utils import MIN_ORDER_VALUES, QTY_STEP_SIZES


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

            # market_warning은 거래 상태가 아니므로 status는 None (Upbit은 모두 거래 가능)
            # CAUTION은 투자유의 종목이지만 거래는 가능
            market_status = None

            # 최소 주문금액 (마켓별 고정값)
            min_trade_value_size = MIN_ORDER_VALUES.get(quote)

            # 최소 주문수량 (Upbit은 미제공, None)
            min_trade_asset_size = None

            # 가격 호가 단위는 None (KRW는 가격대별로 다름 - get_krw_price_tick_size 함수 사용)
            # 현재 가격을 모르므로 None
            min_value_tick_size = None

            # 수량 호가 단위 (마켓별 기본값)
            min_asset_tick_size = QTY_STEP_SIZES.get(quote)

            # MarketInfo 객체 생성
            market_info = MarketInfo(
                symbol=Symbol(f"{base}/{quote}"),
                status=market_status,
                min_trade_value_size=min_trade_value_size,
                min_trade_asset_size=min_trade_asset_size,
                min_value_tick_size=min_value_tick_size,
                min_asset_tick_size=min_asset_tick_size,
            )
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
