# see_ticker Request/Response 설계

## 개요

현재 시세 조회 요청. 특정 자산의 현재가, 고가, 저가, 시가, 거래량을 조회한다.

## see_ticker Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 대상
- `address: StockAddress` - 조회할 자산 주소 (financial-assets)

## see_ticker Response 구조

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

**가격:**
- `current: float` - 현재가
- `open: float` - 시가
- `high: float` - 고가
- `low: float` - 저가

**거래량:**
- `volume: float` - 거래량 (base asset 기준)

**참고:**
- 시가/고가/저가의 기준 시간은 거래소와 시장 특성에 따라 다름
- 24시간 개장 시장(암호화폐): 일반적으로 rolling 24h
- 제한된 거래시간(주식): 일반적으로 당일 거래 시작 시간 기준
- Gateway 사용자는 거래소 특성을 이해하고 사용

### 실패 시 에러 코드

**데이터 에러:**
- `INVALID_SYMBOL` - 존재하지 않는 심볼
- `MARKET_NOT_FOUND` - 존재하지 않는 마켓

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

## 설계 원칙

### 기본 필드만 제공

ticker 조회는 가장 기본적인 시세 정보만 제공:
- 현재가, 시가, 고가, 저가, 거래량

변화율, 호가, 가중평균가 등 부가 정보는 제외:
- 변화율: 사용자가 직접 계산 가능
- 호가: see_orderbook으로 조회
- 상세 통계: 거래소별로 차이가 큼

### Implicit 기준 시간

시가/고가/저가의 기준 시간은 명시하지 않음:
- 거래소와 시장 타입에 따라 자연스럽게 해석
- 암호화폐: rolling 24h
- 주식: 당일 거래시간
- Gateway 문서에서 거래소별 특성 안내

### 단순 매핑

거래소 API가 제공하는 ticker 정보를 직접 매핑:
- 복잡한 변환이나 계산 없음
- 거래소가 제공하는 값 그대로 전달

## 거래소별 매핑 예시

### Binance

**API:**
```
GET /api/v3/ticker/24hr?symbol=BTCUSDT
```

**Response:**
```json
{
  "symbol": "BTCUSDT",
  "lastPrice": "50000.00",
  "openPrice": "49000.00",
  "highPrice": "51000.00",
  "lowPrice": "48500.00",
  "volume": "1234.56"
}
```

**변환:**
```python
SeeTickerResponse(
    request_id=request_id,
    is_success=True,
    send_when=send_when,
    receive_when=receive_when,
    processed_when=close_time,
    timegaps=receive_when - send_when,
    current=50000.00,
    open=49000.00,
    high=51000.00,
    low=48500.00,
    volume=1234.56
)
```

### Upbit

**API:**
```
GET /v1/ticker?markets=KRW-BTC
```

**Response:**
```json
{
  "market": "KRW-BTC",
  "trade_price": 65000000,
  "opening_price": 64000000,
  "high_price": 66000000,
  "low_price": 63500000,
  "acc_trade_volume_24h": 123.45
}
```

**변환:**
```python
SeeTickerResponse(
    request_id=request_id,
    is_success=True,
    send_when=send_when,
    receive_when=receive_when,
    processed_when=trade_timestamp,
    timegaps=receive_when - send_when,
    current=65000000,
    open=64000000,
    high=66000000,
    low=63500000,
    volume=123.45
)
```

### Coinbase

**API:**
```
GET /products/BTC-USD/ticker
GET /products/BTC-USD/stats
```

**Ticker Response:**
```json
{
  "price": "50000.00",
  "volume": "1234.56"
}
```

**Stats Response:**
```json
{
  "open": "49000.00",
  "high": "51000.00",
  "low": "48500.00"
}
```

**변환:**
```python
# Ticker + Stats 조합 필요
SeeTickerResponse(
    request_id=request_id,
    is_success=True,
    send_when=send_when,
    receive_when=receive_when,
    processed_when=ticker_time,
    timegaps=receive_when - send_when,
    current=50000.00,
    open=49000.00,
    high=51000.00,
    low=48500.00,
    volume=1234.56
)
```

**참고:** Coinbase는 ticker와 stats를 별도 API로 제공하므로, Gateway 내부에서 두 API를 조합하여 응답 생성.

### Simulation Gateway

시뮬레이션 Exchange에서 제공하는 ticker 정보를 그대로 반환.

## 사용 시나리오

### 1. 현재가 확인
```python
response = gateway.execute(SeeTickerRequest(
    request_id="req-001",
    gateway_name="binance",
    address=StockAddress(...)
))

if response.is_success:
    print(f"현재가: {response.current}")
```

### 2. 변화율 계산
```python
if response.is_success:
    change = response.current - response.open
    change_percent = (change / response.open) * 100
    print(f"변화: {change} ({change_percent:.2f}%)")
```

### 3. 가격 범위 확인
```python
if response.is_success:
    price_range = response.high - response.low
    current_position = (response.current - response.low) / price_range
    print(f"현재가는 범위의 {current_position*100:.1f}% 위치")
```

## 다음 구현 단계

1. `SeeTickerRequest` dataclass 구현
2. `SeeTickerResponse` dataclass 구현
3. `__init__.py`에 export 추가
4. Gateway Worker 구현 시 거래소별 API 매핑
