# SeeOpenOrdersWorker - Simulation Spot Gateway

from typing import List, Optional
from simple_logger import init_logging, func_logging
from financial_assets.order import SpotOrder
from financial_assets.stock_address import StockAddress
from financial_gateway.structures.see_open_orders.request import SeeOpenOrdersRequest
from financial_gateway.structures.see_open_orders.response import SeeOpenOrdersResponse


class SeeOpenOrdersWorker:
    # 미체결 주문 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeOpenOrdersRequest) -> SeeOpenOrdersResponse:
        # 미체결 주문 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. symbol 추출 (address가 있으면)
            symbol = self._get_symbol(request.address) if request.address else None

            # 2. Exchange에서 미체결 주문 조회
            orders = self.exchange.get_open_orders(symbol)
            receive_when = self._get_timestamp_ms()

            # 3. 최신순 정렬 (timestamp 내림차순)
            orders = sorted(orders, key=lambda o: o.timestamp, reverse=True)

            # 4. limit 적용
            if request.limit is not None and request.limit > 0:
                orders = orders[:request.limit]

            # 5. Decode: → Response
            return self._decode_success(request, orders, send_when, receive_when)

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
        request: SeeOpenOrdersRequest,
        orders: List[SpotOrder],
        send_when: int,
        receive_when: int
    ) -> SeeOpenOrdersResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOpenOrdersResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            orders=orders
        )

    def _decode_error(
        self,
        request: SeeOpenOrdersRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeOpenOrdersResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOpenOrdersResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=error_message,
            orders=[]
        )

    def _get_timestamp_ms(self) -> int:
        # 현재 시뮬레이션 타임스탬프 (초 → 밀리초 변환)
        return self.exchange.get_current_timestamp() * 1000
