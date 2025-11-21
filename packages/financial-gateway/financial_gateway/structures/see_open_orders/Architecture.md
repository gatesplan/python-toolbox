# see_open_orders Request/Response 설계

## 개요

활성(미체결) 주문 목록 조회 요청. 현재 체결을 기다리고 있는 모든 주문을 조회한다.

## see_open_orders Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 옵션

**마켓 필터링:**
- `address: Optional[StockAddress]` - 특정 마켓만 조회 (None이면 전체 마켓)

**개수 제한:**
- `limit: Optional[int]` - 조회 개수 (None이면 거래소 기본값 사용)
  - 거래소 기본값은 다양함 (제한 없음 또는 500 등)
  - 최대값 초과 시 거래소 최대값으로 조정

**동작:**
- `address=None`: 모든 마켓의 활성 주문 조회
- `address=StockAddress(...)`: 해당 마켓의 활성 주문만 조회

## see_open_orders Response 구조

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

**orders: List[SpotOrder]** (financial-assets)

**활성 주문 조건:**
- `status=NEW` - 아직 체결 안 됨
- `status=PARTIAL` - 부분 체결
- 즉, FILLED, CANCELED, REJECTED, EXPIRED는 제외

**정렬:**
- timestamp 내림차순 (최신 주문이 첫 번째)

**참고:**
- 활성 주문이 없으면 빈 리스트 반환
- 각 주문은 see_order와 동일한 SpotOrder 구조

### 실패 시 에러 코드

**데이터 에러:**
- `INVALID_SYMBOL` - 존재하지 않는 심볼 (address 지정 시)
- `MARKET_NOT_FOUND` - 존재하지 않는 마켓

**권한/인증 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패
- `PERMISSION_DENIED` - 주문 조회 권한 없음

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

## 설계 원칙

### SpotOrder 리스트 반환

see_order와 동일한 SpotOrder 객체 사용:
```python
from financial_assets.order import SpotOrder

# Response에서
for order in response.orders:
    print(f"{order.order_id}: {order.status.name} - {order.filled_amount}/{order.amount}")
```

**일관성 유지:**
- see_order → SpotOrder 1개
- see_open_orders → List[SpotOrder]
- 동일한 도메인 객체 사용

### 단순한 필터링

**address만 제공:**
- 특정 마켓 vs 전체 마켓
- 시간 범위는 제외 (활성 주문은 보통 최근 것만 의미 있음)

**상태 필터 불필요:**
- 모두 "open" 상태 (NEW, PARTIAL)
- 거래소 API에서 자동으로 필터링

### 최신순 정렬 보장

모든 거래소에서 일관된 정렬:
- timestamp 내림차순 (최신 → 과거)
- 거래소 API가 다른 순서를 제공하면 Gateway에서 재정렬

### limit 처리

- `limit=None`: 거래소 기본값 사용 (보통 제한 없음 또는 500)
- `limit=N`: N개 조회
- 거래소 최대값 초과 시: 로깅 경고 후 최대값으로 조정

### 거래소별 특이사항

**Upbit:**
- states="wait,watch" 사용
- done/cancel과 혼용 불가 (2021년 3월 이후)

**Bybit:**
- category="spot" 필수
- openOnly 파라미터 사용

**Coinbase:**
- status="open" 또는 "active" 사용
- 1000개 이상이면 Websocket 권장 (Gateway 구현 시 고려)

### 사용 시나리오

**1. 전체 활성 주문 확인:**
```python
response = gateway.execute(SeeOpenOrdersRequest(
    request_id="req-001",
    gateway_name="binance",
    address=None  # 전체 마켓
))

if response.is_success:
    print(f"활성 주문: {len(response.orders)}개")
    for order in response.orders:
        print(f"- {order.stock_address.base}/{order.stock_address.quote}: {order.side.name} {order.amount}")
```

**2. 특정 마켓 활성 주문:**
```python
response = gateway.execute(SeeOpenOrdersRequest(
    request_id="req-001",
    gateway_name="binance",
    address=btc_usdt_address
))

if response.is_success:
    for order in response.orders:
        print(f"{order.order_id}: {order.price} @ {order.amount}")
```

**3. 일괄 취소 준비:**
```python
# 활성 주문 조회
open_response = gateway.execute(SeeOpenOrdersRequest(...))

# 모두 취소
for order in open_response.orders:
    cancel_response = gateway.execute(CancelOrderRequest(
        request_id=generate_id(),
        gateway_name="binance",
        order=order
    ))
```
