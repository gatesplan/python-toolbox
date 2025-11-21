# see_order Request/Response 설계

## 개요

특정 주문의 현재 상태를 조회하는 요청. 주문 생성 후 체결 확인, 주문 추적, 상태 모니터링에 사용한다.

## see_order Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 대상

**주문 객체:**
- `order: SpotOrder` - 조회할 주문 객체 (financial-assets)

**동작 원칙:**
- `order.client_order_id`가 있으면 우선 사용
- `order.client_order_id`가 없으면 `order.order_id` 사용
- `order.stock_address`로 마켓 정보 획득 (Binance 등에서 필요)

**cancel_order와 동일한 패턴:**
- 주문 객체를 직접 전달
- ID 우선순위 동일
- 안전성 및 편의성 확보

## see_order Response 구조

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

**order: SpotOrder** (financial-assets, 업데이트된 주문 정보)

**see_order에서 업데이트되는 필드:**
- `status`: OrderStatus (NEW, PARTIAL, FILLED, CANCELED 등)
- `filled_amount`: 체결된 수량

**변경되지 않는 필드:**
- `order_id`, `client_order_id`
- `stock_address`
- `side`, `order_type`
- `price`, `amount` (원래 주문 가격/수량)
- `timestamp` (주문 생성 시각)
- `fee_rate`, `min_trade_amount`, `time_in_force`, `expire_timestamp`, `stop_price`

**참고:**
- SpotOrder에는 `average_price` 필드가 없음 (평균 체결가는 see_trades에서 확인)
- SpotOrder에는 `updated_at` 필드가 없음 (timestamp 필드 사용)
- SpotOrder에는 `trades` 필드가 없음 (체결 내역은 see_trades Request로 조회)

### 실패 시 에러 코드

**주문 상태 에러:**
- `ORDER_NOT_FOUND` - 존재하지 않는 주문
- `ORDER_EXPIRED` - 만료된 주문 (기록 삭제됨)

**권한/인증 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패
- `PERMISSION_DENIED` - 주문 조회 권한 없음
- `NOT_YOUR_ORDER` - 다른 계정의 주문

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

## 설계 원칙

### Order 객체 입출력

**주문 생명주기 전체에서 Order 객체 중심:**
1. create_order → SpotOrder 생성
2. see_order → SpotOrder 업데이트 (상태, 체결량)
3. cancel_order → SpotOrder 사용

**Request → Order 객체:**
```python
# 주문 생성 후
created_order = create_order_response.order

# 상태 조회
see_order_request = SeeOrderRequest(
    request_id="req-002",
    gateway_name="binance",
    order=created_order  # Order 객체 그대로 전달
)
```

**Response → 업데이트된 Order 객체:**
```python
response = gateway.execute(see_order_request)

if response.is_success:
    updated_order = response.order

    if updated_order.status == OrderStatus.FILLED:
        print("주문 완전 체결")
    elif updated_order.status == OrderStatus.PARTIAL:
        print(f"부분 체결: {updated_order.filled_amount}")
```

### client_order_id 우선 사용

**거래소 지원:**
- Binance: `origClientOrderId` 사용 가능
- Upbit: `identifier` 사용 가능
- Bybit: `orderLinkId` 사용 가능
- Coinbase: `client:` prefix 사용 가능

**우선 순위:**
1. `order.client_order_id` 있으면 → 이것 사용
2. 없으면 → `order.order_id` 사용

**이유:**
- 사용자가 명시적으로 지정한 ID 존중
- 추적/관리 용이
- cancel_order와 동일한 패턴

### 주문 상태 매핑

거래소별 상태값을 OrderStatus enum으로 통일:

| OrderStatus | Binance | Upbit | Bybit | Coinbase |
|-------------|---------|-------|-------|----------|
| NEW | NEW | wait | New | open |
| PARTIAL | PARTIALLY_FILLED | wait (부분체결) | PartiallyFilled | open (부분체결) |
| FILLED | FILLED | done | Filled | done |
| CANCELED | CANCELED | cancel | Cancelled | done (cancelled) |
| REJECTED | REJECTED | - | Rejected | - |
| EXPIRED | EXPIRED | - | - | - |
