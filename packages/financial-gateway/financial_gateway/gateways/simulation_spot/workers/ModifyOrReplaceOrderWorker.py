# ModifyOrReplaceOrderWorker - Simulation Spot Gateway

import uuid
from typing import List
from simple_logger import init_logging, func_logging
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.constants import OrderStatus, TimeInForce
from financial_gateway.structures.modify_or_replace_order.request import ModifyOrReplaceOrderRequest
from financial_gateway.structures.modify_or_replace_order.response import ModifyOrReplaceOrderResponse


class ModifyOrReplaceOrderWorker:
    # 주문 수정/교체 Worker (Simulation)
    # Simulation에서는 modify가 없으므로 취소 후 재생성으로 구현

    @init_logging(level="INFO", log_params=True)
    def __init__(self, exchange):
        self.exchange = exchange

    @func_logging(level="INFO", log_params=True, log_result=True)
    def execute(self, request: ModifyOrReplaceOrderRequest) -> ModifyOrReplaceOrderResponse:
        # 주문 수정/교체 실행 (동기식)
        send_when = self._get_timestamp_ms()

        try:
            # 1. 기존 주문 조회
            order_id = request.original_order.order_id
            existing_order = self.exchange.get_order(order_id)

            if existing_order is None:
                receive_when = self._get_timestamp_ms()
                return self._decode_error(request, "ORDER_NOT_FOUND", f"Order {order_id} not found", send_when, receive_when)

            # 2. 주문 상태 확인 (이미 체결된 경우 에러)
            order_status = self.exchange.get_order_status(order_id)
            if order_status == OrderStatus.FILLED:
                receive_when = self._get_timestamp_ms()
                return self._decode_error(request, "ORDER_ALREADY_FILLED", f"Order {order_id} is already filled", send_when, receive_when)

            # 3. 기존 주문 취소
            self.exchange.cancel_order(order_id)

            # 4. 새 파라미터로 주문 생성
            new_order = self._create_new_order(request, existing_order)
            trades = self.exchange.place_order(new_order)
            receive_when = self._get_timestamp_ms()

            # 5. Decode: → Response
            return self._decode_success(request, new_order, trades, send_when, receive_when)

        except KeyError as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "ORDER_NOT_FOUND", str(e), send_when, receive_when)

        except ValueError as e:
            receive_when = self._get_timestamp_ms()
            error_message = str(e)

            # 에러 메시지로 에러 코드 분류
            if "balance" in error_message.lower() or "insufficient" in error_message.lower() or "잔고" in error_message:
                error_code = "INSUFFICIENT_BALANCE"
            elif "amount" in error_message.lower() or "quantity" in error_message.lower() or "수량" in error_message or "유효하지" in error_message:
                error_code = "INVALID_QUANTITY"
            else:
                error_code = "INVALID_PARAMETERS"

            return self._decode_error(request, error_code, error_message, send_when, receive_when)

        except Exception as e:
            receive_when = self._get_timestamp_ms()
            return self._decode_error(request, "API_ERROR", str(e), send_when, receive_when)

    def _create_new_order(self, request: ModifyOrReplaceOrderRequest, existing_order: SpotOrder) -> SpotOrder:
        # 새 주문 파라미터 결정 (None이면 기존값 유지)
        side = request.side if request.side is not None else existing_order.side
        order_type = request.order_type if request.order_type is not None else existing_order.order_type
        price = request.price if request.price is not None else existing_order.price
        amount = request.asset_quantity if request.asset_quantity is not None else existing_order.amount
        time_in_force = request.time_in_force if request.time_in_force is not None else (existing_order.time_in_force or TimeInForce.GTC)
        client_order_id = request.client_order_id if request.client_order_id is not None else existing_order.client_order_id

        # 새 order_id 생성
        new_order_id = f"sim_{uuid.uuid4().hex[:16]}"

        # timestamp (exchange의 현재 시각)
        timestamp = self.exchange.get_current_timestamp()

        # 새 주문 생성
        new_order = SpotOrder(
            order_id=new_order_id,
            stock_address=existing_order.stock_address,
            side=side,
            order_type=order_type,
            price=price,
            amount=amount,
            timestamp=timestamp,
            client_order_id=client_order_id,
            time_in_force=time_in_force,
            min_trade_amount=0.01  # 시뮬레이션 기본값
        )

        return new_order

    def _decode_success(
        self,
        request: ModifyOrReplaceOrderRequest,
        new_order: SpotOrder,
        trades: List[SpotTrade],
        send_when: int,
        receive_when: int
    ) -> ModifyOrReplaceOrderResponse:
        # 성공 응답 디코딩
        # processed_when (exchange 타임스탬프를 ms로 변환)
        processed_when = self.exchange.get_current_timestamp() * 1000

        # timegaps 계산
        timegaps = receive_when - send_when

        # status 결정
        if trades and len(trades) > 0:
            total_filled = sum(trade.pair.get_asset() for trade in trades)

            if total_filled >= new_order.amount:
                status = OrderStatus.FILLED
            elif total_filled > 0:
                status = OrderStatus.PARTIALLY_FILLED
            else:
                status = OrderStatus.NEW
        else:
            # trades가 비어있으면 미체결
            status = OrderStatus.NEW

        return ModifyOrReplaceOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=new_order.order_id,
            client_order_id=new_order.client_order_id,
            status=status,
            trades=trades if trades else None
        )

    def _decode_error(
        self,
        request: ModifyOrReplaceOrderRequest,
        error_code: str,
        error_message: str,
        send_when: int,
        receive_when: int
    ) -> ModifyOrReplaceOrderResponse:
        # 에러 응답 디코딩
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return ModifyOrReplaceOrderResponse(
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
