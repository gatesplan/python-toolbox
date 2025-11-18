# throttled_api.providers.upbit

Upbit Spot API Provider - Wrapper 패턴으로 Upbit 클라이언트에 throttle 적용

## 개요

Upbit Spot API의 rate limit을 관리하는 throttler. 기존 Upbit 클라이언트(upbit-client, pyupbit 등)를 감싸서 rate limit 체크만 수행하는 wrapper 패턴.

## Rate Limit 정책 (Upbit Spot API)

- **QUOTATION** (시세 조회): 초당 10회, 분당 600회
- **EXCHANGE_ORDER** (주문): 초당 8회, 분당 200회
- **EXCHANGE_NON_ORDER** (주문 외 거래): 초당 30회, 분당 900회

## endpoints.py

엔드포인트별 카테고리 정의 모듈

```
UPBIT_ENDPOINT_CATEGORIES: Dict[Tuple[str, str], EndpointCategory]
    (method, endpoint) -> category 매핑

get_endpoint_category(method: str, endpoint: str) -> EndpointCategory
    엔드포인트의 카테고리 조회
    raise KeyError  # 알 수 없는 엔드포인트

is_order_endpoint(method: str, endpoint: str) -> bool
    주문 관련 엔드포인트인지 판단

is_quotation_endpoint(method: str, endpoint: str) -> bool
    시세 조회 엔드포인트인지 판단
```

