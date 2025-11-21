# Gateway 구현 가이드라인

## 문서 목적

이 문서는 구체 Gateway Worker를 구현할 때 따라야 할 철학, 원칙, 동작 방향을 제시한다. 각 request/response 엔드포인트별로 어떤 순서와 방향성을 가지고 동작을 구현해야 하는지를 의사코드 수준에서 명세한다.

**대상 독자:** Gateway Worker 구현자 (BinanceSpotGateway, UpbitSpotGateway 등)

**범위:**
- 개념 및 용어 정의
- 엔드포인트별 구현 철학 및 동작 순서
- 공통 처리 원칙
- 거래소별 특수 처리 지침

**제외:**
- 구체적인 코드 구현 (언어/라이브러리 종속적)
- 거래소 API 세부 파라미터 (각 Gateway 구현에서 처리)

---

## 핵심 개념 및 용어

### Gateway의 역할

**Gateway는:**
- financial-assets의 표준 타입(StockAddress, Symbol, Order, Token, Pair 등)을 입력받음
- 거래소 API 형식으로 변환(encode)하여 요청
- 거래소 API 응답을 표준 Request/Response 명세에 정의된 형식으로 변환(decode)하여 반환
- throttled-api를 통해 rate limit을 준수하며 API 호출
- 여러 거래소의 차이를 추상화하여 통합된(unified) 인터페이스 제공

**Gateway는 아님:**
- 비즈니스 로직 실행 주체 (전략, 포트폴리오 관리 등)
- 데이터 저장소 (주문, 잔고 등은 상위 레이어에서 관리)
- 명세에 없는 파생 데이터 생성기 (수익률, 변화율 등 계산하지 않음)

### 핵심 용어

**Encode:**
- financial-assets 표준 타입 → 거래소 API 파라미터 변환
- 예: `StockAddress("BINANCE", "SPOT", "BTC", "USDT")` → `"BTCUSDT"`
- 예: `Symbol("BTC/USDT")` → `"BTCUSDT"`
- 예: `OrderSide.BUY` → `"BUY"`

**Decode:**
- 거래소 API 응답 → financial-gateway Response 객체 변환
- 예: `{"orderId": "12345", "status": "NEW"}` → `CreateOrderResponse(order_id="12345", status=OrderStatus.NEW)`

**Symbol:**
- 거래쌍을 나타내는 표준 타입 (financial-assets)
- `Symbol("BTC/USDT")` → base: "BTC", quote: "USDT"
- base: 거래 대상 자산 (보유하거나 매수/매도하는 자산)
- quote: 가격 표시 통화 (unit_currency)

**Processed When:**
- 서버가 요청을 처리한 시각 (UTC ms)
- 우선순위: (1) 거래소 응답의 서버 타임스탬프, (2) `(send_when + receive_when) / 2`

**Timegaps:**
- `receive_when - send_when` (API 왕복 시간, ms)

---

## Gateway 구현 일반 원칙

### 1. 표준 명세 준수 원칙 (Specification Compliance)

**철학:**
여러 거래소 API를 통합(unified)된 방식으로 다루기 위해, financial-gateway는 각 거래/조회/변경 행위에 대한 자체적인 기준(명세)을 세운다. 구체 Gateway Worker는 이 명세에 맞추기 위해 필요한 모든 변환과 매핑을 수행한다.

**적용:**
- Request/Response 구조는 거래소와 무관하게 동일
- 거래소 API 응답을 명세에 정의된 형식으로 변환
- 거래소별 차이를 추상화하여 일관된 인터페이스 제공
- 명세에 정의된 필드는 가능한 한 모두 채움

**예시:**
```
OrderStatus 통합:
  Binance "NEW" → OrderStatus.NEW
  Upbit "wait" → OrderStatus.NEW
  Coinbase "open" → OrderStatus.NEW

타임스탬프 통일:
  Binance transactTime (ms) → processed_when (UTC ms)
  Upbit created_at (ISO string) → processed_when (UTC ms로 변환)

에러 코드 표준화:
  Binance "-1013: Invalid quantity" → INVALID_QUANTITY
  Upbit "invalid_parameter.volume" → INVALID_QUANTITY
```

