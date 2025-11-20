# cancel_order Request/Response 설계

## 개요

주문 취소 요청의 파라미터 및 응답 구조를 정의한다. Order 객체를 직접 받아 취소를 처리하며, 거래소 API의 order_id 또는 client_order_id를 사용한다.

## cancel_order Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 주문 취소 필드

**필수:**
- `order: SpotOrder` - 취소할 주문 객체 (financial-assets)

**동작 원칙:**
- `order.client_order_id`가 있으면 이것을 우선 사용
- `order.client_order_id`가 없으면 `order.order_id` 사용
- `order.stock_address`로 마켓 정보 획득 (race condition 방지)

## cancel_order Response 구조

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

**주문 정보:**
- `order_id: str` - 거래소 발급 주문 ID
- `client_order_id: Optional[str]` - 클라이언트 주문 ID
- `status: OrderStatus` - CANCELED

**참고:** 취소 처리 시각은 BaseResponse의 `processed_when` 필드 사용

**취소 시점 체결 정보:**
- `filled_amount: float` - 취소 전 체결된 수량
- `remaining_amount: float` - 취소된 수량 (미체결분)

### 실패 시 에러 코드

**주문 상태 에러:**
- `ORDER_NOT_FOUND` - 존재하지 않는 주문
- `ORDER_ALREADY_CANCELED` - 이미 취소된 주문
- `ORDER_ALREADY_FILLED` - 이미 전체 체결된 주문
- `ORDER_NOT_CANCELABLE` - 취소 불가능한 상태 (거래소 처리 중)

**권한/인증 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패
- `PERMISSION_DENIED` - 주문 취소 권한 없음
- `NOT_YOUR_ORDER` - 다른 계정의 주문

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과
- `CANCEL_REQUEST_TIMEOUT` - 취소 요청 타임아웃

**특수 상황:**
- `CANCEL_STATUS_UNKNOWN` - 서버 오류로 취소 상태 불명 (재조회 필요)

## 설계 원칙

### Order 객체를 직접 받는 이유

**안전성:**
- order_id와 stock_address를 함께 전달하여 잘못된 마켓 취소 방지
- Order 객체의 유효성이 이미 검증됨

**편의성:**
```python
# 기존 방식 (X)
cancel_req = CancelOrderRequest(
    request_id="...",
    gateway_name="binance",
    order_id="12345",
    address=StockAddress(...)
)

# Order 객체 방식 (O)
cancel_req = CancelOrderRequest(
    request_id="...",
    gateway_name="binance",
    order=my_order  # 모든 정보 포함
)
```

**일관성:**
- create_order → SpotOrder 생성
- SpotOrder → cancel_order Request
- 주문 생명주기 전체에서 Order 객체 중심

### client_order_id 우선 사용

**거래소 지원:**
- Binance: `origClientOrderId` 사용 가능, 성능은 `orderId`보다 약간 느림
- Upbit: `identifier` 사용 가능
- Coinbase: `client:` prefix로 사용 가능

**우선 순위:**
1. `order.client_order_id` 있으면 → 이것 사용
2. 없으면 → `order.order_id` 사용

**이유:**
- client_order_id는 사용자가 명시적으로 지정한 ID
- 사용자의 추적/관리 의도 존중

### 취소 불가능한 상태 처리

**거래소 처리 중인 주문:**
- 일부 거래소는 체결 처리 중인 주문을 취소할 수 없음
- 에러 코드: `ORDER_NOT_CANCELABLE`
- 사용자가 재시도하거나 상태 조회 후 판단

**전체 체결 완료:**
- 이미 전체 체결된 주문은 취소 불가
- 에러 코드: `ORDER_ALREADY_FILLED`
- 정상적인 상황이므로 에러가 아닌 정보성 응답

**이미 취소됨:**
- 중복 취소 요청 감지
- 에러 코드: `ORDER_ALREADY_CANCELED`
- Idempotent 처리: 성공으로 간주할 수도 있음 (Gateway 구현 선택)

### 부분 체결 후 취소

**시나리오:**
```
주문: BTC 1.0 매수
상태: 0.3 체결, 0.7 미체결
취소: 미체결 0.7 취소
```

**응답:**
- `filled_amount: 0.3` - 취소 전 체결량
- `remaining_amount: 0.7` - 취소된 수량
- `status: CANCELED`