**주요 엔드포인트**:
- QUOTATION: /v1/market/all, /v1/ticker, /v1/candles/*, /v1/orderbook, /v1/trades/ticks
- EXCHANGE_ORDER: POST /v1/orders, DELETE /v1/order
- EXCHANGE_NON_ORDER: GET /v1/accounts, GET /v1/order, GET /v1/orders, /v1/deposits, /v1/withdraws

## UpbitSpotThrottler

BaseThrottler를 상속한 Upbit Spot API 전용 throttler

```
client: Any                               # 주입받은 Upbit 클라이언트
warning_threshold: float                  # 서버/로컬 사용량 차이 경고 임계값
quotation_pipelines: List[Pipeline]       # QUOTATION 카테고리 Pipeline들
exchange_order_pipelines: List[Pipeline]  # EXCHANGE_ORDER 카테고리 Pipeline들
exchange_non_order_pipelines: List[Pipeline]  # EXCHANGE_NON_ORDER 카테고리 Pipeline들

__init__(client, warning_threshold=0.2)
    client: 기존 Upbit 클라이언트 객체
    warning_threshold: 서버/로컬 사용량 차이 경고 임계값

    6개 Pipeline 초기화:
    - QUOTATION_1S: SlidingWindow(10, 1초, max_soft_delay=0.1)
    - QUOTATION_1M: FixedWindow(600, 60초, max_soft_delay=0.3)
    - EXCHANGE_ORDER_1S: SlidingWindow(8, 1초, max_soft_delay=0.1)
    - EXCHANGE_ORDER_1M: FixedWindow(200, 60초, max_soft_delay=0.3)
    - EXCHANGE_NON_ORDER_1S: SlidingWindow(30, 1초, max_soft_delay=0.1)
    - EXCHANGE_NON_ORDER_1M: FixedWindow(900, 60초, max_soft_delay=0.3)

async _check_and_wait(cost: int, category: EndpointCategory) -> None
    카테고리별 Pipeline에 대해 throttle 체크 및 대기
    해당 카테고리의 Pipeline들만 선택적으로 체크
```

## Mixins

### QuotationMixin (quotation.py)

시세 조회 API 메서드 제공

```
get_market_all(is_details=False) -> dict
    GET /v1/market/all
    마켓 코드 조회

get_candles_minutes(unit, market, to=None, count=1) -> list
    GET /v1/candles/minutes/{unit}
    분봉 캔들 조회 (unit: 1,3,5,10,15,30,60,240)

get_candles_days(market, to=None, count=1, converting_price_unit=None) -> list
    GET /v1/candles/days
    일봉 캔들 조회

get_candles_weeks(market, to=None, count=1) -> list
    GET /v1/candles/weeks
    주봉 캔들 조회

get_candles_months(market, to=None, count=1) -> list
    GET /v1/candles/months
    월봉 캔들 조회

get_ticker(markets: List[str]) -> list
    GET /v1/ticker
    현재가 정보 조회

get_orderbook(markets: List[str]) -> list
    GET /v1/orderbook
    호가 정보 조회

get_trades_ticks(market, to=None, count=1, cursor=None, days_ago=None) -> list
    GET /v1/trades/ticks
    최근 체결 내역 조회
```

### AccountMixin (account.py)

계좌 정보 조회 API 메서드 제공

```
get_accounts() -> list
    GET /v1/accounts
    전체 계좌 조회

get_api_keys() -> list
    GET /v1/api_keys
    API 키 리스트 조회
```

### TradingMixin (trading.py)

주문 관련 API 메서드 제공

```
create_order(market, side, ord_type, volume=None, price=None, identifier=None) -> dict
    POST /v1/orders
    주문하기 (EXCHANGE_ORDER 카테고리)

cancel_order(uuid=None, identifier=None) -> dict
    DELETE /v1/order
    주문 취소 (EXCHANGE_ORDER 카테고리)

get_order(uuid=None, identifier=None) -> dict
    GET /v1/order
    개별 주문 조회 (EXCHANGE_NON_ORDER 카테고리)

get_orders(market=None, uuids=None, identifiers=None, state=None, states=None, page=1, limit=100, order_by="desc") -> list
    GET /v1/orders
    주문 리스트 조회 (EXCHANGE_NON_ORDER 카테고리)

get_orders_chance(market) -> dict
    GET /v1/orders/chance
    주문 가능 정보

get_orders_open(market=None, page=1, limit=100, order_by="desc") -> list
    GET /v1/orders/open
    미체결 주문 조회

get_orders_closed(market=None, state=None, start_time=None, end_time=None, page=1, limit=100, order_by="desc") -> list
    GET /v1/orders/closed
    종료된 주문 조회
```

### DepositsMixin (deposits.py)

입금 관련 API 메서드 제공

```
get_deposits(currency=None, state=None, uuids=None, txids=None, limit=100, page=1, order_by="desc") -> list
    GET /v1/deposits
    입금 리스트 조회

get_deposit(uuid=None, txid=None, currency=None) -> dict
    GET /v1/deposit
    개별 입금 조회

generate_coin_address(currency) -> dict
    POST /v1/deposits/generate_coin_address
    입금 주소 생성 요청

get_coin_addresses() -> list
    GET /v1/deposits/coin_addresses
    전체 입금 주소 조회

get_coin_address(currency) -> dict
    GET /v1/deposits/coin_address
    개별 입금 주소 조회

create_krw_deposit(amount) -> dict
    POST /v1/deposits/krw
    원화 입금하기
```

### WithdrawalsMixin (withdrawals.py)

출금 관련 API 메서드 제공

```
get_withdraws(currency=None, state=None, uuids=None, txids=None, limit=100, page=1, order_by="desc") -> list
    GET /v1/withdraws
    출금 리스트 조회

get_withdraw(uuid=None, txid=None, currency=None) -> dict
    GET /v1/withdraw
    개별 출금 조회

get_withdraws_chance(currency) -> dict
    GET /v1/withdraws/chance
    출금 가능 정보

withdraw_coin(currency, amount, address, secondary_address=None, transaction_type="default") -> dict
    POST /v1/withdraws/coin
    코인 출금하기

withdraw_krw(amount) -> dict
    POST /v1/withdraws/krw
    원화 출금하기
```

## 사용 예시

### 기본 사용

```python
from throttled_api.providers.upbit import UpbitSpotThrottler
from upbit.client import Upbit  # upbit-client 예시

# Upbit 클라이언트 생성
upbit_client = Upbit(access_key="...", secret_key="...")

# Throttler로 감싸기
throttler = UpbitSpotThrottler(client=upbit_client)

# throttler를 통해 요청
response = await throttler.get_ticker(markets=["KRW-BTC"])
```

### 시세 조회

```python
# 현재가 조회
ticker = await throttler.get_ticker(markets=["KRW-BTC", "KRW-ETH"])

# 분봉 캔들 조회
candles = await throttler.get_candles_minutes(
    unit=1,
    market="KRW-BTC",
    count=10
)

# 호가 조회
orderbook = await throttler.get_orderbook(markets=["KRW-BTC"])
```

### 주문

```python
# 지정가 매수 주문
order = await throttler.create_order(
    market="KRW-BTC",
    side="bid",
    ord_type="limit",
    volume="0.01",
    price="50000000"
)

# 주문 취소
cancel_result = await throttler.cancel_order(uuid=order["uuid"])

# 미체결 주문 조회
open_orders = await throttler.get_orders_open(market="KRW-BTC")
```

### 이벤트 리스너 등록

```python
def on_threshold_event(event):
    print(f"[ALERT] {event.timeframe}: {event.remaining_rate:.1%} remaining")

throttler.add_event_listener(on_threshold_event)

# 사용량이 80% 도달 시 이벤트 발행
# 출력 예: [ALERT] QUOTATION_1M: 19.8% remaining
```

## 테스트 커버리지

- endpoints.py: 6 tests
- UpbitSpotThrottler.py: 11 tests (asyncio 백엔드)
- 총 17 tests 통과

**테스트 항목**:
- 엔드포인트 카테고리 매핑
- 카테고리별 독립적 rate limiting
- Quotation / Trading / Account API 호출
- 다중 Pipeline 동시 관리
- Mock 클라이언트 wrapper 검증

## 주의사항

1. **Wrapper 패턴**: 직접 HTTP 요청하지 않음, client 주입 필요
2. **카테고리 기반 제한**: Upbit은 weight가 아닌 카테고리별 횟수 제한
3. **클라이언트 호환성**: upbit-client, pyupbit, aiopyupbit 등 지원
4. **계정 기반 제한**: Upbit rate limit은 API 키가 아닌 계정 기반
5. **헤더 의존성**: Remaining-Req 헤더로 남은 요청 수 확인 가능

## 향후 개선

- [ ] Remaining-Req 헤더 파싱 및 drift 체크
- [ ] Upbit Futures API 지원
- [ ] WebSocket API throttling 지원
- [ ] 더 많은 클라이언트 패턴 지원