**예외: 명세 필수 필드 계산**
```
명세에 필수로 정의된 필드는 거래소가 직접 제공하지 않아도 계산:
  - see_holdings의 평단가 (avg_buy_price)
    → 거래소가 직접 제공하지 않으면 거래 내역 조회하여 계산
  - Pair의 value (Token)
    → total × avg_buy_price

단, 거래 내역 API를 제공하지 않는 거래소는 지원하지 않음
```

**단, 다음은 하지 않음:**
- 비즈니스 로직 수행 (전략, 리스크 관리 등)
- 명세에 없는 파생 데이터 생성 (수익률, 변화율, 호가 스프레드 등)
- 명세에 Optional로 정의된 필드를 추론하거나 계산

### 2. 명시적 에러 처리 (Explicit Error Handling)

**철학:**
모든 실패 케이스를 표준화된 에러 코드로 분류한다. 거래소 에러 메시지는 그대로 전달하되, 에러 코드로 분류하여 상위 레이어가 처리 가능하게 한다.

**에러 응답 구조:**
```
Response(
  is_success=False,
  error_code="INSUFFICIENT_BALANCE",
  error_message="[원본 거래소 에러 메시지]",
  ... (기타 공통 필드)
)
```

**에러 코드 분류:**
- 파라미터 에러: `INVALID_*` (수량, 가격, 심볼 등)
- 상태 에러: `ORDER_ALREADY_*`, `MARKET_CLOSED` 등
- 권한 에러: `AUTHENTICATION_FAILED`, `PERMISSION_DENIED` 등
- 시스템 에러: `API_ERROR`, `NETWORK_ERROR`, `RATE_LIMIT_EXCEEDED` 등

### 3. 타임스탬프 우선순위 (Timestamp Priority)

**철학:**
서버 타임스탬프를 최우선으로 사용한다. 로컬 시간은 fallback으로만 사용한다.

**Processed When 설정 순서:**
1. 거래소 응답의 서버 타임스탬프 (transactTime, updateTime, timestamp 등)
2. 없으면 추정값: `(send_when + receive_when) / 2`

**Send/Receive When:**
- `send_when`: API 요청 직전 시각 (로컬)
- `receive_when`: API 응답 수신 직후 시각 (로컬)

### 4. Order 객체 중심 설계 (Order-Centric Design)

**철학:**
주문 생명주기 전체에서 Order 객체를 중심으로 데이터를 전달한다.

**흐름:**
```
create_order Request
  → 거래소 API 호출
  → SpotOrder 생성 (financial-assets)
  → Response에 주문 정보 포함

cancel_order / modify_or_replace_order Request
  → SpotOrder 객체를 그대로 받음
  → order.order_id, order.stock_address 활용
  → API 호출
```

**장점:**
- Race condition 방지 (order_id + address 함께 전달)
- 파라미터 누락 방지
- 일관된 데이터 흐름

### 5. 거래소 독립성 유지 (Exchange Independence)

**철학:**
Gateway는 거래소별 특수 로직을 포함하지만, 인터페이스는 거래소 독립적이다.

**원칙:**
- Request/Response 구조는 모든 거래소에 동일
- 거래소별 차이는 Worker 내부에서 처리
- 거래소가 지원하지 않는 기능은 에러 반환 (FEATURE_NOT_SUPPORTED)

**예시:**
```
Upbit은 modify 미지원
→ Worker 내부에서 cancel + create로 처리
→ 사용자는 ModifyOrReplaceOrderRequest를 동일하게 사용

Binance는 post_only를 timeInForce로 처리
→ Worker 내부에서 encode 시 변환
→ 사용자는 post_only 파라미터를 동일하게 사용
```

---

## 엔드포인트별 구현 가이드라인

### create_order - 주문 생성

**목적:** 새로운 주문을 생성한다.

**Request 철학:**
- 주문 타입(LIMIT, MARKET, STOP 등)에 따라 필수 파라미터가 다름
- Optional 파라미터(time_in_force, post_only 등)는 기본값 적용
- client_order_id가 없으면 request_id를 사용

**Worker 동작 순서:**

