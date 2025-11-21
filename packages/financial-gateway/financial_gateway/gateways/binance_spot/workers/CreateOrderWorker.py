import time
from typing import List, Optional
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.stock_address import StockAddress
from financial_assets.constants import OrderSide, OrderType, OrderStatus, TimeInForce
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotTrade
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_gateway.structures.create_order import CreateOrderRequest, CreateOrderResponse


class CreateOrderWorker:
    """주문 생성 Worker

    Binance API:
    - POST /api/v3/order
    - Weight: 1 (+ Orders: 1)
    """

    # Binance 에러 코드 → 표준 에러 코드 매핑
    BINANCE_ERROR_MAP = {
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
        "PARTIALLY_FILLED": OrderStatus.PARTIAL,
        "FILLED": OrderStatus.FILLED,
        "CANCELED": OrderStatus.CANCELED,
        "REJECTED": OrderStatus.REJECTED,
        "EXPIRED": OrderStatus.EXPIRED,
    }

    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler

    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: CreateOrderRequest) -> CreateOrderResponse:
        """주문 생성 실행"""
        try:
            # 1. Encode: Request → Binance API params
            params = self._encode(request)

            # 2. API 호출 (via Throttler)
            send_when = self._utc_now_ms()
            api_response = await self.throttler.create_order(**params)
            receive_when = self._utc_now_ms()

            # 3. Decode: API response → Response 객체
            return self._decode_success(request, api_response, send_when, receive_when)

        except Exception as e:
            # 에러 처리
            logger.error(f"CreateOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)

    def _encode(self, request: CreateOrderRequest) -> dict:
        """Request → Binance API params 변환

        Binance API 파라미터:
        - symbol (required): "BTCUSDT"
        - side (required): "BUY" or "SELL"
        - type (required): "LIMIT", "MARKET", "STOP_LOSS", etc.
        - quantity: 주문 수량
        - quoteOrderQty: 시장가 매수 시 인용 자산 수량
        - price: 지정가 주문 가격
        - stopPrice: 스톱 주문 트리거 가격
        - timeInForce: "GTC", "IOC", "FOK"
        - newClientOrderId: 클라이언트 주문 ID
        - newOrderRespType: "FULL" (fills 포함)
        """
        params = {
            # 필수 파라미터
            "symbol": self._encode_symbol(request.address),
            "side": request.side.name,
            "type": request.order_type.name,
            # FULL 응답 타입 (fills 포함)
            "newOrderRespType": "FULL",
        }

        # 수량/가격 파라미터
        if request.asset_quantity is not None:
            params["quantity"] = request.asset_quantity
        if request.quote_quantity is not None:
            params["quoteOrderQty"] = request.quote_quantity
        if request.price is not None:
            params["price"] = request.price
        if request.stop_price is not None:
            params["stopPrice"] = request.stop_price

        # timeInForce 처리
        if request.time_in_force is not None:
            params["timeInForce"] = request.time_in_force.name
        elif request.order_type == OrderType.LIMIT:
            # LIMIT 주문은 timeInForce 필수
            params["timeInForce"] = "GTC"

        # post_only 처리: timeInForce=GTX로 변환
        if request.post_only:
            params["timeInForce"] = "GTX"

        # client_order_id 처리
        if request.client_order_id:
            params["newClientOrderId"] = request.client_order_id
        else:
            # request_id를 client_order_id로 사용
            params["newClientOrderId"] = request.request_id

        # self_trade_prevention 처리 (Binance는 selfTradePreventionMode 지원)
        if request.self_trade_prevention is not None:
            params["selfTradePreventionMode"] = request.self_trade_prevention.name

        logger.debug(f"Encoded params: {params}")
        return params

    def _decode_success(
        self,
        request: CreateOrderRequest,
        api_response: dict,
        send_when: int,
        receive_when: int,
    ) -> CreateOrderResponse:
        """성공 응답 디코딩

        Binance FULL Response:
        {
          "symbol": "BTCUSDT",
          "orderId": 28,
          "clientOrderId": "6gCrw2kRUAF9CvJDGP16IP",
          "transactTime": 1507725176595,
          "status": "FILLED",
          "fills": [
            {
              "price": "4000.00000000",
              "qty": "1.00000000",
              "commission": "4.00000000",
              "commissionAsset": "USDT",
              "tradeId": 56
            }
          ]
        }
        """
        # 기본 필드 추출
        order_id = str(api_response.get("orderId"))
        client_order_id = api_response.get("clientOrderId")
        status_str = api_response.get("status")
        status = self.STATUS_MAP.get(status_str, OrderStatus.UNKNOWN)

        # transactTime을 processed_when으로 사용
        processed_when = api_response.get("transactTime")
        if processed_when is None:
            # Fallback: 추정값
            processed_when = (send_when + receive_when) // 2

        # created_at: 주문 생성 시각 (workingTime 또는 transactTime)
        created_at = api_response.get("workingTime", processed_when)

        # timegaps 계산
        timegaps = receive_when - send_when

        # fills 배열 → SpotTrade 리스트 변환
        trades = None
        fills = api_response.get("fills")
        if fills:
            trades = self._decode_fills(request, fills, order_id, client_order_id, created_at)

        return CreateOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order_id=order_id,
            client_order_id=client_order_id,
            status=status,
            created_at=created_at,
            trades=trades,
        )

    def _decode_fills(
        self,
        request: CreateOrderRequest,
        fills: List[dict],
        order_id: str,
        client_order_id: str,
        timestamp: int,
    ) -> List[SpotTrade]:
        """fills 배열 → SpotTrade 리스트 변환

        Fill structure:
        {
          "price": "4000.00000000",
          "qty": "1.00000000",
          "commission": "4.00000000",
          "commissionAsset": "USDT",
          "tradeId": 56
        }
        """
        trades = []
        symbol = request.address.to_symbol()

        for fill in fills:
            trade_id = str(fill.get("tradeId"))
            price = float(fill.get("price"))
            qty = float(fill.get("qty"))
            commission = float(fill.get("commission", 0))
            commission_asset = fill.get("commissionAsset", "")

            # Pair 생성: asset + value
            asset_token = Token(symbol.base, qty)
            value_token = Token(symbol.quote, qty * price)
            pair = Pair(asset_token, value_token)

            # fee Token 생성
            fee = Token(commission_asset, commission) if commission > 0 else None

            # SpotOrder 생성 (임시 - Trade가 order를 참조하므로 필요)
            # 실제로는 이 order를 CreateOrderResponse에서 반환된 정보로 생성해야 함
            spot_order = SpotOrder(
                order_id=order_id,
                stock_address=request.address,
                side=request.side,
                order_type=request.order_type,
                price=request.price,
                amount=qty,  # 이 fill의 수량
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
        request: CreateOrderRequest,
        error: Exception,
        send_when: int,
        receive_when: int,
    ) -> CreateOrderResponse:
        """에러 응답 디코딩"""
        # processed_when 추정값
        processed_when = (send_when + receive_when) // 2

        # timegaps 계산
        timegaps = receive_when - send_when

        # 에러 코드 분류
        error_code = self._classify_error(error)

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

    def _encode_symbol(self, address: StockAddress) -> str:
        """StockAddress → Binance symbol 문자열 변환

        예: StockAddress(base="BTC", quote="USDT") → "BTCUSDT"
        """
        symbol = address.to_symbol()
        return symbol.to_compact()

    def _utc_now_ms(self) -> int:
        """현재 UTC 시각을 밀리초 단위로 반환"""
        return int(time.time() * 1000)
