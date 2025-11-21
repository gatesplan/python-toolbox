# see_orderbook Request/Response 설계

## 개요

호가창(Order Book) 조회 요청. 특정 자산의 매도/매수 호가 레벨과 수량을 조회한다.

## see_orderbook Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 대상
- `address: StockAddress` - 조회할 자산 주소 (financial-assets)

### 조회 옵션
- `limit: Optional[int]` - 호가 레벨 수 (None이면 기본값 10 사용)

**limit 동작:**
- `limit=None`: 기본값 10 레벨 사용
- `limit=5`: Ask 5개 + Bid 5개 레벨
- `limit=100`: Ask 100개 + Bid 100개 레벨
- 최대값 초과 시: 로깅 경고 후 거래소 최대값으로 조정
  - Binance 최대: 5000
  - Upbit 최대: 30
  - Bybit 최대: 1000 (spot/linear), 500 (inverse), 25 (option)
  - Coinbase 최대: 무제한 (Level 3)

## see_orderbook Response 구조

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

**orderbook: Orderbook** (financial-assets)
```python
orderbook = Orderbook(
    asks=[
        OrderbookLevel(price=50000.0, size=2.5),
        OrderbookLevel(price=50010.0, size=2.0),
        OrderbookLevel(price=50020.0, size=1.5),
    ],
    bids=[
        OrderbookLevel(price=49900.0, size=1.5),
        OrderbookLevel(price=49880.0, size=2.0),
        OrderbookLevel(price=49850.0, size=0.8),
    ]
)
```

**OrderbookLevel 구조:**
- `price: float` - 호가 가격
- `size: float` - 해당 가격의 주문 수량

**정렬:**
- `asks`: 가격 오름차순 (가장 낮은 매도가가 첫 번째)
- `bids`: 가격 내림차순 (가장 높은 매수가가 첫 번째)

### 실패 시 에러 코드

**데이터 에러:**
- `INVALID_SYMBOL` - 존재하지 않는 심볼
- `MARKET_NOT_FOUND` - 존재하지 않는 마켓
- `MARKET_CLOSED` - 마켓 거래 정지
- `INVALID_LIMIT` - 잘못된 limit 값 (최대값 초과)

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

## 설계 원칙

### 단순성: price와 size만

호가 레벨은 가장 기본적인 정보만 제공:
- 가격 (price)
- 수량 (size)

제외된 정보:
- 주문 개수 (num_orders): Coinbase만 제공, 대부분 거래소 미지원
- 총 호가량 (total_ask_size, total_bid_size): Upbit만 제공, 수동 계산 가능

### Orderbook 타입 사용

financial-assets의 Orderbook 타입 사용:
```python
from financial_assets.orderbook import Orderbook, OrderbookLevel

# Response에서
response.orderbook.asks[0].price  # 베스트 매도가
response.orderbook.bids[0].price  # 베스트 매수가
```

도메인 객체 사용으로 일관성 유지:
- Order, Trade, Pair, Token과 동일한 패턴
- Gateway 외부에서도 Orderbook 타입 재사용 가능

### limit 처리 정책

**기본값:**
- `limit=None` → 10 레벨 사용
- 모든 거래소에서 통일된 기본값

**최대값 초과 시 처리:**
1. 로깅 경고: `logger.warning(f"Requested limit {limit} exceeds {gateway} max {max_limit}, using {max_limit}")`
2. 거래소 최대값으로 조정하여 API 호출
3. 사용자에게는 조정된 결과 반환

**거래소별 최대값:**
- Binance: 5000
- Upbit: 30
- Bybit: 1000 (spot/linear), 500 (inverse), 25 (option)
- Coinbase: 무제한 (실제로는 Level 2 사용, 적절한 수준)

### 타임스탬프 처리

`processed_when` 우선순위:
1. 매칭 엔진 타임스탬프 (Bybit cts) - 최우선
2. 서버 타임스탬프 (Upbit timestamp, Bybit ts, Coinbase time)
3. 추정값 `(send_when + receive_when) / 2` (Binance)
