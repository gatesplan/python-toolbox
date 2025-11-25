# SeeOrderbookWorker - Simulation Spot Gateway

from simple_logger import init_logging, func_logging
from financial_assets.stock_address import StockAddress
from financial_assets.orderbook import Orderbook
from financial_gateway.structures.see_orderbook.request import SeeOrderbookRequest
from financial_gateway.structures.see_orderbook.response import SeeOrderbookResponse


class SeeOrderbookWorker:
    # 호가창 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeOrderbookRequest) -> SeeOrderbookResponse:
        # 호가창 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. StockAddress → symbol
            symbol = self._get_symbol(request.address)

            # 2. depth 결정 (limit이 None이면 기본값 10)
            depth = request.limit if request.limit is not None else 10

            # 3. Exchange에서 호가창 생성
            orderbook = self.exchange.get_orderbook(symbol, depth=depth)
            receive_when = self._get_timestamp_ms()

            # 4. Decode: → Response
            return self._decode_success(request, orderbook, send_when, receive_when)

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
        request: SeeOrderbookRequest,
        orderbook: Orderbook,
        send_when: int,
        receive_when: int
    ) -> SeeOrderbookResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderbookResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            orderbook=orderbook
        )

    def _decode_error(
        self,
        request: SeeOrderbookRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeOrderbookResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderbookResponse(
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
