import time
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.order.spot_order import SpotOrder
from financial_assets.constants import OrderType, OrderSide, OrderStatus
from financial_gateway.structures.see_order import SeeOrderRequest, SeeOrderResponse


class SeeOrderWorker:
    """주문 조회 Worker

    Upbit API:
    - GET /v1/order
    - Weight: Exchange Non-Order (초당 30회, 분당 900회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeOrderRequest) -> SeeOrderResponse:
        send_when = self._utc_now_ms()

        try:
            # request.order에서 ID 추출
            order = request.order
            api_response = await self.throttler.get_order(
                uuid=order.order_id if not order.client_order_id else None,
                identifier=order.client_order_id,
            )

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeOrderRequest, api_response: dict, send_when: int, receive_when: int
    ) -> SeeOrderResponse:
        # SpotOrder 재구성
        order = SpotOrder(
            order_id=api_response.get("uuid"),
            stock_address=request.order.stock_address,
            side=OrderSide.BUY if api_response.get("side") == "bid" else OrderSide.SELL,
            order_type=self._map_order_type(api_response.get("ord_type")),
            price=float(api_response.get("price", 0)) if api_response.get("price") else None,
            amount=float(api_response.get("volume", 0)),
            timestamp=self._parse_timestamp(api_response.get("created_at")) or (send_when + receive_when) // 2,
            client_order_id=request.order.client_order_id,
            filled_amount=float(api_response.get("executed_volume", 0)),
            status=self._map_status(api_response.get("state")),
        )

        processed_when = self._parse_timestamp(api_response.get("created_at")) or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order=order,
        )

    def _decode_error(
        self, request: SeeOrderRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeOrderResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeOrderResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code="API_ERROR",
            error_message=str(error),
        )

    def _map_order_type(self, ord_type: str) -> OrderType:
        type_map = {
            "limit": OrderType.LIMIT,
            "price": OrderType.MARKET,
            "market": OrderType.MARKET,
        }
        return type_map.get(ord_type, OrderType.LIMIT)

    def _map_status(self, upbit_state: str) -> OrderStatus:
        status_map = {
            "wait": OrderStatus.PENDING,
            "watch": OrderStatus.PENDING,
            "done": OrderStatus.FILLED,
            "cancel": OrderStatus.CANCELED,
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