```
1. Request 검증
   - 주문 타입별 필수 파라미터 확인
   - 수량/가격 유효성 사전 검증 (선택적)

2. Encode (Request → API params)
   - address → symbol (거래소 형식)
   - side, order_type → 거래소 enum
   - time_in_force, post_only → 거래소 파라미터
   - self_trade_prevention → 거래소 파라미터 (지원 시)

3. API 호출 (via throttler)
   - send_when 기록
   - throttler.execute(api_call, params)
   - receive_when 기록

4. Decode (API response → Response)
   - order_id, client_order_id 추출
   - status 매핑 (거래소 enum → OrderStatus)
   - processed_when 설정 (서버 타임스탬프 우선)
   - trades 추출 (즉시 체결 시)

5. Response 반환
   - is_success=True
   - 모든 타임스탬프 필드 설정
   - timegaps 계산
```

**에러 처리:**
```
API 에러 발생 시:
  - 에러 응답 파싱
  - 에러 코드 분류 (거래소 에러 → 표준 에러 코드)
  - Response(is_success=False, error_code=..., error_message=...)

네트워크 에러:
  - error_code="NETWORK_ERROR"
  - error_message에 예외 메시지 포함

Rate limit 초과:
  - throttler가 자동 처리 (대기 후 재시도)
  - 재시도 실패 시 error_code="RATE_LIMIT_EXCEEDED"
```

**특수 케이스:**
- 즉시 체결 (MARKET 또는 IOC): trades 리스트 포함
- Post-only 거부: error_code="POST_ONLY_REJECTED"
- FOK 전량 미체결: error_code="FOK_NO_FULL_FILL"

---

### cancel_order - 주문 취소

**목적:** 기존 주문을 취소한다.

**Request 철학:**
- SpotOrder 객체를 직접 받아 order_id와 address를 함께 전달
- client_order_id가 있으면 우선 사용 (거래소 권장사항)

**Worker 동작 순서:**

```
1. Order 정보 추출
   - order_id = request.order.order_id
   - client_order_id = request.order.client_order_id (있으면)
   - address = request.order.stock_address

2. Encode
   - address → symbol
   - order_id 또는 client_order_id 전달 (우선순위: client_order_id)

3. API 호출 (via throttler)
   - send_when, receive_when 기록
   - throttler.execute(cancel_api, params)

4. Decode
   - status → OrderStatus.CANCELED
   - filled_amount, remaining_amount 추출
   - processed_when 설정

5. Response 반환
```

**에러 처리:**
```
ORDER_NOT_FOUND:
  - 주문이 존재하지 않음
  - 이미 완전 체결되어 자동 삭제되었을 가능성

ORDER_ALREADY_CANCELED:
  - 중복 취소 요청
  - 멱등성: 성공으로 처리할지, 에러로 처리할지는 구현 선택

ORDER_ALREADY_FILLED:
  - 취소 시도 전에 이미 전량 체결
  - filled_amount 포함하여 반환

CANCEL_STATUS_UNKNOWN:
  - 서버 오류로 취소 상태 불명
  - 사용자는 see_order로 재조회 필요
```

**Race Condition 처리:**
- 취소 요청 중 체결 발생: filled_amount 반영
- 동시 취소 요청: 거래소가 처리, 첫 요청만 성공

---

### modify_or_replace_order - 주문 수정/재생성

**목적:** 기존 주문을 수정하거나 취소 후 재생성한다.

**Request 철학:**
- original_order로 기존 주문 식별
- Optional 파라미터로 수정 사항 전달 (None이면 변경 안 함)
- 거래소가 amend 지원하면 수정, 미지원하면 cancel + create

**Worker 동작 순서:**

```
1. 거래소 기능 확인
   - amend 지원 여부 확인
   - 지원: 수정 흐름
   - 미지원: 재생성 흐름

2-A. Amend 흐름 (Bybit, Coinbase, Binance Futures)
   - 기존 order_id 유지
   - None이 아닌 파라미터만 API에 전달
   - 수정 가능 필드 제약 확인 (거래소별)

2-B. Cancel + Create 흐름 (Upbit, Binance Spot)
   - 기존 주문 취소 API 호출
   - 새 주문 생성 API 호출
   - 새 order_id 발급
   - 거래소별 제약 검증 (예: Upbit은 same side/market 필수)

3. Encode
   - original_order → order_id, symbol 추출
   - 수정 파라미터 → 거래소 API 파라미터

4. API 호출

5. Decode
   - order_id (amend: 유지, replace: 새 ID)
   - status 매핑
   - trades 추출 (replace 시 기존 체결 내역)

6. Response 반환
```

