# see_available_markets Request/Response 설계

## 개요

거래 가능한 마켓 목록 조회 요청. 거래소에서 제공하는 모든 거래쌍(심볼)과 각 마켓의 거래 상태를 조회한다.

## see_available_markets Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 옵션

**개수 제한:**
- `limit: Optional[int]` - 조회할 마켓 개수 (None이면 게이트웨이 기본값 또는 전체 조회)

**limit 동작:**
- `limit=None`: 게이트웨이에서 적당한 기본값 또는 전체 마켓 반환 (구현 의존)
- `limit=100`: 최대 100개 마켓 반환
- 거래소별로 최대값이 다르므로, Worker 구현 시 적절히 처리

**설계 원칙:**
- 최소주의 접근 (Upbit 스타일)
- 거래소 API 원본 데이터를 최대한 활용
- Gateway는 단순히 조회만 담당
- 필터링이 필요한 경우 사용자가 Response 데이터를 직접 필터링

## see_available_markets Response 구조

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

**markets: List[MarketInfo]** (financial-gateway 도메인 객체)

```python
@dataclass
class MarketInfo:
    symbol: Symbol                    # financial-assets.symbol.Symbol
    status: MarketStatus              # financial-assets.constants.MarketStatus
```

**예시:**
```python
markets = [
    MarketInfo(
        symbol=Symbol("BTC/USDT"),
        status=MarketStatus.TRADING
    ),
    MarketInfo(
        symbol=Symbol("ETH/USDT"),
        status=MarketStatus.TRADING
    ),
    MarketInfo(
        symbol=Symbol("DOGE/USDT"),
        status=MarketStatus.HALT
    ),
]
```

### 실패 시 에러 코드

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

**권한 에러:**
- `AUTHENTICATION_FAILED` - API 키 인증 실패 (일부 거래소에서 인증 필요)

## 설계 원칙

### Symbol 객체 사용

financial-assets의 Symbol 클래스 사용:
```python
from financial_assets.symbol import Symbol

# Response에서
for market in response.markets:
    print(f"{market.symbol.base}/{market.symbol.quote}: {market.status.name}")
    # BTC/USDT: TRADING
```

**도메인 객체 사용 이점:**
- base/quote 자동 파싱
- 형식 변환 메서드 제공 (to_slash, to_dash, to_compact)
- 일관된 대문자 정규화

### MarketStatus 매핑

거래소별 상태값을 MarketStatus enum으로 통일:

**Binance:**
```python
"TRADING" -> MarketStatus.TRADING
"HALT" -> MarketStatus.HALT
"BREAK" -> MarketStatus.BREAK
"PRE_TRADING" -> MarketStatus.PRE_TRADING
"POST_TRADING" -> MarketStatus.POST_TRADING
"AUCTION_MATCH" -> MarketStatus.AUCTION
```

**Upbit:**
```python
# status 필드 없음
None -> MarketStatus.UNKNOWN
```

**Bybit:**
```python
"Trading" -> MarketStatus.TRADING
"Closed" -> MarketStatus.CLOSED
```

**Coinbase:**
```python
trading_disabled=False -> MarketStatus.TRADING
trading_disabled=True -> MarketStatus.HALT
auction_mode=True -> MarketStatus.AUCTION
```

### MarketInfo 객체 도입

**단순한 구조:**
- `symbol: Symbol` - 거래쌍 정보
- `status: MarketStatus` - 거래 상태

**제외된 정보:**
- 거래 규칙 (filters, lot size 등) - 별도 API에서 조회
- 현재가/거래량 - see_ticker에서 조회
- 상세 메타데이터 - 필요 시 별도 API

**이유:**
- see_available_markets는 **"어떤 마켓이 존재하는가"**만 답변
- 상세 정보는 각 마켓별로 별도 조회
- 응답 크기 최소화 및 성능 최적화

### 거래소별 특수 처리

**Bybit - category 필수:**
```python
# Worker에서 처리
categories = ["spot", "linear", "inverse", "option"]
all_markets = []
for category in categories:
    response = api.get_instruments_info(category=category)
    all_markets.extend(response["list"])
```
- 모든 category를 순회하여 전체 마켓 수집
- Worker 내부에서 처리, 사용자는 단일 Response 받음

**Upbit - 심볼 파싱:**
```python
# "KRW-BTC" -> Symbol("BTC/KRW")
market_code = "KRW-BTC"
parts = market_code.split("-")
symbol = Symbol(f"{parts[1]}/{parts[0]}")  # BTC/KRW
```
- Upbit은 "QUOTE-BASE" 순서
- Symbol 생성 시 순서 변경 필요