**사용자 처리:**
- 체결된 0.3은 Ledger에 기록
- 취소된 0.7은 자금 반환

### 서버 오류 시 UNKNOWN 상태

**시나리오:**
- 취소 요청 전송 → 서버 오류 (5XX)
- 실제 취소 여부 불명

**응답:**
- `is_success: false`
- `error_code: CANCEL_STATUS_UNKNOWN`

**사용자 처리:**
1. `see_order` Request로 주문 상태 재조회
2. 상태 확인 후 판단:
   - CANCELED → 취소 완료
   - FILLED → 전체 체결
   - PARTIAL/PENDING → 재시도 또는 포기

## 거래소별 매핑 예시

### Binance

**Request 변환:**
```python
# CancelOrderRequest → Binance API params
{
    "symbol": order.stock_address.to_binance_symbol(),  # "BTCUSDT"
    "origClientOrderId": order.client_order_id,  # 우선
    "orderId": order.order_id,  # 대체
    "timestamp": current_timestamp_ms()
}
```

**Response 변환:**
```python
# Binance API response → CancelOrderResponse
{
    "orderId": 12345,
    "clientOrderId": "my-order-123",
    "status": "CANCELED",
    "executedQty": "0.3",
    "cummulativeQuoteQty": "15000",
    "transactTime": 1699999999000
}

# → CancelOrderResponse
CancelOrderResponse(
    request_id=request_id,
    is_success=True,
    send_when=send_when,
    receive_when=receive_when,
    processed_when=1699999999000,  # transactTime
    timegaps=receive_when - send_when,
    order_id="12345",
    client_order_id="my-order-123",
    status=OrderStatus.CANCELED,
    filled_amount=0.3,
    remaining_amount=0.7  # origQty - executedQty
)
```

### Upbit

**Request 변환:**
```python
# CancelOrderRequest → Upbit API params
{
    "uuid": order.order_id,  # 또는
    "identifier": order.client_order_id  # 우선
}
```

**Response 변환:**
```python
# Upbit API response → CancelOrderResponse
{
    "uuid": "abc-123",
    "side": "bid",
    "ord_type": "limit",
    "state": "cancel",
    "volume": "1.0",
    "executed_volume": "0.3",
    "remaining_volume": "0.7",
    "created_at": "2024-11-20T10:00:00+09:00"
}

# → CancelOrderResponse
CancelOrderResponse(
    request_id=request_id,
    is_success=True,
    send_when=send_when,
    receive_when=receive_when,
    processed_when=parse_upbit_timestamp("2024-11-20T10:00:00+09:00"),
    timegaps=receive_when - send_when,
    order_id="abc-123",
    client_order_id=order.client_order_id,  # Upbit는 응답에 포함 안 함, Request에서 복사
    status=OrderStatus.CANCELED,
    filled_amount=0.3,
    remaining_amount=0.7
)
```

### Coinbase

**Request 변환:**
```python
# CancelOrderRequest → Coinbase API
DELETE /orders/{order_id}?product_id={product_id}

# Path: order.client_order_id (client: prefix) 또는 order.order_id
# Query: order.stock_address.to_coinbase_product_id()  # "BTC-USD"
```

**Response 변환:**
```python
# Coinbase API response (단순 ID 반환)
"12345"

# 추가 조회 필요 → see_order로 상세 정보 획득
# → CancelOrderResponse
CancelOrderResponse(
    request_id=request_id,
    is_success=True,
    send_when=send_when,
    receive_when=receive_when,
    processed_when=(send_when + receive_when) // 2,  # 서버 시각 없으면 중간값
    timegaps=receive_when - send_when,
    order_id="12345",
    client_order_id=order.client_order_id,
    status=OrderStatus.CANCELED,
    filled_amount=None,  # 조회 필요
    remaining_amount=None  # 조회 필요
)
```

**참고:** Coinbase는 취소 응답이 단순하므로, Gateway 구현 시 `see_order`를 추가로 호출하여 상세 정보를 채울 수 있습니다.

## 다음 구현 단계

1. `CancelOrderRequest` dataclass 구현
2. `CancelOrderResponse` dataclass 구현
3. `__init__.py`에 export 추가
4. Gateway Worker 구현 시 이 문서 참조