**거래소별 특수 처리:**
```
Upbit:
  - same side + same market 필수
  - 검증 실패 시 error_code="SAME_SIDE_REQUIRED" 또는 "SAME_MARKET_REQUIRED"

Coinbase:
  - LIMIT + GTC만 수정 가능
  - 검증 실패 시 error_code="INVALID_ORDER_TYPE_FOR_EDIT"

Bybit:
  - category (spot, linear, inverse, option) 필수
  - original_order.stock_address에서 추론
```

**에러 처리:**
```
CANNOT_MODIFY_MARKET_ORDER:
  - 시장가 주문은 수정 불가 (일부 거래소)

INVALID_QUANTITY:
  - 체결량 이하로 감소 불가

ORDER_ALREADY_FILLED / ORDER_ALREADY_CANCELED:
  - 수정 불가능한 상태
```

---

### see_order - 단일 주문 조회

**목적:** 특정 주문의 현재 상태를 조회한다.

**Request 철학:**
- order_id 또는 client_order_id로 식별
- address를 함께 전달 (일부 거래소는 symbol 필수)

**Worker 동작 순서:**

```
1. 식별자 우선순위
   - client_order_id 우선 (있으면)
   - 없으면 order_id

2. Encode
   - address → symbol
   - order_id 또는 client_order_id

3. API 호출

4. Decode
   - order_id, client_order_id, status 추출
   - filled_quantity, remaining_quantity 추출
   - average_price 추출 (거래소 제공 시)
   - trades 추출 (거래소 제공 시)
   - processed_when ← 주문의 최종 업데이트 시각

5. Response 반환
```

**에러 처리:**
```
ORDER_NOT_FOUND:
  - 주문이 존재하지 않음
  - 오래된 주문은 거래소가 삭제했을 가능성
```

---

### see_open_orders - 미체결 주문 목록 조회

**목적:** 현재 미체결 상태인 주문들을 조회한다.

**Request 철학:**
- address로 필터링 (Optional, None이면 전체)
- 미체결 = NEW 또는 PARTIALLY_FILLED 상태

**Worker 동작 순서:**

```
1. 필터 설정
   - address가 있으면 symbol로 encode
   - 없으면 전체 조회

2. API 호출
   - 미체결 주문 조회 API

3. Decode
   - 각 주문별로 Order 정보 추출
   - orders 리스트 생성
   - processed_when ← 응답 타임스탬프 (또는 추정)

4. Response 반환
   - orders: List[OrderInfo]
```

**특수 케이스:**
```
거래소가 전체 조회 미지원:
  - 사용 가능한 심볼 목록 조회
  - 각 심볼별 미체결 주문 조회
  - 결과 병합
```

---

### see_holdings - 보유 자산 조회

**목적:** 현재 보유 중인 자산(거래 대상)을 조회한다.

**Request 철학:**
- symbols로 필터링 (Optional, None이면 전체)
- Symbol 객체를 사용하여 unit_currency 명시
- symbols에 따라 필터링 동작이 다름:
  - `symbols=None`: 보유량이 0.001 미만인 자산 제외 (dust 제거)
  - `symbols=[Symbol("BTC/USDT"), Symbol("ETH/BTC")]`: 보유량이 0이어도 포함 (0으로 표시)

**Worker 동작 순서:**

```
1. 필터 및 unit_currency 설정
   if symbols is not None:
     - 각 Symbol의 base 추출 (조회 대상 자산)
     - 각 Symbol의 quote 추출 (unit_currency)
   else:
     - 전체 조회
     - 거래소 기본 unit_currency 사용 (Upbit: KRW, Binance: USDT 등)

2. API 호출
   - 잔고 조회 API

3. Decode
   - 각 자산별로:
     - Symbol에서 quote 추출 (또는 거래소 기본값)
     - balance = Pair(
         asset=Token(symbol.base, total),
         value=Token(symbol.quote, total * avg_price)
       )
     - available, promised 추출
   - holdings dict 생성

4. 보유량 필터링
   if symbols is None:
     - total >= 0.001인 자산만 포함 (dust 제거)
   else:
     - symbols에 명시된 자산(base)은 모두 포함 (total이 0이어도)

5. Response 반환
   - holdings: dict[str, dict[str, Union[Pair, float]]]
```

