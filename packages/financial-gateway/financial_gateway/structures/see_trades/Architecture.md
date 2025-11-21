# see_trades Request/Response 설계

## 개요

체결 내역 조회 요청. 특정 주문의 체결 내역 또는 특정 마켓의 모든 체결 내역을 조회한다.

## see_trades Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 대상

**마켓 지정:**
- `address: StockAddress` - 조회할 마켓 주소 (financial-assets)

**주문 필터링 (선택):**
- `order: Optional[SpotOrder]` - 특정 주문의 체결만 조회 (None이면 마켓 전체 조회)

**동작:**
- `order=None`: 해당 마켓의 모든 체결 내역 조회
- `order=SpotOrder(...)`: 해당 주문의 체결 내역만 조회

### 조회 옵션

**시간 범위:**
- `start_time: Optional[int]` - 조회 시작 시각 (UTC ms, None이면 제한 없음)
- `end_time: Optional[int]` - 조회 종료 시각 (UTC ms, None이면 제한 없음)

**개수 제한:**
- `limit: Optional[int]` - 조회 개수 (None이면 거래소 기본값 사용)
  - 기본값은 거래소마다 다름 (Binance: 500, Upbit: 100 등)
  - 최대값 초과 시 거래소 최대값으로 조정

**정렬 순서:**
- 최신순 정렬 (timestamp 내림차순)
- 거래소 API가 다른 순서를 제공하더라도 Gateway에서 정렬 보장

## see_trades Response 구조

### 공통 필드 (Response Base)
- `request_id`: 원본 요청 참조
- `is_success`: 성공/실패
- `send_when`: UTC ms
- `receive_when`: UTC ms
- `processed_when`: UTC ms (서버 처리 시각)
- `timegaps`: ms
- `error_code`: 에러 코드 (실패 시)
- `error_message`: 에러 메시지 (실패 시)

### 성공 시 응답 데이터

**trades: List[SpotTrade]** (financial-assets)

SpotTrade 구조:
- `trade_id: str` - 거래소 발급 체결 ID
- `order: Order` - 해당 체결의 주문 정보
- `pair: Pair` - 체결된 거래 쌍 (자산 + 가격)
- `timestamp: int` - 체결 시각 (UTC ms)
- `fee: Optional[Token]` - 수수료 (심볼, 금액)
- `stock_address: StockAddress` - 자산 주소 (order에서 자동 설정)
- `side: OrderSide` - 거래 방향 (order에서 자동 설정)

**정렬:**
- timestamp 내림차순 (최신 체결이 첫 번째)

**참고:**
- 평균 체결가는 사용자가 직접 계산 (sum(pair.value.amount) / sum(pair.asset.amount))
- 체결 내역이 없으면 빈 리스트 반환

### 실패 시 에러 코드

**데이터 에러:**
- `INVALID_SYMBOL` - 존재하지 않는 심볼
- `MARKET_NOT_FOUND` - 존재하지 않는 마켓
- `ORDER_NOT_FOUND` - 존재하지 않는 주문 (order 지정 시)

**권한/인증 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패
- `PERMISSION_DENIED` - 체결 내역 조회 권한 없음

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

**시간 범위 에러:**
- `INVALID_TIME_RANGE` - 잘못된 시간 범위 (start_time > end_time)
- `TIME_RANGE_TOO_LARGE` - 시간 범위가 너무 큼 (거래소 제한 초과)

## 설계 원칙

### SpotTrade 객체 반환

financial-assets의 SpotTrade 타입 사용:
```python
from financial_assets.trade import SpotTrade

# Response에서
for trade in response.trades:
    print(f"{trade.trade_id}: {trade.pair.asset.amount} @ {trade.pair.value.amount / trade.pair.asset.amount}")
```

도메인 객체 사용으로 일관성 유지:
- Order, Pair, Token과 동일한 패턴
- Gateway 외부에서도 SpotTrade 타입 재사용 가능

### 두 가지 조회 모드

**1. 특정 주문의 체결 내역:**
```python
request = SeeTradesRequest(
    request_id="req-001",
    gateway_name="binance",
    address=stock_address,
    order=my_order  # 특정 주문
)
```

**2. 마켓 전체 체결 내역:**
```python
request = SeeTradesRequest(
    request_id="req-001",
    gateway_name="binance",
    address=stock_address,
    order=None  # 전체 조회
)
```

### order → order.order_id 변환

Request의 order 필드는 SpotOrder 객체:
- `order.order_id` 또는 `order.client_order_id`를 API 파라미터로 사용
- see_order, cancel_order와 동일한 패턴

### 최신순 정렬 보장

모든 거래소에서 일관된 정렬 순서:
- timestamp 내림차순 (최신 → 과거)
- 거래소 API가 다른 순서를 제공하면 Gateway에서 재정렬

### 시간 범위 제한

거래소별로 조회 가능한 시간 범위 제한이 다름:
- Binance: 최대 24시간
- Upbit: 제한 없음 (하지만 성능 고려)
- Worker에서 거래소 제한 확인 후 적절히 처리

### limit 처리

- `limit=None`: 거래소 기본값 사용
- `limit=N`: N개 조회
- 거래소 최대값 초과 시: 로깅 경고 후 최대값으로 조정

### Trade 생성 시 Order 정보

SpotTrade는 Order 객체를 포함:
- 거래소 API가 제공하는 정보로 Order 재구성
- 최소 필드만 채우고 나머지는 None/기본값 사용 가능
- 완전한 Order 정보가 필요하면 see_order로 별도 조회

**예시:**
```python
# 거래소 API에서 받은 체결 정보
api_trade = {
    "id": "12345",
    "orderId": "67890",
    "symbol": "BTCUSDT",
    "price": "50000.0",
    "qty": "0.1",
    "commission": "0.0001",
    "commissionAsset": "BTC",
    "time": 1699999999000
}

# SpotTrade 생성
trade = SpotTrade(
    trade_id="12345",
    order=SpotOrder(
        order_id="67890",
        stock_address=stock_address,
        side=OrderSide.BUY,
        order_type=OrderType.LIMIT,
        # ... 최소 필수 필드만
    ),
    pair=Pair(
        asset=Token("BTC", 0.1),
        value=Token("USDT", 5000.0)
    ),
    timestamp=1699999999000,
    fee=Token("BTC", 0.0001)
)
```
