import time
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.constants import OrderStatus
from financial_assets.order import SpotOrder
from financial_gateway.structures.see_order import SeeOrderRequest, SeeOrderResponse


class SeeOrderWorker:
    """주문 조회 Worker
    
    Binance API:
    - GET /api/v3/order
    - Weight: 4
    """
    
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
    async def execute(self, request: SeeOrderRequest) -> SeeOrderResponse:
        send_when = self._utc_now_ms()
        
        try:
            params = self._encode(request)
            api_response = await self.throttler.get_order(**params)
            receive_when = self._utc_now_ms()
            
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeOrderWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)
    
    def _encode(self, request: SeeOrderRequest) -> dict:
        order = request.order
        symbol = order.stock_address.to_symbol().to_compact()
        
        params = {"symbol": symbol}
        
        if order.client_order_id:
            params["orig_client_order_id"] = order.client_order_id
        else:
            params["order_id"] = int(order.order_id)
        
        return params
    
    def _decode_success(
        self, request: SeeOrderRequest, api_response: dict, send_when: int, receive_when: int
    ) -> SeeOrderResponse:
        # SpotOrder 생성
        order_id = str(api_response.get("orderId"))
        client_order_id = api_response.get("clientOrderId")
        status_str = api_response.get("status")
        status = self.STATUS_MAP.get(status_str, OrderStatus.UNKNOWN)
        
        price_str = api_response.get("price", "0")
        price = float(price_str) if price_str and price_str != "0.00000000" else None
        
        orig_qty = float(api_response.get("origQty", 0))
        executed_qty = float(api_response.get("executedQty", 0))
        
        order_type_str = api_response.get("type", "LIMIT")
        from financial_assets.constants import OrderType
        order_type = getattr(OrderType, order_type_str, OrderType.LIMIT)
        
        side_str = api_response.get("side", "BUY")
        from financial_assets.constants import OrderSide
        side = getattr(OrderSide, side_str, OrderSide.BUY)
        
        time_ms = api_response.get("time") or api_response.get("updateTime")
        
        spot_order = SpotOrder(
            order_id=order_id,
            stock_address=request.order.stock_address,
            side=side,
            order_type=order_type,
            price=price,
            amount=orig_qty,
            timestamp=time_ms or send_when,
            client_order_id=client_order_id,
            filled_amount=executed_qty,
            status=status,
        )
        
        processed_when = api_response.get("updateTime") or (send_when + receive_when) // 2
        timegaps = receive_when - send_when
        
        return SeeOrderResponse(
            request_id=request.request_id,
            is_success=True,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            order=spot_order,
        )
    
    def _decode_error(
        self, request: SeeOrderRequest, error: Exception, send_when: int, receive_when: int
    ) -> SeeOrderResponse:
        processed_when = (send_when + receive_when) // 2
        timegaps = receive_when - send_when
        
        error_str = str(error)
        if "2011" in error_str or "not found" in error_str.lower():
            error_code = "ORDER_NOT_FOUND"
        else:
            error_code = "API_ERROR"
        
        return SeeOrderResponse(
            request_id=request.request_id,
            is_success=False,
            send_when=send_when,
            receive_when=receive_when,
            processed_when=processed_when,
            timegaps=timegaps,
            error_code=error_code,
            error_message=str(error),
        )
    
    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
