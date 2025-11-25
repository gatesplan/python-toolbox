# SeeTickerWorker - Simulation Spot Gateway

from simple_logger import init_logging, func_logging
from financial_assets.stock_address import StockAddress
from financial_gateway.structures.see_ticker.request import SeeTickerRequest
from financial_gateway.structures.see_ticker.response import SeeTickerResponse


class SeeTickerWorker:
    # 시세 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeTickerRequest) -> SeeTickerResponse:
        # 시세 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. MarketData에서 현재 가격 정보 조회
            price_data = self.exchange._market_data.get_current(symbol)
            receive_when = self._get_timestamp_ms()

            if price_data is None:
                return self._decode_error(request, "INVALID_SYMBOL", f"Symbol {symbol} not found", send_when, receive_when)

            # 3. Decode: Price → Response
            return self._decode_success(request, price_data, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "INVALID_SYMBOL", str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_symbol(self, address: StockAddress) -> str:
        # StockAddress → symbol (BTC/USDT)
        return address.to_symbol().to_slash()

    def _decode_success(
        self,
        request: SeeTickerRequest,
        price_data,
        send_when: int,
        receive_when: int
    ) -> SeeTickerResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTickerResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            current=price_data.c,
            open=price_data.o,
            high=price_data.h,
            low=price_data.l,
            volume=price_data.v
        )

    def _decode_error(
        self,
        request: SeeTickerRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeTickerResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeTickerResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=error_message
        )

    def _get_timestamp_ms(self) -> int:
        # 현재 시뮬레이션 타임스탬프 (초 → 밀리초 변환)
        return self.exchange.get_current_timestamp() * 1000
