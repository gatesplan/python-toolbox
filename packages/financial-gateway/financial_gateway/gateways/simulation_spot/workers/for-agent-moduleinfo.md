# Simulation Spot Workers

Simulation Spot Gateway의 Worker 레이어. Exchange를 공유 리소스로 받아 각 Request 타입별 처리를 수행한다.

## 공통 패턴

모든 Worker는 동일한 구조를 따른다:
- `__init__(exchange)` - SpotExchange 인스턴스를 받아 저장
- `execute(request) -> response` - 동기 함수, Request 처리 후 Response 반환
- `_decode_success()` - 성공 응답 생성
- `_decode_error()` - 에러 응답 생성
- `_get_timestamp_ms()` - 현재 시뮬레이션 타임스탬프 (ms)

## CancelOrderWorker

주문 취소 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: CancelOrderRequest) -> CancelOrderResponse
    주문 취소 실행 (동기)

## CreateOrderWorker

주문 생성 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: CreateOrderRequest) -> CreateOrderResponse
    주문 생성 실행 (동기)

## ModifyOrReplaceOrderWorker

주문 수정/교체 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: ModifyOrReplaceOrderRequest) -> ModifyOrReplaceOrderResponse
    주문 수정 또는 교체 실행 (동기)

## SeeAvailableMarketsWorker

거래 가능 마켓 목록 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeAvailableMarketsRequest) -> SeeAvailableMarketsResponse
    마켓 목록 조회 실행 (동기)
    exchange.get_available_markets() 사용
    dict → MarketInfo 변환
    limit 적용

## SeeBalanceWorker

화폐 잔고 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeBalanceRequest) -> SeeBalanceResponse
    잔고 조회 실행 (동기)
    Dict[currency, Dict["balance"|"available"|"promised", Token|float]] 반환

## SeeCandlesWorker

캔들 데이터 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeCandlesRequest) -> SeeCandlesResponse
    캔들 조회 실행 (동기)
    exchange.get_candles() 사용
    pd.DataFrame 반환

## SeeHoldingsWorker

포지션 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeHoldingsRequest) -> SeeHoldingsResponse
    포지션 조회 실행 (동기)
    Dict[base, Dict["balance"|"available"|"promised", Pair|float]] 반환

## SeeOpenOrdersWorker

미체결 주문 목록 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeOpenOrdersRequest) -> SeeOpenOrdersResponse
    미체결 주문 조회 실행 (동기)
    List[SpotOrder] 반환

## SeeOrderWorker

특정 주문 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeOrderRequest) -> SeeOrderResponse
    주문 조회 실행 (동기)
    SpotOrder 반환

## SeeOrderbookWorker

호가창 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeOrderbookRequest) -> SeeOrderbookResponse
    호가창 조회 실행 (동기)
    exchange.get_orderbook() 사용
    Orderbook 반환

## SeeServerTimeWorker

서버 시간 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeServerTimeRequest) -> SeeServerTimeResponse
    서버 시간 조회 실행 (동기)
    exchange.get_current_timestamp() * 1000 사용

## SeeTickerWorker

현재가 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeTickerRequest) -> SeeTickerResponse
    현재가 조회 실행 (동기)
    exchange._market_data.get_current() 사용

## SeeTradesWorker

체결 내역 조회 Worker

exchange: SpotExchange  # 공유 리소스

execute(request: SeeTradesRequest) -> SeeTradesResponse
    체결 내역 조회 실행 (동기)
    exchange.get_trade_history() 사용
    order 필터링, limit, timestamp 내림차순 정렬 지원
