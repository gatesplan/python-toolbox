import time
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.constants import OrderStatus
from financial_gateway.structures.modify_or_replace_order import ModifyOrReplaceOrderRequest, ModifyOrReplaceOrderResponse


class ModifyOrReplaceOrderWorker:
    """주문 수정 Worker

    Upbit은 주문 수정 API가 없으므로 Cancel → Create로 구현
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: ModifyOrReplaceOrderRequest) -> ModifyOrReplaceOrderResponse:
        send_when = self._utc_now_ms()

        try:
            # 1. 기존 주문 취소
            cancel_response = await self.throttler.cancel_order(
                uuid=request.original_order.order_id if not request.original_order.client_order_id else None,
                identifier=request.original_order.client_order_id,
            )

            # 2. 새 주문 생성
            market = f"{request.address.quote}-{request.address.base}"
            side = "bid" if request.original_order.side.value == "BUY" else "ask"

            # 새 파라미터 적용
            new_quantity = request.new_quantity if request.new_quantity is not None else request.original_order.quantity
            new_price = request.new_price if request.new_price is not None else request.original_order.price

            ord_type = "limit"  # Upbit은 지정가만 수정 가능
            create_response = await self.throttler.create_order(
                market=market,
                side=side,
                ord_type=ord_type,
                volume=str(new_quantity),
                price=str(new_price),
                identifier=request.new_client_order_id,
            )

            receive_when = self._utc_now_ms()
            return self._decode_success(request, cancel_response, create_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"ModifyOrReplaceOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: ModifyOrReplaceOrderRequest, cancel_response: dict, create_response: dict, send_when: int, receive_when: int
    ) -> ModifyOrReplaceOrderResponse:
        old_order_id = cancel_response.get("uuid")
        new_order_id = create_response.get("uuid")
        new_status = self._map_status(create_response.get("state", "wait"))

        processed_when = self._parse_timestamp(create_response.get("created_at")) or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return ModifyOrReplaceOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            old_order_id=old_order_id,
            new_order_id=new_order_id,
            new_order_status=new_status,
        )

    def _decode_error(
        self, request: ModifyOrReplaceOrderRequest, error: Exception, send_when: int, receive_when: int
    ) -> ModifyOrReplaceOrderResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        error_str = str(error).lower()

        if "not found" in error_str:
            error_code = "ORDER_NOT_FOUND"
        else:
            error_code = "API_ERROR"

        return ModifyOrReplaceOrderResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=str(error),
        )

    def _map_status(self, upbit_state: str) -> OrderStatus:
        status_map = {
            "wait": OrderStatus.PENDING,
            "watch": OrderStatus.PENDING,
            "done": OrderStatus.FILLED,
            "cancel": OrderStatus.CANCELLED,
        }
        return status_map.get(upbit_state, OrderStatus.PENDING)

    def _parse_timestamp(self, timestamp_str: str) -> int:
        if not timestamp_str:
            return None
        from datetime import datetime
        try:
            dt = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            return int(dt.timestamp() * 1000)
        except:
            return None

    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
