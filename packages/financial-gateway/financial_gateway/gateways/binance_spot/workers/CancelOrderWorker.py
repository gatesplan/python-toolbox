import time
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.constants import OrderStatus
from financial_gateway.structures.cancel_order import CancelOrderRequest, CancelOrderResponse


class CancelOrderWorker:
    """주문 취소 Worker

    Binance API:
    - DELETE /api/v3/order
    - Weight: 1 (+ Orders: 1)
    """

    # Binance 에러 코드 → 표준 에러 코드 매핑
    BINANCE_ERROR_MAP = {
        -2011: "ORDER_NOT_FOUND",
        -1121: "INVALID_SYMBOL",
        -2010: "ORDER_ALREADY_FILLED",
        -1003: "RATE_LIMIT_EXCEEDED",
        -2015: "AUTHENTICATION_FAILED",
    }

    # OrderStatus 매핑
    STATUS_MAP = {
        "CANCELED": OrderStatus.CANCELED,
        "FILLED": OrderStatus.FILLED,
        "PARTIALLY_FILLED": OrderStatus.PARTIAL,
    }

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: CancelOrderRequest) -> CancelOrderResponse:
        """주문 취소 실행"""
        send_when = self._utc_now_ms()

        try:
            # 1. Encode: Request → Binance API params
            params = self._encode(request)

            # 2. API 호출 (via Throttler)
            api_response = await self.throttler.cancel_order(**params)
            receive_when = self._utc_now_ms()

            # 3. Decode: API response → Response 객체
            return self._decode_success(request, api_response, send_when, receive_when)

        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"CancelOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _encode(self, request: CancelOrderRequest) -> dict:
        """Request → Binance API params 변환

        Binance API 파라미터:
        - symbol (required): "BTCUSDT"
        - orderId: 주문 ID
        - origClientOrderId: 원본 클라이언트 주문 ID

        Note: orderId 또는 origClientOrderId 중 하나 필수
        """
        order = request.order
        symbol = order.stock_address.to_symbol().to_compact()

        params = {"symbol": symbol}

        # client_order_id 우선 사용 (있으면)
        if order.client_order_id:
            params["origClientOrderId"] = order.client_order_id
            logger.debug(f"Using client_order_id: {order.client_order_id}")
        else:
            # order_id 사용
            params["orderId"] = int(order.order_id)
            logger.debug(f"Using order_id: {order.order_id}")

        logger.debug(f"Encoded params: {params}")
        return params

    def _decode_success(
        self,
        request: CancelOrderRequest,
        api_response: dict,
        send_when: int,
        receive_when: int,
    ) -> CancelOrderResponse:
        """성공 응답 디코딩

        Binance Response:
        {
          "symbol": "LTCBTC",
          "orderId": 28,
          "origClientOrderId": "myOrder1",
          "clientOrderId": "cancelMyOrder1",
          "transactTime": 1507725176595,
          "price": "1.00000000",
          "origQty": "10.00000000",
          "executedQty": "8.00000000",
          "cummulativeQuoteQty": "8.00000000",
          "status": "CANCELED",
          "timeInForce": "GTC",
          "type": "LIMIT",
          "side": "SELL"
        }
        """
        # 기본 필드 추출
        order_id = str(api_response.get("orderId"))
        client_order_id = api_response.get("origClientOrderId")
        status_str = api_response.get("status")
        status = self.STATUS_MAP.get(status_str, OrderStatus.CANCELED)

        # 체결 정보
        orig_qty = float(api_response.get("origQty", 0))
        executed_qty = float(api_response.get("executedQty", 0))
        filled_amount = executed_qty
        remaining_amount = orig_qty - executed_qty

        # transactTime을 processed_when으로 사용
        processed_when = api_response.get("transactTime")
        if processed_when is None:
            processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return CancelOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=client_order_id,
            status=status,
            filled_amount=filled_amount,
            remaining_amount=remaining_amount,
        )

    def _decode_error(
        self,
        request: CancelOrderRequest,
        error: Exception,
        send_when: int,
        receive_when: int,
    ) -> CancelOrderResponse:
        """에러 응답 디코딩"""
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        # 에러 코드 분류
        error_code = self._classify_error(error)

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

    def _classify_error(self, error: Exception) -> str:
        """Binance 에러 → 표준 에러 코드 분류"""
        error_str = str(error)

        # Binance 에러 코드 추출 시도
        for binance_code, standard_code in self.BINANCE_ERROR_MAP.items():
            if str(binance_code) in error_str:
                return standard_code

        # 네트워크 에러
        if "network" in error_str.lower() or "connection" in error_str.lower():
            return "NETWORK_ERROR"

        # Rate limit 에러
        if "rate limit" in error_str.lower() or "429" in error_str:
            return "RATE_LIMIT_EXCEEDED"

        # 기본: API 에러
        return "API_ERROR"

    def _utc_now_ms(self) -> int:
        """현재 UTC 시각을 밀리초 단위로 반환"""
        return int(time.time() * 1000)
