# BinanceSpotGateway

Binance Spot 거래소 API와 통신하는 Gateway Controller. SpotMarketGatewayBase 인터페이스를 구현한다.

gateway_name: str = "binance"
is_realworld_gateway: bool = True
_order_request_service: OrderRequestService
_order_query_service: OrderQueryService
_balance_service: BalanceService
_market_data_service: MarketDataService

__init__() -> None
    raise EnvironmentError
    환경변수에서 BINANCE_SPOT_API_KEY, BINANCE_SPOT_API_SECRET 검증.
    없으면 EnvironmentError 발생.
    Service 계층 인스턴스 생성.

**주문 관리 메서드:**

request_limit_buy_order(request: LimitBuyOrderRequest) -> OpenSpotOrderResponse
    지정가 매수 주문 요청.
    OrderRequestService.execute_limit_buy()를 호출하여 처리.

request_limit_sell_order(request: LimitSellOrderRequest) -> OpenSpotOrderResponse
    지정가 매도 주문 요청.
    OrderRequestService.execute_limit_sell()를 호출하여 처리.

request_market_buy_order(request: MarketBuyOrderRequest) -> OpenSpotOrderResponse
    시장가 매수 주문 요청.
    OrderRequestService.execute_market_buy()를 호출하여 처리.

request_market_sell_order(request: MarketSellOrderRequest) -> OpenSpotOrderResponse
    시장가 매도 주문 요청.
    OrderRequestService.execute_market_sell()를 호출하여 처리.

request_cancel_order(request: CancelOrderRequest) -> CancelOrderResponse
    주문 취소 요청.
    OrderQueryService.cancel_order()를 호출하여 처리.

request_order_status(request: OrderStatusRequest) -> OrderStatusResponse
    주문 상태 조회.
    OrderQueryService.get_order_status()를 호출하여 처리.

**계정 정보 메서드:**

request_current_balance(request: BalanceRequest) -> BalanceResponse
    현재 잔고 조회.
    BalanceService.get_balance()를 호출하여 처리.

request_trade_history(request: TradeHistoryRequest) -> TradeHistoryResponse
    체결 내역 조회.
    OrderQueryService.get_trade_history()를 호출하여 처리.

**시장 데이터 메서드:**

request_ticker(request: TickerRequest) -> TickerResponse
    시세 정보 조회.
    MarketDataService.get_ticker()를 호출하여 처리.

request_orderbook(request: OrderbookRequest) -> OrderbookResponse
    호가 정보 조회.
    MarketDataService.get_orderbook()를 호출하여 처리.

request_candles(request: CandleRequest) -> CandleResponse
    캔들 데이터 조회.
    MarketDataService.get_candles()를 호출하여 처리.

**시스템 정보 메서드:**

request_available_markets(request: MarketListRequest) -> MarketListResponse
    거래 가능한 마켓 목록 조회.
    MarketDataService.get_available_markets()를 호출하여 처리.

request_server_time() -> ServerTimeResponse
    서버 시간 조회.
    MarketDataService.get_server_time()를 호출하여 처리.

## 사용 예시

```python
from financial_gateway.binance_spot.API.BinanceSpotGateway import BinanceSpotGateway
from financial_assets.request import LimitBuyOrderRequest

# .env에 BINANCE_SPOT_API_KEY, BINANCE_SPOT_API_SECRET 설정 필요
gateway = BinanceSpotGateway()

# 주문 요청
request = LimitBuyOrderRequest(
    address="BTCUSDT",
    price=50000.0,
    volume=0.001
)
response = gateway.request_limit_buy_order(request)

if response.is_success:
    print(f"Order placed: {response.order.order_id}")
else:
    print(f"Error: {response.error_message}")
```
