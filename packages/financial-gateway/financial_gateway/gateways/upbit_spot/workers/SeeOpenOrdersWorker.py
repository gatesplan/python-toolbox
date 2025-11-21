import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.stock_address import StockAddress
from financial_assets.order.spot_order import SpotOrder
from financial_assets.constants import OrderType, OrderSide, OrderStatus
from financial_gateway.structures.see_open_orders import SeeOpenOrdersRequest, SeeOpenOrdersResponse


class SeeOpenOrdersWorker:
    """미체결 주문 목록 조회 Worker

    Upbit API:
    - GET /v1/orders/open
    - Weight: Exchange Non-Order (초당 30회, 분당 900회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeOpenOrdersRequest) -> SeeOpenOrdersResponse:
        send_when = self._utc_now_ms()

        try:
            market = None
            if request.address:
                market = f"{request.address.quote}-{request.address.base}"

            api_response = await self.throttler.get_orders_open(market=market)

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeOpenOrdersWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _decode_success(
        self, request: SeeOpenOrdersRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeOpenOrdersResponse:
        orders: List[SpotOrder] = []

        for order_data in api_response:
            # 마켓 코드 파싱 (KRW-BTC → quote=KRW, base=BTC)
            market_code = order_data.get("market", "")
            if "-" in market_code:
                quote, base = market_code.split("-", 1)
            else:
                quote, base = "KRW", market_code

            address = StockAddress("crypto", "UPBIT", "SPOT", base, quote, "1d")

            order = SpotOrder(
                order_id=order_data.get("uuid"),
                stock_address=address,
                side=OrderSide.BUY if order_data.get("side") == "bid" else OrderSide.SELL,
                order_type=self._map_order_type(order_data.get("ord_type")),
                price=float(order_data.get("price", 0)) if order_data.get("price") else None,
                amount=float(order_data.get("volume", 0)),
                timestamp=self._parse_timestamp(order_data.get("created_at")) or send_when,
                filled_amount=float(order_data.get("executed_volume", 0)),
                status=self._map_status(order_data.get("state")),
            )
            orders.append(order)

        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeOpenOrdersResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            orders=orders,
        )

    def _decode_error(
        self, request: SeeOpenOrdersRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeOpenOrdersResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return SeeOpenOrdersResponse(
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
