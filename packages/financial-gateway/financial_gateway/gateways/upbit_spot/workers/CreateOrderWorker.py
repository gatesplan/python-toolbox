import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.upbit import UpbitSpotThrottler
from financial_assets.order.spot_order import SpotOrder
from financial_assets.trade.spot_trade import SpotTrade
from financial_assets.constants import OrderType, OrderSide, OrderStatus
from financial_gateway.structures.create_order import CreateOrderRequest, CreateOrderResponse


class CreateOrderWorker:
    """주문 생성 Worker

    Upbit API:
    - POST /v1/orders
    - Weight: Exchange Order (초당 8회, 분당 200회)
    """

    def __init__(self, throttler: UpbitSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: CreateOrderRequest) -> CreateOrderResponse:
        send_when = self._utc_now_ms()

        try:
            # StockAddress → Upbit 마켓 코드 변환 (KRW-BTC)
            market = f"{request.address.quote}-{request.address.base}"

            # OrderSide → Upbit side 변환
            side = "bid" if request.order.side == OrderSide.BUY else "ask"

            # OrderType → Upbit ord_type 변환
            ord_type, volume, price = self._encode_order_type(request.order)

            # API 호출
            api_response = await self.throttler.create_order(
                market=market,
                side=side,
                ord_type=ord_type,
                volume=volume,
                price=price,
                identifier=request.order.client_order_id,
            )

            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"CreateOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _encode_order_type(self, order: SpotOrder) -> tuple:
        """OrderType을 Upbit ord_type으로 변환

        Returns:
            (ord_type, volume, price)
        """
        if order.order_type == OrderType.LIMIT:
            # 지정가: volume, price 모두 필요
            return ("limit", str(order.quantity), str(order.price))
        elif order.order_type == OrderType.MARKET:
            if order.side == OrderSide.BUY:
                # 시장가 매수: price만 필요 (매수 금액)
                return ("price", None, str(order.price))
            else:
                # 시장가 매도: volume만 필요
                return ("market", str(order.quantity), None)
        else:
            raise ValueError(f"Unsupported order type: {order.order_type}")

    def _decode_success(
        self, request: CreateOrderRequest, api_response: dict, send_when: int, receive_when: int
    ) -> CreateOrderResponse:
        # Upbit 응답 구조:
        # {
        #   "uuid": "cdd92199-2897-4e14-9448-f923320408ad",
        #   "side": "bid",
        #   "ord_type": "limit",
        #   "price": "100.0",
        #   "state": "wait",
        #   "market": "KRW-BTC",
        #   "created_at": "2018-04-10T15:42:23+09:00",
        #   "volume": "0.01",
        #   "remaining_volume": "0.01",
        #   "reserved_fee": "0.0015",
        #   "remaining_fee": "0.0015",
        #   "paid_fee": "0",
        #   "locked": "1.0015",
        #   "executed_volume": "0",
        #   "trades_count": 0
        # }

        order_id = api_response.get("uuid")
        status = self._map_status(api_response.get("state", "wait"))
        executed_volume = float(api_response.get("executed_volume", 0))
        remaining_volume = float(api_response.get("remaining_volume", 0))

        # 체결 내역은 별도 조회 필요 (Upbit은 주문 생성 시 체결 내역 미제공)
        fills: List[SpotTrade] = []

        processed_when = self._parse_timestamp(api_response.get("created_at")) or (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        return CreateOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=request.order.client_order_id,
            status=status,
            order_type=request.order.order_type,
            filled_amount=executed_volume,
            remaining_amount=remaining_volume,
            fills=fills,
        )

    def _decode_error(
        self, request: CreateOrderRequest, error: Exception, send_when: int, receive_when: int
    ) -> CreateOrderResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when

        error_str = str(error).lower()

        # 에러 코드 매핑
        if "balance" in error_str or "insufficient" in error_str:
            error_code = "INSUFFICIENT_BALANCE"
        elif "quantity" in error_str or "volume" in error_str:
            error_code = "INVALID_QUANTITY"
        elif "price" in error_str:
            error_code = "INVALID_PRICE"
        else:
            error_code = "API_ERROR"

        return CreateOrderResponse(
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
        """Upbit state를 OrderStatus로 매핑"""
        status_map = {
            "wait": OrderStatus.PENDING,
            "watch": OrderStatus.PENDING,
            "done": OrderStatus.FILLED,
            "cancel": OrderStatus.CANCELLED,
        }
        return status_map.get(upbit_state, OrderStatus.PENDING)

    def _parse_timestamp(self, timestamp_str: str) -> int:
        """Upbit 타임스탬프 파싱 (ISO 8601)"""
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