**Coinbase - 페이지네이션:**
```python
# cursor 기반 페이지네이션
all_products = []
cursor = None
while True:
    response = api.list_products(cursor=cursor)
    all_products.extend(response["products"])
    cursor = response.get("pagination", {}).get("cursor")
    if not cursor:
        break
```
- 전체 마켓 수집 위해 페이지네이션 처리

**한국투자 - 메서드 매핑:**
```python
# fetch_symbols() 또는 fetch_kospi_symbols() + fetch_kosdaq_symbols()
# 크립토 게이트웨이이므로 일단 미지원
# 추후 확장 시 처리
```

### 사용 시나리오

**1. 전체 마켓 조회 (limit 없음):**
```python
response = gateway.execute(SeeAvailableMarketsRequest(
    request_id="req-001",
    gateway_name="binance"
    # limit=None (기본값) - 게이트웨이가 전체 또는 적당한 개수 반환
))

if response.is_success:
    print(f"총 {len(response.markets)}개 마켓")
    for market in response.markets:
        print(f"{market.symbol}: {market.status.name}")
```

**1-1. 개수 제한 조회:**
```python
response = gateway.execute(SeeAvailableMarketsRequest(
    request_id="req-001",
    gateway_name="binance",
    limit=100  # 최대 100개만
))

if response.is_success:
    print(f"조회된 마켓: {len(response.markets)}개 (최대 {100})")
```

**2. USDT 마켓만 필터링:**
```python
response = gateway.execute(SeeAvailableMarketsRequest(
    request_id="req-001",
    gateway_name="binance"
))

usdt_markets = [m for m in response.markets if m.symbol.quote == "USDT"]
print(f"USDT 마켓: {len(usdt_markets)}개")
```

**3. 거래 가능 마켓만 필터링:**
```python
response = gateway.execute(SeeAvailableMarketsRequest(
    request_id="req-001",
    gateway_name="binance"
))

trading_markets = [m for m in response.markets if m.status == MarketStatus.TRADING]
print(f"거래 중인 마켓: {len(trading_markets)}개")
```

**4. 심볼 검증:**
```python
response = gateway.execute(SeeAvailableMarketsRequest(
    request_id="req-001",
    gateway_name="binance"
))

target_symbol = Symbol("BTC/USDT")
is_available = any(m.symbol == target_symbol for m in response.markets)
print(f"BTC/USDT 거래 가능: {is_available}")
```

## 거래소별 API 매핑

### Binance
- **Endpoint:** `GET /api/v3/exchangeInfo`
- **필터링:** 없음 (전체 조회)
- **변환:**
  - `symbol: "BTCUSDT"` → `Symbol("BTC/USDT")` (파싱 필요)
  - `status: "TRADING"` → `MarketStatus.TRADING`

### Upbit
- **Endpoint:** `GET /v1/market/all`
- **필터링:** 없음
- **변환:**
  - `market: "KRW-BTC"` → `Symbol("BTC/KRW")` (순서 변경)
  - 상태 없음 → `MarketStatus.UNKNOWN`

### Bybit
- **Endpoint:** `GET /v5/market/instruments-info`
- **필터링:** category 순회 (spot, linear, inverse, option)
- **변환:**
  - `symbol: "BTCUSDT"` → `Symbol("BTC/USDT")` (파싱 필요)
  - `status: "Trading"` → `MarketStatus.TRADING`

### Coinbase
- **Endpoint:** `GET /api/v3/brokerage/products`
- **페이지네이션:** cursor 기반
- **변환:**
  - `product_id: "BTC-USD"` → `Symbol("BTC/USD")`
  - `trading_disabled: False` → `MarketStatus.TRADING`

### 한국투자
- **API:** `fetch_symbols()`, `fetch_kospi_symbols()`, `fetch_kosdaq_symbols()`
- **현재:** 크립토 게이트웨이이므로 미지원
- **추후:** 한국투자증권용 Gateway 구현 시 추가

## 타임스탬프 처리

`processed_when` 우선순위:
1. 서버 타임스탬프 (Binance serverTime, Upbit 없음)
2. 추정값 `(send_when + receive_when) / 2`

대부분의 거래소는 마켓 목록 조회 시 서버 타임스탬프를 제공하지 않으므로, 중간값 사용이 기본이다.
