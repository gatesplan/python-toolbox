# base 모듈 구조

Gateway 시스템의 인터페이스 레이어. 모든 Gateway의 공통 인터페이스를 정의한다.

## BaseGateway
모든 Gateway의 최상위 추상 클래스. gateway_name 속성과 is_realworld_gateway 플래그를 제공한다.

gateway_name: str               # 거래소 식별자 (예: "binance", "upbit", "simulation")
is_realworld_gateway: bool      # Real world gateway 여부 (True: API 키 검증 필요, False: 검증 불필요)

__init__(gateway_name: str, is_realworld_gateway: bool) -> None
    BaseGateway 초기화. 하위 클래스에서 super().__init__()로 호출.

## SpotMarketGatewayBase
Spot 거래의 통일된 인터페이스를 정의하는 추상 클래스. 모든 Spot Gateway 구현체(Binance, Upbit, Simulation)가 이 인터페이스를 구현한다.

**주문 관리 인터페이스:**
- request_limit_buy_order(request: LimitBuyOrderRequest) -> OpenSpotOrderResponse
- request_limit_sell_order(request: LimitSellOrderRequest) -> OpenSpotOrderResponse
- request_market_buy_order(request: MarketBuyOrderRequest) -> OpenSpotOrderResponse
- request_market_sell_order(request: MarketSellOrderRequest) -> OpenSpotOrderResponse
- request_cancel_order(request: CancelOrderRequest) -> CancelOrderResponse
- request_order_status(request: OrderStatusRequest) -> OrderStatusResponse

**계정 정보 인터페이스:**
- request_current_balance(request: BalanceRequest) -> BalanceResponse
- request_trade_history(request: TradeHistoryRequest) -> TradeHistoryResponse

**시장 데이터 인터페이스:**
- request_ticker(request: TickerRequest) -> TickerResponse
- request_orderbook(request: OrderbookRequest) -> OrderbookResponse
- request_candles(request: CandleRequest) -> CandleResponse

**시스템 정보 인터페이스:**
- request_available_markets(request: MarketListRequest) -> MarketListResponse
- request_server_time() -> ServerTimeResponse

**사용 예시:**
```python
# 전략 코드 (Gateway 독립적)
class TradingStrategy:
    def __init__(self, gateway: SpotMarketGatewayBase):
        self.gateway = gateway

    def execute_trade(self):
        request = LimitBuyOrderRequest(address=..., price=..., volume=...)
        response = self.gateway.request_limit_buy_order(request)
        if response.is_success:
            # 주문 성공 처리
            pass

# Gateway 교체만으로 Sim-to-Real 전환
sim_gateway = SimulationSpotGateway(spot_exchange)
strategy = TradingStrategy(gateway=sim_gateway)  # 시뮬레이션

binance_gateway = BinanceSpotGateway()
strategy = TradingStrategy(gateway=binance_gateway)  # 실전
```
