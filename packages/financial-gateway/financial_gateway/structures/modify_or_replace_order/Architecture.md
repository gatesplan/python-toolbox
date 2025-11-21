# modify_or_replace_order Request/Response 설계

## 개요

기존 주문을 수정하거나 취소 후 재생성하는 요청. 거래소가 직접 수정(amend)을 지원하면 수정하고, 지원하지 않으면 취소 후 새 주문을 생성한다.

## modify_or_replace_order Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 기존 주문
- `original_order: SpotOrder` - 수정할 주문 (order_id로 식별)

### 새 주문 파라미터 (Optional - None이면 변경 안 함)

**주문 기본 정보:**
- `side: Optional[OrderSide]` - BUY / SELL
- `order_type: Optional[OrderType]` - LIMIT, MARKET, STOP_LOSS 등

**수량/가격:**
- `asset_quantity: Optional[float]` - 주문 수량
- `price: Optional[float]` - 주문 가격
- `quote_quantity: Optional[float]` - 인용 자산 수량 (시장가 매수 시)
- `stop_price: Optional[float]` - 트리거 가격

**체결 조건:**
- `time_in_force: Optional[TimeInForce]` - GTC, IOC, FOK
- `post_only: Optional[bool]` - Maker 전용 주문 여부

**자전거래 방지:**
- `self_trade_prevention: Optional[SelfTradePreventionMode]` - NONE, CANCEL_MAKER, CANCEL_TAKER, CANCEL_BOTH

**클라이언트 주문 ID:**
- `client_order_id: Optional[str]` - 사용자 정의 주문 ID

**동작 원칙:**
- None이 아닌 파라미터만 수정 대상
- 거래소가 amend 지원: 해당 필드만 수정
- 거래소가 amend 미지원: 기존 주문 취소 후 새 주문 생성

## modify_or_replace_order Response 구조

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
- `order_id: str` - 주문 ID (amend 시 유지, replace 시 새 ID)
- `client_order_id: str` - 클라이언트 주문 ID
- `status: OrderStatus` - NEW, PARTIALLY_FILLED, FILLED, CANCELED, REJECTED 등

**체결 정보 (일부 체결 상태였던 경우):**
- `trades: Optional[List[Trade]]` - 기존 체결 내역 (replace 시에만, amend 시 없음)

### 실패 시 에러 코드

**주문 상태 에러:**
- `ORDER_NOT_FOUND` - 존재하지 않는 주문
- `ORDER_ALREADY_FILLED` - 이미 완전 체결된 주문
- `ORDER_ALREADY_CANCELED` - 이미 취소된 주문
- `CANNOT_MODIFY_MARKET_ORDER` - 시장가 주문은 수정 불가 (일부 거래소)

**파라미터 에러:**
- `INVALID_PARAMETERS` - 잘못된 파라미터
- `INVALID_QUANTITY` - 잘못된 수량 (체결량 이하로 감소 불가)
- `INVALID_PRICE` - 잘못된 가격
- `SAME_MARKET_REQUIRED` - 동일 마켓 필수 (Upbit)
- `SAME_SIDE_REQUIRED` - 동일 방향 필수 (Upbit)

**권한 에러:**
- `INSUFFICIENT_BALANCE` - 잔고 부족 (수량 증가 시)
- `PERMISSION_DENIED` - 주문 수정 권한 없음

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

## 거래소별 API 매핑

### Binance

**Futures - Modify Order:**
- **Endpoint:** `PUT /fapi/v1/order`
- **지원:** 직접 수정 (amend)
- **수정 가능:** quantity, price
- **제약:** 미체결 또는 부분체결 주문만

**Spot - Cancel and Replace:**
- **방식:** 취소 후 재생성
- **제약:** 동일 symbol

### Upbit

**Cancel and New:**
- **Endpoint:** `POST /v1/orders/cancel_and_new`
- **방식:** 취소 후 재생성
- **제약:**
  - **반드시 동일 마켓 + 동일 방향** (검증 필요)
  - 새 주문 ID 발급
- **수정 가능:** 모든 필드 (ord_type 포함)

### Bybit

**Amend Order:**
- **Endpoint:** `POST /v5/order/amend`
- **지원:** 직접 수정 (가장 유연)
- **수정 가능:** qty, price, triggerPrice, takeProfit, stopLoss 등
- **제약:** 미체결 또는 부분체결 주문만
- **category 필수:** spot, linear, inverse, option

### Coinbase

**Edit Order:**
- **Endpoint:** `POST /api/v3/brokerage/orders/edit`
- **지원:** 직접 수정
- **제약:**
  - **Limit 주문 + GTC만**
  - 체결량 이하로 size 감소 불가
- **수정 가능:** price, size, stop_price

## 설계 원칙

### Replace 중심 설계

**"Replace"에 초점:**
- 수정 범위가 넓어 새로 만드는 것과 동등
- Worker가 amend 가능하면 amend, 불가능하면 cancel + create
- 사용자는 구현 방식 신경 쓰지 않음

