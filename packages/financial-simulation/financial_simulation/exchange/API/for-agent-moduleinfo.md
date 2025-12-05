# SpotExchange

Spot 거래소 API Layer. 외부 시스템의 진입점으로 주문 생성, 취소, 잔고 조회, 시장 틱 처리 등 전체 거래소 기능 제공.

## 속성

_portfolio: Portfolio
_orderbook: OrderBook
_order_history: OrderHistory
_market_data: MarketData
_order_validator: OrderValidator
_order_executor: OrderExecutor
_position_manager: PositionManager
_market_data_service: MarketDataService
_trade_simulation: TradeSimulation
_trade_history: list[SpotTrade]
_trade_index_by_order: dict[str, list[int]]    # order_id 기반 거래 내역 인덱스 (O(1) 조회)
_initial_balance: float
_quote_currency: str
_maker_fee_ratio: float
_taker_fee_ratio: float

## Symbol 지원

모든 symbol 관련 메서드는 `str | Symbol` 타입 지원:
- str: "BTC/USDT" (slash 형식)
- Symbol: Symbol("BTC/USDT") 또는 Symbol("BTC-USDT")

내부 변환:
- MarketData/OrderBook 호출 시: str(symbol) → "BTC/USDT"
- Portfolio 호출 시: symbol.to_dash() → "BTC-USDT"

## 메서드

### 초기화

__init__(initial_balance: float, market_data: MarketData, maker_fee_ratio=0.001, taker_fee_ratio=0.002, quote_currency="USDT")
    거래소 초기화. Portfolio에 초기 자금 입금하고 모든 Service/Core 컴포넌트 생성.

### 주문 관리

place_order(order: SpotOrder) -> list[SpotTrade]
    raise ValueError
    주문 실행 (잔고/자산 부족 시 ValueError)

cancel_order(order_id: str) -> None
    raise KeyError
    미체결 주문 취소 (주문 없으면 KeyError)

get_order(order_id: str) -> SpotOrder | None
    개별 주문 조회 (미체결 + 이력)

get_order_status(order_id: str) -> OrderStatus | None
    주문 상태 조회

get_open_orders(symbol: str | Symbol | None) -> list[SpotOrder]
    미체결 주문 조회

get_trade_history(symbol: str | Symbol | None) -> list[SpotTrade]
    거래 내역 조회

get_trades_by_order_id(order_id: str) -> list[SpotTrade]
    order_id로 거래 내역 조회 (O(1) + O(k) 성능, 인덱스 기반)

### 잔고 조회 (Currency)

get_balance(currency: str | None) -> float | dict[str, float]
    Currency 잔고 조회 (사용 가능 잔고)
    NOTE: Quote Currency(USDT, USD) 전용. Base Asset(BTC, ETH)는 get_position() 사용

get_locked_balance(currency: str) -> float
    잠긴 잔고 조회 (미체결 매수 주문용)

get_currencies() -> list[str]
    보유 화폐 목록 조회

### 포지션 조회 (Position)

get_positions() -> dict[str, float]
    보유 포지션 조회 {ticker: amount}

get_position(symbol: str | Symbol) -> float
    단일 포지션 수량 조회 (없으면 0.0)

get_available_position(symbol: str | Symbol) -> float
    사용 가능 포지션 조회 (매도 가능 수량)

get_locked_position(symbol: str | Symbol) -> float
    잠긴 포지션 조회 (미체결 매도 주문용)

get_position_value(symbol: str | Symbol) -> dict[str, float]
    특정 포지션의 상세 가치 정보 (book_value, market_value, pnl, pnl_ratio)

get_total_value() -> float
    총 자산 가치 (quote_currency 기준)

get_statistics() -> dict[str, float]
    포트폴리오 통계 조회 (total_value, total_pnl, total_pnl_ratio, currency_value, position_value, allocation)

### 시장 데이터

get_current_timestamp() -> int | None
    현재 시장 타임스탬프 조회

