# CancelOrderWorker - Simulation Spot Gateway

from simple_logger import init_logging, func_logging
from financial_assets.constants import OrderStatus
from financial_gateway.structures.cancel_order.request import CancelOrderRequest
from financial_gateway.structures.cancel_order.response import CancelOrderResponse


class CancelOrderWorker:
    # 주문 취소 Worker (Simulation)

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: CancelOrderRequest) -> CancelOrderResponse:
        # 주문 취소 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. order_id 추출
            order_id = self._get_order_id(request.order)

            # 2. 취소 전 상태 조회 (filled_amount 계산용)
            filled_before = self._calculate_filled_amount(order_id)
            original_amount = request.order.amount

            # 3. Exchange 호출 (취소)
            self.exchange.cancel_order(order_id)
            receive_when = self._get_timestamp_ms()

            # 4. Decode: → Response
            return self._decode_success(request, order_id, filled_before, original_amount, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "ORDER_NOT_FOUND", str(e), send_when, receive_when)

        except ValueError as e:
            receive_when = self._get_timestamp_ms()
            # OrderHistory에서 상태 확인하여 에러 코드 결정
            error_code = self._classify_error(request.order, e)
            return self._decode_error(request, error_code, str(e), send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _get_order_id(self, order):
        # order_id 사용 (OrderBook은 order_id로만 관리)
        return order.order_id

    def _calculate_filled_amount(self, order_id: str) -> float:
        # 주문의 체결 수량 계산 (Trade history 조회)
        trades = self.exchange.get_trade_history()
        filled = sum(
            trade.pair.get_asset()
            for trade in trades
            if trade.order.order_id == order_id or trade.order.client_order_id == order_id
        )
        return filled

    def _classify_error(self, order, error: Exception) -> str:
        # 에러 분류
        error_message = str(error)

        # OrderHistory에서 주문 상태 확인
        order_id = self._get_order_id(order)
        order_obj = self.exchange.get_order(order_id)

        if order_obj is None:
            return "ORDER_NOT_FOUND"

        # 주문 상태 확인
        status = self.exchange.get_order_status(order_id)

        if status == OrderStatus.FILLED:
            return "ORDER_ALREADY_FILLED"
        elif status == OrderStatus.CANCELED:
            return "ORDER_ALREADY_CANCELED"
        else:
            # 기타: 메시지로 분류
            if "filled" in error_message.lower() or "체결" in error_message:
                return "ORDER_ALREADY_FILLED"
            elif "canceled" in error_message.lower() or "취소" in error_message:
                return "ORDER_ALREADY_CANCELED"
            else:
                return "API_ERROR"

    def _decode_success(
        self,
        request: CancelOrderRequest,
        order_id: str,
        filled_amount: float,
        original_amount: float,
        send_when: int,
        receive_when: int
    ) -> CancelOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        # remaining_amount 계산
        remaining_amount = original_amount - filled_amount

        return CancelOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=request.order.client_order_id,
            status=OrderStatus.CANCELED,
            filled_amount=filled_amount,
            remaining_amount=remaining_amount
        )

    def _decode_error(
        self,
        request: CancelOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> CancelOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return CancelOrderResponse(
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
