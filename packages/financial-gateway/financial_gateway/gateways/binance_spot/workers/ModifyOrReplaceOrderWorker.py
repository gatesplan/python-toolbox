import time
from typing import List, Optional
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.constants import OrderStatus, OrderType
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_gateway.structures.modify_or_replace_order import (
    ModifyOrReplaceOrderRequest,
    ModifyOrReplaceOrderResponse,
)


class ModifyOrReplaceOrderWorker:
    """주문 수정/재생성 Worker

    Binance API:
    - POST /api/v3/order/cancelReplace
    - Weight: 1 (+ Orders: 1)
    """

    # Binance 에러 코드 → 표준 에러 코드 매핑
    BINANCE_ERROR_MAP = {
        -2011: "ORDER_NOT_FOUND",
        -1013: "INVALID_QUANTITY",
        -1111: "INVALID_PRICE",
        -2010: "INSUFFICIENT_BALANCE",
        -1121: "INVALID_SYMBOL",
        -1003: "RATE_LIMIT_EXCEEDED",
        -2015: "AUTHENTICATION_FAILED",
    }

    # OrderStatus 매핑
    STATUS_MAP = {
        "NEW": OrderStatus.NEW,
        "PARTIALLY_FILLED": OrderStatus.PARTIALLY_FILLED,
        "FILLED": OrderStatus.FILLED,
        "CANCELED": OrderStatus.CANCELED,
        "REJECTED": OrderStatus.REJECTED,
        "EXPIRED": OrderStatus.EXPIRED,
    }

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(
        self, request: ModifyOrReplaceOrderRequest
    ) -> ModifyOrReplaceOrderResponse:
        """주문 수정/재생성 실행"""
        send_when = self._utc_now_ms()

        try:
            # 1. Amend 케이스 확인
            if self._is_amend_case(request):
                # 2. amendAllowed 확인
                if await self._check_amend_allowed(request.original_order):
                    # 3. Amend 시도
                    try:
                        return await self._try_amend(request, send_when)
                    except Exception as e:
                        logger.warning(f"Amend 실패, cancel-replace로 전환: {e}")

            # 4. Cancel-Replace 실행
            return await self._try_cancel_replace(request, send_when)

        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"ModifyOrReplaceOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _encode(self, request: ModifyOrReplaceOrderRequest) -> dict:
        """Request → Binance API params 변환

        Binance API 파라미터:
        - symbol (required)
        - cancelReplaceMode (required): STOP_ON_FAILURE or ALLOW_FAILURE
        - cancelOrderId or cancelOrigClientOrderId (required)
        - side (required for new order)
        - type (required for new order)
        - quantity, price 등 (새 주문 파라미터)
        """
        original_order = request.original_order
        symbol = original_order.stock_address.to_symbol().to_compact()

        params = {
            "symbol": symbol,
            # STOP_ON_FAILURE: 취소 실패 시 새 주문 생성하지 않음 (안전)
            "cancel_replace_mode": "STOP_ON_FAILURE",
            # 새 주문 응답 타입: FULL (fills 포함)
            "newOrderRespType": "FULL",
        }

        # 취소할 주문 ID
        if original_order.client_order_id:
            params["cancelOrigClientOrderId"] = original_order.client_order_id
        else:
            params["cancelOrderId"] = int(original_order.order_id)

        # 새 주문 파라미터 (None이 아닌 것만 전달)
        # side와 type은 필수
        params["side"] = (request.side or original_order.side).name
        params["type"] = (request.order_type or original_order.order_type).name

        # 수량/가격
        if request.asset_quantity is not None:
            params["quantity"] = request.asset_quantity
        elif original_order.amount:
            params["quantity"] = original_order.amount

        if request.price is not None:
            params["price"] = request.price
        elif original_order.price and original_order.order_type == OrderType.LIMIT:
            params["price"] = original_order.price

        if request.quote_quantity is not None:
            params["quoteOrderQty"] = request.quote_quantity

        if request.stop_price is not None:
            params["stopPrice"] = request.stop_price

        # timeInForce
        if request.time_in_force is not None:
            params["timeInForce"] = request.time_in_force.name
        elif original_order.time_in_force:
            params["timeInForce"] = original_order.time_in_force.name
        elif request.order_type == OrderType.LIMIT or original_order.order_type == OrderType.LIMIT:
            params["timeInForce"] = "GTC"

        # post_only 처리
        if request.post_only is not None and request.post_only:
            params["timeInForce"] = "GTX"

        # client_order_id
        if request.client_order_id:
            params["newClientOrderId"] = request.client_order_id

        # self_trade_prevention
        if request.self_trade_prevention is not None:
            params["selfTradePreventionMode"] = request.self_trade_prevention.name

        logger.debug(f"Encoded params: {params}")
        return params

    def _decode_success(
        self,
        request: ModifyOrReplaceOrderRequest,
        api_response: dict,
        send_when: int,
        receive_when: int,
    ) -> ModifyOrReplaceOrderResponse:
        """성공 응답 디코딩

        Binance Response:
        {
          "cancelResult": "SUCCESS",
          "newOrderResult": "SUCCESS",
          "cancelResponse": { /* canceled order details */ },
          "newOrderResponse": { /* new order details with fills */ }
        }
        """
        # cancelResult, newOrderResult 확인
        cancel_result = api_response.get("cancelResult")
        new_order_result = api_response.get("newOrderResult")

        if cancel_result != "SUCCESS" or new_order_result != "SUCCESS":
            # 부분 실패 처리
            error_msg = f"Cancel: {cancel_result}, New: {new_order_result}"
            logger.error(f"CancelReplace partial failure: {error_msg}")
            raise Exception(error_msg)

        # 새 주문 정보 추출
        new_order_response = api_response.get("newOrderResponse", {})

        order_id = str(new_order_response.get("orderId"))
        client_order_id = new_order_response.get("clientOrderId")
        status_str = new_order_response.get("status")
        status = self.STATUS_MAP.get(status_str, OrderStatus.UNKNOWN)

        # processed_when: transactTime 사용
        processed_when = new_order_response.get("transactTime")
        if processed_when is None:
            processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        # fills 배열 → SpotTrade 리스트 변환 (있으면)
        trades = None
        fills = new_order_response.get("fills")
        if fills:
            trades = self._decode_fills(
                request, fills, order_id, client_order_id, processed_when
            )

        return ModifyOrReplaceOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=client_order_id,
            status=status,
            trades=trades,
        )

    def _decode_fills(
        self,
        request: ModifyOrReplaceOrderRequest,
        fills: List[dict],
        order_id: str,
        client_order_id: str,
        timestamp: int,
    ) -> List[SpotTrade]:
        """fills 배열 → SpotTrade 리스트 변환"""
        trades = []
        symbol = request.original_order.stock_address.to_symbol()

        for fill in fills:
            trade_id = str(fill.get("tradeId"))
            price = float(fill.get("price"))
            qty = float(fill.get("qty"))
            commission = float(fill.get("commission", 0))
            commission_asset = fill.get("commissionAsset", "")

            # Pair 생성
            asset_token = Token(symbol.base, qty)
            value_token = Token(symbol.quote, qty * price)
            pair = Pair(asset_token, value_token)

            # fee Token
            fee = Token(commission_asset, commission) if commission > 0 else None

            # SpotOrder 생성
            spot_order = SpotOrder(
                order_id=order_id,
                stock_address=request.original_order.stock_address,
                side=request.side or request.original_order.side,
                order_type=request.order_type or request.original_order.order_type,
                price=request.price or request.original_order.price,
                amount=qty,
                timestamp=timestamp,
                client_order_id=client_order_id,
            )

            # SpotTrade 생성
            trade = SpotTrade(
                trade_id=trade_id,
                order=spot_order,
                pair=pair,
                timestamp=timestamp,
                fee=fee,
            )
            trades.append(trade)

        return trades

    def _decode_error(
        self,
        request: ModifyOrReplaceOrderRequest,
        error: Exception,
        send_when: int,
        receive_when: int,
    ) -> ModifyOrReplaceOrderResponse:
        """에러 응답 디코딩"""
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when
        error_code = self._classify_error(error)

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

    def _classify_error(self, error: Exception) -> str:
        """Binance 에러 → 표준 에러 코드 분류"""
        error_str = str(error)

        for binance_code, standard_code in self.BINANCE_ERROR_MAP.items():
            if str(binance_code) in error_str:
                return standard_code

        if "network" in error_str.lower() or "connection" in error_str.lower():
            return "NETWORK_ERROR"

        if "rate limit" in error_str.lower() or "429" in error_str:
            return "RATE_LIMIT_EXCEEDED"

        return "API_ERROR"

    def _utc_now_ms(self) -> int:
        """현재 UTC 시각을 밀리초 단위로 반환"""
        return int(time.time() * 1000)

    def _is_amend_case(self, request: ModifyOrReplaceOrderRequest) -> bool:
        """Amend 가능 케이스 확인

        조건:
        - 수량만 변경 (asset_quantity만 None이 아님)
        - 수량 감소 (새 수량 < 기존 수량)
        - 다른 모든 파라미터 변경 없음
        """
        return (
            # 수량 변경 필수
            request.asset_quantity is not None
            and request.asset_quantity < request.original_order.amount
            # 다른 파라미터 변경 없음
            and request.side is None
            and request.order_type is None
            and request.price is None
            and request.quote_quantity is None
            and request.stop_price is None
            and request.time_in_force is None
            and request.post_only is None
            and request.self_trade_prevention is None
            # client_order_id는 amend에서 지원 (newClientOrderId)
        )

    async def _check_amend_allowed(self, original_order: SpotOrder) -> bool:
        """심볼의 amendAllowed 확인

        exchangeInfo API를 호출하여 해당 심볼이 amend를 지원하는지 확인
        """
        try:
            symbol = original_order.stock_address.to_symbol().to_compact()
            exchange_info = await self.throttler.get_exchange_info(symbol=symbol)
            symbols = exchange_info.get("symbols", [])
            if symbols:
                amend_allowed = symbols[0].get("amendAllowed", False)
                logger.debug(f"Symbol {symbol} amendAllowed: {amend_allowed}")
                return amend_allowed
            return False
        except Exception as e:
            logger.warning(f"amendAllowed 확인 실패: {e}")
            return False

    async def _try_amend(
        self, request: ModifyOrReplaceOrderRequest, send_when: int
    ) -> ModifyOrReplaceOrderResponse:
        """Amend 시도

        PUT /api/v3/order/amend/keepPriority
        Weight: 4
        """
        original_order = request.original_order
        symbol = original_order.stock_address.to_symbol().to_compact()

        # Amend API 파라미터
        params = {
            "symbol": symbol,
            "newQty": request.asset_quantity,
        }

        # orderId 또는 origClientOrderId
        if original_order.client_order_id:
            params["origClientOrderId"] = original_order.client_order_id
        else:
            params["orderId"] = int(original_order.order_id)

        # newClientOrderId (optional)
        if request.client_order_id:
            params["newClientOrderId"] = request.client_order_id

        logger.debug(f"Amend params: {params}")

        # API 호출
        api_response = await self.throttler.amend_order(**params)
        receive_when = self._utc_now_ms()

        # Decode
        return self._decode_amend_success(request, api_response, send_when, receive_when)

    async def _try_cancel_replace(
        self, request: ModifyOrReplaceOrderRequest, send_when: int
    ) -> ModifyOrReplaceOrderResponse:
        """Cancel-Replace 실행 (기존 로직)"""
        # 1. Encode: Request → Binance API params
        params = self._encode(request)

        # 2. API 호출 (via Throttler)
        api_response = await self.throttler.cancel_replace_order(**params)
        receive_when = self._utc_now_ms()

        # 3. Decode: API response → Response 객체
        return self._decode_success(request, api_response, send_when, receive_when)

    def _decode_amend_success(
        self,
        request: ModifyOrReplaceOrderRequest,
        api_response: dict,
        send_when: int,
        receive_when: int,
    ) -> ModifyOrReplaceOrderResponse:
        """Amend 성공 응답 디코딩

        Binance Amend Response (예상):
        {
          "orderId": 12345,
          "symbol": "BTCUSDT",
          "clientOrderId": "...",
          "status": "NEW",
          "origQty": "1.0",
          "executedQty": "0.5",
          "transactTime": 1234567890000,
          ...
        }
        """
        order_id = str(api_response.get("orderId"))
        client_order_id = api_response.get("clientOrderId")
        status_str = api_response.get("status")
        status = self.STATUS_MAP.get(status_str, OrderStatus.UNKNOWN)

        # processed_when: transactTime 사용
        processed_when = api_response.get("transactTime")
        if processed_when is None:
            processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        return ModifyOrReplaceOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=client_order_id,
            status=status,
            trades=None,  # Amend는 체결 발생하지 않음
        )