get_current_price(symbol: str | Symbol) -> float | None
    현재 시장 가격 조회

get_orderbook(symbol: str | Symbol, depth=20)
    OHLC 기반 더미 호가창 생성 (Gateway API 호환용)

get_available_markets() -> list[dict]
    마켓 목록 조회 (Gateway API 호환용)

get_candles(symbol: str | Symbol, start_time=None, end_time=None, limit=None)
    과거 캔들 데이터 조회 (Gateway API 호환용)

### 시뮬레이션 제어

step() -> bool
    다음 시장 틱으로 이동 (계속 가능하면 True, 종료면 False)

reset() -> None
    거래소 초기화

is_finished() -> bool
    시뮬레이션 종료 여부

## 주요 흐름

### 주문 생성

1. place_order(order) 호출 (order는 gateway에서 이미 생성됨)
2. OrderValidator.validate_order(order) 거래소 컨텍스트 검증
3. OrderExecutor.execute_order(order) 체결 처리
4. 반환된 SpotTrade들을 _trade_history에 추가
5. _trade_index_by_order 업데이트 (O(1) 조회용)
6. SpotTrade 리스트 반환

### 시장 틱 처리

1. step() 호출
2. MarketData.step() 커서 이동
3. OrderBook.expire_orders(current_timestamp) GTD 만료 처리
4. 만료된 주문들의 자산 잠금 해제
5. 시뮬레이션 종료 여부 반환

## 사용 예시

```python
# 초기화
exchange = SpotExchange(
    initial_balance=100000.0,
    market_data=market_data,
    maker_fee_ratio=0.001,
    taker_fee_ratio=0.002,
    quote_currency="USDT"
)

# Symbol 객체로 조회
from financial_assets.symbol import Symbol
btc_symbol = Symbol("BTC/USDT")
price = exchange.get_current_price(btc_symbol)  # Symbol 객체
price2 = exchange.get_current_price("BTC/USDT")  # str도 동일하게 동작

# 주문 실행
order = SpotOrder(...)
trades = exchange.place_order(order)

# order_id로 거래 내역 조회 (O(1) 성능)
order_trades = exchange.get_trades_by_order_id(order.order_id)

# 잔고 조회
usdt_balance = exchange.get_balance("USDT")
all_balances = exchange.get_balance()

# 포지션 조회
btc_amount = exchange.get_position("BTC/USDT")  # 또는 Symbol("BTC/USDT")
btc_available = exchange.get_available_position("BTC/USDT")
btc_locked = exchange.get_locked_position("BTC/USDT")

# 잠금 조회
usdt_locked = exchange.get_locked_balance("USDT")

# 시장 진행
while not exchange.is_finished():
    current_price = exchange.get_current_price("BTC/USDT")
    exchange.step()
```

## 로깅

- 초기화: INFO 레벨, 파라미터 로깅
- place_order: INFO 레벨, 파라미터 및 결과 로깅
- cancel_order: INFO 레벨, 파라미터 로깅
- step, reset: INFO 레벨

## 의존성

Core:
- Portfolio: 잔고 및 자산 관리
- OrderBook: 미체결 주문 관리
- OrderHistory: 주문 이력 관리
- MarketData: 시장 데이터 및 시간 관리

Service:
- OrderValidator: 주문 검증
- OrderExecutor: 주문 실행
- PositionManager: 포지션 통계
- MarketDataService: 시장 정보 조회

External:
- TradeSimulation: 체결 시뮬레이션 (tradesim 모듈)

## 설계 원칙

- API Layer는 완성된 도메인 객체(SpotOrder) 수신하여 처리
- 객체 생성 및 변환은 gateway 책임 (관심사 분리)
- 모든 비즈니스 로직은 Service/Core Layer에 위임
- Symbol 객체와 str 모두 지원하여 유연성 제공
- 상태 변경 이력 추적 (trade_history, order_history)
- 성능 최적화: order_id 기반 거래 조회는 O(1) 인덱스 사용