**create_order와 파라미터 일치:**
- 동일한 Optional 파라미터 제공
- None이면 변경 안 함 (또는 기존 값 유지)

### original_order 사용

**주문 식별:**
```python
order_id = original_order.order_id
# or
client_order_id = original_order.client_order_id
```

**address 추출:**
```python
address = original_order.stock_address
```

**Worker 구현:**
1. original_order에서 order_id 추출
2. None이 아닌 파라미터만 수정 대상으로 전달
3. 거래소 API 호출 (amend or cancel + create)

### 거래소별 특수 처리

**Upbit - 검증 필요:**
```python
# Worker에서
if new_side and new_side != original_order.side:
    raise ValueError("Upbit requires same side")
if new_address and new_address != original_order.stock_address:
    raise ValueError("Upbit requires same market")
```

**Coinbase - 검증 필요:**
```python
# Worker에서
if original_order.order_type != OrderType.LIMIT:
    raise ValueError("Coinbase only supports LIMIT order editing")
if original_order.time_in_force != TimeInForce.GTC:
    raise ValueError("Coinbase only supports GTC order editing")
```

**Bybit - category 전달:**
```python
# original_order에서 category 추론
# spot, linear, inverse, option
category = infer_category(original_order.stock_address)
```

### 사용 시나리오

**1. 가격만 수정:**
```python
response = gateway.execute(ModifyOrReplaceOrderRequest(
    request_id="req-001",
    gateway_name="binance",
    original_order=my_order,
    price=51000.0  # 가격만 변경
))

if response.is_success:
    print(f"주문 수정됨: {response.order_id}, 새 가격: {51000.0}")
```

**2. 수량과 가격 모두 수정:**
```python
response = gateway.execute(ModifyOrReplaceOrderRequest(
    request_id="req-001",
    gateway_name="binance",
    original_order=my_order,
    asset_quantity=0.5,  # 수량 변경
    price=52000.0        # 가격 변경
))
```

**3. 주문 타입 변경 (replace):**
```python
response = gateway.execute(ModifyOrReplaceOrderRequest(
    request_id="req-001",
    gateway_name="upbit",
    original_order=my_order,
    order_type=OrderType.MARKET  # LIMIT → MARKET 변경
))
# Upbit은 cancel + new로 처리
```

**4. Time in Force 변경:**
```python
response = gateway.execute(ModifyOrReplaceOrderRequest(
    request_id="req-001",
    gateway_name="upbit",
    original_order=my_order,
    time_in_force=TimeInForce.IOC  # GTC → IOC 변경
))
```

## Worker 구현 가이드

### Amend 지원 거래소 (Bybit, Coinbase, Binance Futures)

```python
# Bybit 예시
def execute(self, request: ModifyOrReplaceOrderRequest):
    params = {
        "category": self._infer_category(request.original_order),
        "symbol": self._encode_symbol(request.original_order.stock_address),
        "orderId": request.original_order.order_id,
    }

    # None이 아닌 필드만 추가
    if request.asset_quantity is not None:
        params["qty"] = str(request.asset_quantity)
    if request.price is not None:
        params["price"] = str(request.price)
    if request.stop_price is not None:
        params["triggerPrice"] = str(request.stop_price)

    # API 호출
    response = self.throttler.execute(
        self.client.amend_order,
        **params
    )

    return self._decode_response(response)
```

### Cancel + Replace 거래소 (Upbit, Binance Spot)

```python
# Upbit 예시
def execute(self, request: ModifyOrReplaceOrderRequest):
    # 검증
    if request.side and request.side != request.original_order.side:
        raise ValueError("Same side required")

    params = {
        "prev_order_uuid": request.original_order.order_id,
        "market": self._encode_symbol(request.original_order.stock_address),
        "side": request.side or request.original_order.side,
    }

    # 새 주문 파라미터
    if request.order_type:
        params["new_ord_type"] = self._encode_order_type(request.order_type)
    if request.asset_quantity:
        params["new_volume"] = str(request.asset_quantity)
    if request.price:
        params["new_price"] = str(request.price)

    # API 호출
    response = self.throttler.execute(
        lambda: requests.post(
            f"{self.base_url}/v1/orders/cancel_and_new",
            headers=self._auth_headers(),
            json=params
        ).json()
    )

    return self._decode_response(response)
```

## 타임스탬프 처리

`processed_when` (공통 필드) 설정 우선순위:
1. 서버 타임스탬프 (updateTime, transactTime 등) - 주문 수정/생성 시각
2. 추정값 `(send_when + receive_when) / 2` - 서버 타임스탬프 없을 경우

대부분의 거래소는 수정 시각을 제공하므로, 서버 타임스탬프를 `processed_when`에 설정하는 것이 기본이다.
별도의 `updated_at` 필드는 불필요하며, `processed_when`을 사용한다.
