import time
from typing import List, Dict
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.symbol import Symbol
from financial_assets.constants import MarketStatus
from financial_assets.market_info import MarketInfo
from financial_gateway.structures.see_available_markets import (
    SeeAvailableMarketsRequest,
    SeeAvailableMarketsResponse,
)


class SeeAvailableMarketsWorker:
    """거래 가능 마켓 목록 조회 Worker

    Binance API:
    - GET /api/v3/exchangeInfo
    - Weight: 20
    """

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(
        self, request: SeeAvailableMarketsRequest
    ) -> SeeAvailableMarketsResponse:
        send_when = self._utc_now_ms()

        try:
            # exchangeInfo 호출
            await self.throttler._check_and_wait(20)
            api_response = await self.throttler.get_exchange_info()

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeAvailableMarketsWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self,
        request: SeeAvailableMarketsRequest,
        api_response: dict,
        send_when: int,
        receive_when: int,
    ) -> SeeAvailableMarketsResponse:
        symbols_data = api_response.get("symbols", [])
        markets = []

        for symbol_data in symbols_data:
            base_asset = symbol_data.get("baseAsset")
            quote_asset = symbol_data.get("quoteAsset")
            status_str = symbol_data.get("status", "TRADING")

            # status 매핑
            if status_str == "TRADING":
                market_status = MarketStatus.TRADING
            elif status_str == "HALT":
                market_status = MarketStatus.HALT
            else:
                market_status = MarketStatus.UNKNOWN

            # filters 파싱
            filters = {f.get("filterType"): f for f in symbol_data.get("filters", [])}

            # PRICE_FILTER - 가격 호가 단위
            price_filter = filters.get("PRICE_FILTER", {})
            min_value_tick_size = float(price_filter.get("tickSize", 0)) if price_filter.get("tickSize") else None

            # LOT_SIZE - 수량 호가 단위 및 최소 수량
            lot_size = filters.get("LOT_SIZE", {})
            min_asset_tick_size = float(lot_size.get("stepSize", 0)) if lot_size.get("stepSize") else None
            min_trade_asset_size = float(lot_size.get("minQty", 0)) if lot_size.get("minQty") else None

            # MIN_NOTIONAL or NOTIONAL - 최소 주문금액
            min_notional_filter = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL", {})
            min_trade_value_size = float(min_notional_filter.get("minNotional", 0)) if min_notional_filter.get("minNotional") else None

            # MarketInfo 객체 생성
            market_info = MarketInfo(
                symbol=Symbol(f"{base_asset}/{quote_asset}"),
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
        self,
        request: SeeAvailableMarketsRequest,
        error: Exception,
        send_when: int,
        receive_when: int,
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
