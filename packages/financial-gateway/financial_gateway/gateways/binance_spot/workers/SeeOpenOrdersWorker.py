import time
from typing import List
from simple_logger import func_logging, logger
from throttled_api.providers.binance import BinanceSpotThrottler
from financial_assets.constants import OrderStatus, OrderSide, OrderType
from financial_assets.order import SpotOrder
from financial_gateway.structures.see_open_orders import SeeOpenOrdersRequest, SeeOpenOrdersResponse


class SeeOpenOrdersWorker:
    """미체결 주문 목록 조회 Worker
    
    Binance API:
    - GET /api/v3/openOrders
    - Weight: symbol 지정 시 6, 전체 조회 시 80
    """
    
    STATUS_MAP = {
        "NEW": OrderStatus.NEW,
        "PARTIALLY_FILLED": OrderStatus.PARTIAL,
    }
    
    def __init__(self, throttler: BinanceSpotThrottler):
        self.throttler = throttler
    
    @func_logging(level="INFO", log_params=True, log_result=True)
    async def execute(self, request: SeeOpenOrdersRequest) -> SeeOpenOrdersResponse:
        send_when = self._utc_now_ms()
        
        try:
            params = self._encode(request)
            
            # Throttler의 account mixin에서 get_open_orders 메서드 사용
            from throttled_api.providers.binance.mixins import AccountMixin
            if hasattr(self.throttler, 'get_open_orders'):
                api_response = await self.throttler.get_open_orders(**params)
            else:
                # Fallback: client 직접 호출
                await self.throttler._check_and_wait(80 if not params.get('symbol') else 6)
                api_response = self.throttler.client.get_open_orders(**params)
            
            receive_when = self._utc_now_ms()
            return self._decode_success(request, api_response, send_when, receive_when)
        except Exception as e:
            receive_when = self._utc_now_ms()
            logger.error(f"SeeOpenOrdersWorker 실행 실패: {e}")
            return self._decode_error(request, e, send_when, receive_when)
    
    def _encode(self, request: SeeOpenOrdersRequest) -> dict:
        params = {}
        
        if request.address:
            symbol = request.address.to_symbol().to_compact()
            params["symbol"] = symbol
        
        return params
    
    def _decode_success(
        self, request: SeeOpenOrdersRequest, api_response: list, send_when: int, receive_when: int
    ) -> SeeOpenOrdersResponse:
        orders = []
        
        for order_data in api_response:
            order_id = str(order_data.get("orderId"))
            client_order_id = order_data.get("clientOrderId")
            status_str = order_data.get("status")
            status = self.STATUS_MAP.get(status_str, OrderStatus.NEW)
            
            price_str = order_data.get("price", "0")
            price = float(price_str) if price_str and price_str != "0.00000000" else None
            
            orig_qty = float(order_data.get("origQty", 0))
            executed_qty = float(order_data.get("executedQty", 0))
            
            order_type_str = order_data.get("type", "LIMIT")
            order_type = getattr(OrderType, order_type_str, OrderType.LIMIT)
            
            side_str = order_data.get("side", "BUY")
            side = getattr(OrderSide, side_str, OrderSide.BUY)
            
            time_ms = order_data.get("time") or send_when
            
            symbol_str = order_data.get("symbol", "BTCUSDT")
            # StockAddress 재구성 필요 - 요청에서 주어진 address 사용
            if request.address:
                stock_address = request.address
            else:
                # symbol을 파싱해서 StockAddress 생성
                from financial_assets.stock_address import StockAddress
                # 간단한 파싱 (BTC/USDT 형태로 가정)
                if "USDT" in symbol_str:
                    base = symbol_str.replace("USDT", "")
                    quote = "USDT"
                elif "BTC" in symbol_str and symbol_str != "BTC":
                    base = symbol_str.replace("BTC", "")
                    quote = "BTC"
                else:
                    base = symbol_str[:3]
                    quote = symbol_str[3:]
                
                stock_address = StockAddress(
                    archetype="crypto",
                    exchange="BINANCE",
                    tradetype="SPOT",
                    base=base,
                    quote=quote,
                    timeframe="1d"
                )
            
            spot_order = SpotOrder(
                order_id=order_id,
                stock_address=stock_address,
                side=side,
                order_type=order_type,
                price=price,
                amount=orig_qty,
                timestamp=time_ms,
                client_order_id=client_order_id,
                filled_amount=executed_qty,
                status=status,
            )
            orders.append(spot_order)
        
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
    
    def _utc_now_ms(self) -> int:
        return int(time.time() * 1000)
