# SeeOrderWorker - Simulation Spot Gateway

from simple_logger import init_logging, func_logging
from financial_assets.order import SpotOrder
from financial_gateway.structures.see_order.request import SeeOrderRequest
from financial_gateway.structures.see_order.response import SeeOrderResponse


class SeeOrderWorker:
    # 주문 조회 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: SeeOrderRequest) -> SeeOrderResponse:
        # 주문 조회 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. order_id 추출
            order_id = self._get_order_id(request.order)

            # 2. Exchange에서 주문 조회
            order = self.exchange.get_order(order_id)
            receive_when = self._get_timestamp_ms()

            if order is None:
                return self._decode_error(request, "ORDER_NOT_FOUND", f"Order {order_id} not found", send_when, receive_when)

            # 3. Decode: → Response
            return self._decode_success(request, order, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "ORDER_NOT_FOUND", str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_order_id(self, order: SpotOrder) -> str:
        # Simulation Exchange는 order_id로만 조회 가능
        # (실제 거래소 Worker에서는 client_order_id 우선 사용)
        return order.order_id

    def _decode_success(
        self,
        request: SeeOrderRequest,
        order: SpotOrder,
        send_when: int,
        receive_when: int
    ) -> SeeOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order=order
        )

    def _decode_error(
        self,
        request: SeeOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> SeeOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return SeeOrderResponse(
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