**Symbol과 Pair:**
```
Symbol.quote가 Pair의 value currency:
  - Symbol("BTC/USDT") 요청
    → Pair(Token("BTC", 0.5), Token("USDT", 25000))
  - Symbol("ETH/BTC") 요청
    → Pair(Token("ETH", 10), Token("BTC", 0.5))

symbols=None (전체 조회) 시:
  - 거래소 기본 quote currency 사용 (Upbit: KRW, Binance: USDT)
```

---

### see_balance - 잔고 조회 (자금)

**목적:** 거래 자금(USDT, KRW 등)의 잔고를 조회한다.

**Request 철학:**
- see_holdings와 유사하지만, 거래 자금에 초점
- 일부 거래소는 holdings와 balance를 구분하지 않음

**Worker 동작 순서:**

```
1. API 호출
   - 자금 잔고 조회 API

2. Decode
   - 각 통화별:
     - total, available, promised 추출
     - Token 생성

3. Response 반환
   - balances: dict[str, Token]
```

**거래소별 차이:**
```
Binance:
  - Spot wallet에 BTC, ETH, USDT 모두 포함
  - holdings와 balance 구분 없음

Upbit:
  - KRW는 balance, BTC/ETH는 holdings
  - 명확히 구분됨
```

---

### see_available_markets - 거래 가능 마켓 조회

**목적:** 거래소에서 거래 가능한 마켓(심볼) 목록을 조회한다.

**Request 철학:**
- 필터링 없이 전체 조회
- 마켓별 메타데이터 포함 (min_quantity, price_precision 등)

**Worker 동작 순서:**

```
1. API 호출
   - 거래 가능 마켓 조회 API

2. Decode
   - 각 마켓별:
     - address = StockAddress 생성
     - metadata 추출:
       - min_quantity, max_quantity
       - min_price, max_price
       - price_precision, quantity_precision
       - status (TRADING, HALT 등)

3. Response 반환
   - markets: List[MarketInfo]
```

**활용:**
```
상위 레이어가 주문 생성 시 검증에 사용:
  - 수량이 min_quantity 이상인지
  - 가격의 소수점 자리수가 price_precision 이내인지
```

---

### see_ticker - 현재 시세 조회

**목적:** 특정 마켓의 현재 시세를 조회한다.

**Request 철학:**
- address로 마켓 지정
- 기본 필드만 제공 (current, open, high, low, volume)

**Worker 동작 순서:**

```
1. Encode
   - address → symbol

2. API 호출
   - ticker 조회 API

3. Decode
   - current, open, high, low, volume 추출
   - processed_when ← 거래소 타임스탬프

4. Response 반환
```

**설계 철학:**
```
최소 필드만 제공:
  - 변화율, 호가 등 파생 데이터는 제외
  - 사용자가 직접 계산 가능

기준 시간은 implicit:
  - 암호화폐: rolling 24h
  - 주식: 당일 거래시간
  - Gateway 문서에서 거래소별 특성 안내
```

---

### see_orderbook - 호가창 조회

**목적:** 특정 마켓의 매수/매도 호가를 조회한다.

**Request 철학:**
- address로 마켓 지정
- depth 지정 (Optional, 기본값: 거래소 제공 전체)

**Worker 동작 순서:**

```
1. Encode
   - address → symbol
   - depth → limit (거래소 파라미터)

2. API 호출

3. Decode
   - bids: List[PriceLevel] (매수 호가, 내림차순)
   - asks: List[PriceLevel] (매도 호가, 오름차순)
   - PriceLevel = (price: float, quantity: float)

4. Response 반환
   - bids, asks
   - processed_when
```

**정렬 보장:**
```
bids: 높은 가격부터 (내림차순)
asks: 낮은 가격부터 (오름차순)

거래소 응답이 다른 순서면 Worker에서 정렬
```

---

### see_trades - 최근 체결 내역 조회

**목적:** 특정 마켓의 최근 체결 내역을 조회한다.

**Request 철학:**
- address로 마켓 지정
- limit로 개수 제한 (Optional)

**Worker 동작 순서:**

```
1. Encode
   - address → symbol
   - limit → 거래소 파라미터

2. API 호출

3. Decode
   - 각 체결별:
     - price, quantity, timestamp
     - side (매수/매도 구분, 거래소 제공 시)
   - trades 리스트 생성

4. Response 반환
   - trades: List[PublicTrade]
```

