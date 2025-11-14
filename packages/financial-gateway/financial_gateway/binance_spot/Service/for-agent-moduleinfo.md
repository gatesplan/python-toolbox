# Service 계층

비즈니스 워크플로우를 구현한다. Core 계층(RequestConverter, ResponseParser, APICallExecutor)을 조합하여 완전한 요청-응답 사이클을 구성한다.

## OrderRequestService
주문 요청 처리 워크플로우. Request → API 파라미터 변환 → API 호출 → Response 파싱.

execute_limit_buy(request: LimitBuyOrderRequest) -> OpenSpotOrderResponse
    지정가 매수 주문 실행.

execute_limit_sell(request: LimitSellOrderRequest) -> OpenSpotOrderResponse
    지정가 매도 주문 실행.

execute_market_buy(request: MarketBuyOrderRequest) -> OpenSpotOrderResponse
    시장가 매수 주문 실행.

execute_market_sell(request: MarketSellOrderRequest) -> OpenSpotOrderResponse
    시장가 매도 주문 실행.

## OrderQueryService
주문 조회 및 관리 워크플로우. 주문 상태, 취소, 체결 내역 조회.

cancel_order(request: CancelOrderRequest) -> CancelOrderResponse
    주문 취소 실행.

get_order_status(request: OrderStatusRequest) -> OrderStatusResponse
    주문 상태 조회.

get_trade_history(request: TradeHistoryRequest) -> TradeHistoryResponse
    체결 내역 조회.

## BalanceService
계정 정보 조회 워크플로우.

get_balance(request: BalanceRequest) -> BalanceResponse
    현재 잔고 조회.

## MarketDataService
시장 데이터 및 시스템 정보 조회 워크플로우.

get_ticker(request: TickerRequest) -> TickerResponse
    시세 정보 조회.

get_orderbook(request: OrderbookRequest) -> OrderbookResponse
    호가 정보 조회.

get_candles(request: CandleRequest) -> CandleResponse
    캔들 데이터 조회.

get_available_markets(request: MarketListRequest) -> MarketListResponse
    거래 가능한 마켓 목록 조회.

get_server_time() -> ServerTimeResponse
    서버 시간 조회.

## 공통 워크플로우 패턴

모든 Service는 다음 패턴을 따른다:

1. RequestConverter로 Request → API 파라미터 변환
2. APICallExecutor로 Binance API 호출
3. ResponseParser로 API 응답 → Response 객체 변환
4. 에러 발생 시 적절한 에러 Response 생성
