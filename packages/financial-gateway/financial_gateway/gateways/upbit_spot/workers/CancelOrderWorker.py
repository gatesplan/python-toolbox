import time
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.constants import OrderStatus
from financial_gateway.structures.cancel_order import CancelOrderRequest, CancelOrderResponse


class CancelOrderWorker:
    """주문 취소 Worker

    Upbit API:
    - DELETE /v1/order
    - Weight: Exchange Order (초당 8회, 분당 200회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: CancelOrderRequest) -> CancelOrderResponse:
        send_when = self._utc_now_ms()

        try:
            # identifier(client_order_id) 우선, 없으면 uuid(order_id)
            api_response = await self.throttler.cancel_order(
                uuid=request.order_id if not request.client_order_id else None,
                identifier=request.client_order_id,
            )

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"CancelOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: CancelOrderRequest, api_response: dict, send_when: int, receive_when: int
    ) -> CancelOrderResponse:
        order_id = api_response.get("uuid")
        executed_volume = float(api_response.get("executed_volume", 0))
        remaining_volume = float(api_response.get("remaining_volume", 0))

        processed_when = self._parse_timestamp(api_response.get("created_at")) or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return CancelOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=request.client_order_id,
            status=OrderStatus.CANCELLED,
            filled_amount=executed_volume,
            remaining_amount=remaining_volume,
        )

    def _decode_error(
        self, request: CancelOrderRequest, error: Exception, send_when: int, receive_when: int
    ) -> CancelOrderResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        error_str = str(error).lower()

        if "not found" in error_str or "order" in error_str:
            error_code = "ORDER_NOT_FOUND"
        else:
            error_code = "API_ERROR"

        return CancelOrderResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=str(error),
        )

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