**주의:**
```
Public trade vs. My trade:
  - see_trades: 전체 시장 체결 내역 (public)
  - see_order의 trades: 내 주문 체결 내역 (private)
```

---

### see_candles - 캔들 차트 조회

**목적:** 특정 마켓의 OHLCV 캔들 데이터를 조회한다.

**Request 철학:**
- address로 마켓 지정
- interval (1m, 5m, 1h, 1d 등)
- start_time, end_time으로 범위 지정

**Worker 동작 순서:**

```
1. Encode
   - address → symbol
   - interval → 거래소 interval 형식
   - start_time, end_time → 거래소 파라미터

2. API 호출

3. Decode
   - 각 캔들별:
     - timestamp, open, high, low, close, volume
   - candles 리스트 생성

4. Response 반환
   - candles: List[Candle]
```

**Interval 매핑:**
```
표준 interval → 거래소 interval:
  - "1m" → Binance: "1m", Upbit: "minutes/1"
  - "1h" → Binance: "1h", Upbit: "minutes/60"
  - "1d" → Binance: "1d", Upbit: "days"

거래소가 지원하지 않는 interval:
  - error_code="INVALID_INTERVAL"
```

---

### see_server_time - 서버 시각 조회

**목적:** 거래소 서버의 현재 시각을 조회한다.

**Request 철학:**
- 파라미터 없음
- 로컬 시간과 서버 시간의 차이를 확인하기 위함

**Worker 동작 순서:**

```
1. API 호출
   - send_when 기록
   - 서버 시각 조회 API
   - receive_when 기록

2. Decode
   - server_time 추출 (UTC ms)
   - processed_when ← server_time

3. Time offset 계산
   - offset = server_time - ((send_when + receive_when) / 2)

4. Response 반환
   - server_time, offset
```

**활용:**
```
로컬 시간 보정:
  - timestamp_for_api = local_time + offset

Timestamp signature 생성 시 사용:
  - 일부 거래소는 시간 차이가 크면 인증 실패
```

---

## 공통 처리 원칙

### 타임스탬프 처리

**Processed When 설정 원칙:**

서버 타임스탬프를 최우선으로 사용:
1. 거래소 응답에서 서버 타임스탬프 필드 찾기
   - 필드명은 거래소마다 다름 (transactTime, updateTime, timestamp 등)
   - 주문 처리/생성/수정 시각을 나타내는 필드 사용
2. 서버 타임스탬프가 없으면 추정값 사용
   - 추정값 = (send_when + receive_when) / 2

**Send/Receive When 기록:**

API 호출 직전과 직후의 로컬 시각을 기록:
- send_when: API 요청을 보내기 직전 (UTC ms)
- receive_when: API 응답을 받은 직후 (UTC ms)
- timegaps = receive_when - send_when (API 왕복 시간)

### 에러 응답 생성

**에러 처리 흐름:**

1. API 호출 중 에러 발생 시 catch
2. 거래소 에러를 표준 에러 코드로 분류
3. Response 객체 생성:
   - is_success = False
   - error_code = 표준 에러 코드
   - error_message = 원본 거래소 에러 메시지 (그대로 보존)
   - 타임스탬프 필드들 (send_when, receive_when, processed_when, timegaps)

**에러 분류 원칙:**

거래소 에러 코드/메시지를 분석하여 표준 에러 코드로 매핑:
- Binance "-1013" → INVALID_QUANTITY
- Binance "-2010" → INSUFFICIENT_BALANCE
- Upbit "invalid_parameter.volume" → INVALID_QUANTITY
- 분류할 수 없는 에러 → API_ERROR (일반적인 에러 코드)

거래소 에러 메시지는 error_message에 그대로 보존하여 디버깅 지원

### Encode/Decode 일관성

**Encode 원칙 (표준 타입 → 거래소 API 형식):**

표준 타입을 거래소 특정 형식으로 변환:
- StockAddress/Symbol → 거래소 심볼 문자열 (Binance: "BTCUSDT", Upbit: "KRW-BTC")
- OrderSide/OrderType/TimeInForce → 거래소 enum 값
- 기타 거래소별 특수 파라미터 처리

거래소가 파라미터를 지원하지 않는 경우:
- Optional 파라미터: 무시하거나 기본값 사용
- 필수 파라미터: 에러 반환 (FEATURE_NOT_SUPPORTED)

**Decode 원칙 (거래소 API 응답 → 표준 Response):**

거래소 응답을 표준 타입으로 변환:
- 심볼 문자열 → StockAddress 또는 Symbol 객체
- 거래소 status 값 → OrderStatus enum
- 거래소 timestamp → UTC ms (int 타입)

거래소가 필드를 제공하지 않는 경우:
- Optional 필드: None으로 설정
- 필수 필드 & 계산 가능: 계산하여 채움 (예: 평단가)
- 필수 필드 & 계산 불가: 거래소 미지원

---

## 거래소별 특수 처리

### Throttler 통합

**모든 API 호출은 throttler를 통해 수행:**

Throttler의 역할:
- Rate limit 준수 (soft rate limiting)
- 일시적 에러 발생 시 자동 재시도
- 에러 분류 및 상위로 전파

Gateway Worker는 직접 API를 호출하지 않고, 항상 throttler를 통해 호출하여 거래소 API 제약을 준수

### 거래소별 제약 처리

**Upbit:**
- modify_or_replace_order: 동일 side + 동일 market 필수 (검증 후 에러 반환)
- 자전거래 방지(self_trade_prevention): 미지원 (파라미터 무시)

**Binance:**
- post_only: timeInForce로 변환하여 처리
- 일부 주문 타입: 파라미터 변환 필요 (예: STOP_LOSS → STOP_LOSS_LIMIT)

**Coinbase:**
- modify: LIMIT + GTC 주문만 수정 가능 (사전 검증)
- 수수료: Maker/Taker 구분 명확, Trade 객체에 정확히 기록

**공통 원칙:**
거래소별 제약은 Worker 내부에서 처리하며, 사용자에게는 통일된 인터페이스 제공

---

## 구현 체크리스트

### 각 엔드포인트 구현 시 확인사항

**Request 처리:**
- [ ] Request 파라미터 검증
- [ ] Encode 함수 구현 (표준 타입 → 거래소 API 파라미터)
- [ ] 거래소별 파라미터 제약 처리
- [ ] client_order_id 기본값 처리 (request_id 사용)

**API 호출:**
- [ ] throttler를 통한 API 호출
- [ ] send_when, receive_when 기록
- [ ] 네트워크 에러 처리
- [ ] Rate limit 에러 처리

**Response 처리:**
- [ ] Decode 함수 구현 (거래소 응답 → Response 객체)
- [ ] processed_when 설정 (서버 타임스탬프 우선)
- [ ] timegaps 계산
- [ ] Optional 필드: 거래소가 제공하지 않으면 None 설정
- [ ] 필수 필드: 거래소가 제공하지 않으면 계산 (계산 불가시 거래소 미지원)

**에러 처리:**
- [ ] 거래소 에러 코드 분류
- [ ] 표준 에러 코드 매핑
- [ ] 에러 메시지 그대로 전달
- [ ] is_success=False 설정

**테스트:**
- [ ] 정상 케이스 테스트
- [ ] 에러 케이스 테스트 (파라미터, 권한, 시스템 에러)
- [ ] 타임스탬프 정확성 확인
- [ ] 거래소별 특수 케이스 테스트

---

## 결론

이 가이드라인은 구체 Gateway Worker 구현 시 따라야 할 철학과 원칙을 제시한다. 핵심은:

1. **표준 명세 준수**: 거래소별 차이를 추상화하여 통합된 Request/Response 명세에 맞춤
2. **명시적 에러 처리**: 모든 실패를 표준 에러 코드로 분류
3. **타임스탬프 우선순위**: 서버 타임스탬프 최우선
4. **Order 중심 설계**: 주문 생명주기에서 Order 객체 활용
5. **거래소 독립성**: 인터페이스는 동일, 내부만 다름

각 엔드포인트는 동일한 패턴을 따르며:
- Request: 표준 타입(Symbol, StockAddress, Order 등) 입력
- Encode: 거래소 API 형식으로 변환
- API 호출: throttler를 통해 rate limit 준수
- Decode: 거래소 응답을 표준 Response로 변환
- 필수 필드는 가능한 한 모두 채움 (필요시 계산)

거래소별 차이는 Worker 내부에서 처리하며, 사용자는 거래소와 무관하게 동일한 인터페이스를 사용한다.
