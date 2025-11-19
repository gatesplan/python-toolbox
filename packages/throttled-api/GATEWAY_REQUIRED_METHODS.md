# UpbitSpotGateway 구현을 위한 필수 메서드 분석

## 분석 기준
- **대상**: financial-gateway의 SpotMarketGatewayBase 인터페이스
- **목적**: UpbitSpotGateway 구현에 필요한 Upbit API 메서드 식별
- **현재 throttled-api 구현 상태**: UpbitSpotThrottler 28개 메서드

---

## 1. SpotMarketGatewayBase 인터페이스 요구사항

### 🔴 필수 구현 메서드 (13개)

| Gateway 메서드 | 목적 | Request 타입 | Response 타입 |
|---------------|------|-------------|---------------|
| `request_limit_buy_order` | 지정가 매수 주문 | LimitBuyOrderRequest | OpenSpotOrderResponse |
| `request_limit_sell_order` | 지정가 매도 주문 | LimitSellOrderRequest | OpenSpotOrderResponse |
| `request_market_buy_order` | 시장가 매수 주문 | MarketBuyOrderRequest | OpenSpotOrderResponse |
| `request_market_sell_order` | 시장가 매도 주문 | MarketSellOrderRequest | OpenSpotOrderResponse |
| `request_cancel_order` | 주문 취소 | CloseOrderRequest | CloseLimitOrderResponse |
| `request_order_status` | 주문 상태 조회 | OrderCurrentStateRequest | OrderCurrentStateResponse |
| `request_current_balance` | 잔고 조회 | CurrentBalanceRequest | CurrentBalanceResponse |
| `request_trade_history` | 체결 내역 조회 | TradeInfoRequest | TradeInfoResponse |
| `request_ticker` | 현재가 조회 | TickerRequest | TickerResponse |
| `request_orderbook` | 호가 조회 | OrderbookRequest | OrderbookResponse |
| `request_candles` | 캔들 데이터 조회 | PriceDataRequest | PriceDataResponse |
| `request_available_markets` | 마켓 목록 조회 | AvailableMarketsRequest | AvailableMarketsResponse |
| `request_server_time` | 서버 시간 조회 | - | ServerTimeResponse |

---

## 2. Upbit API 매핑 (throttled-api 기준)

### 🔴 필수 - 주문 관리 (6개 Gateway 메서드 → 4개 Upbit API)

| Gateway 메서드 | Upbit API 메서드 | 구현 상태 | 시그니처 | 비고 |
|---------------|-----------------|----------|---------|------|
| `request_limit_buy_order` | `create_order` | ✅ | `(market, side="bid", ord_type="limit", volume, price, identifier?)` | |
| `request_limit_sell_order` | `create_order` | ✅ | `(market, side="ask", ord_type="limit", volume, price, identifier?)` | |
| `request_market_buy_order` | `create_order` | ✅ | `(market, side="bid", ord_type="price", price, identifier?)` | 총액 지정 |
| `request_market_sell_order` | `create_order` | ✅ | `(market, side="ask", ord_type="market", volume, identifier?)` | 수량 지정 |
| `request_cancel_order` | `cancel_order` | ✅ | `(uuid?, identifier?)` | 둘 중 하나 필수 |
| `request_order_status` | `get_order` | ✅ | `(uuid?, identifier?)` | 개별 주문 조회 |

**누락 파라미터 (중요도 중)**:
- `create_order`에 `time_in_force`, `smp_type` 누락
  - IOC/FOK 주문 및 자전거래 방지 기능 사용 불가
  - 추후 보강 권장 (우선순위 2)

---

### 🔴 필수 - 계정 정보 (2개 Gateway 메서드 → 2개 Upbit API)

| Gateway 메서드 | Upbit API 메서드 | 구현 상태 | 시그니처 | 비고 |
|---------------|-----------------|----------|---------|------|
| `request_current_balance` | `get_accounts` | ✅ | `()` | 전체 계좌 잔고 |
| `request_trade_history` | ⚠️ **미확정** | ❓ | - | 아래 참조 |

**request_trade_history 구현 옵션**:

1. **Option A: get_orders() 사용** (현재 구현됨 ✅)
   - 시그니처: `get_orders(market?, state="done", ...)`
   - 장점: 이미 구현됨, 체결된 주문 목록 조회 가능
   - 단점: 주문 단위 조회 (여러 체결로 나뉜 주문은 별도 API 필요)

2. **Option B: 개별 주문의 체결 내역 API 사용** ❌
   - Upbit에는 **개별 주문의 상세 체결 내역을 반환하는 별도 API 없음**
   - `get_order(uuid)`는 주문 정보만 반환 (체결 분할 정보 제한적)

3. **Option C: get_orders_closed() 사용** (현재 구현됨 ✅)
   - 시그니처: `get_orders_closed(market?, state?, start_time?, end_time?, ...)`
   - 장점: 종료된 주문 조회 (done, cancel), 시간 범위 지정 가능
   - 추천: **이 방식 사용**

**결론**: `get_orders_closed()`를 `request_trade_history()` 백엔드로 사용 권장

---

### 🔴 필수 - 시장 데이터 (5개 Gateway 메서드 → 5개 Upbit API)

| Gateway 메서드 | Upbit API 메서드 | 구현 상태 | 시그니처 | 비고 |
|---------------|-----------------|----------|---------|------|
| `request_ticker` | `get_ticker` | ✅ | `(markets: List[str])` | 현재가 정보 |
| `request_orderbook` | `get_orderbook` | ✅ | `(markets: List[str])` | 호가 정보 |
| `request_candles` | `get_candles_*` | ✅ | 아래 참조 | 4개 메서드 |
| `request_available_markets` | `get_market_all` | ✅ | `(is_details=False)` | 마켓 목록 |
| `request_server_time` | ❌ **미구현** | ❌ | - | Upbit API 없음 |

**캔들 API 상세** (모두 구현됨 ✅):
- `get_candles_minutes(unit, market, to?, count=1)`
- `get_candles_days(market, to?, count=1, converting_price_unit?)`
- `get_candles_weeks(market, to?, count=1)`
- `get_candles_months(market, to?, count=1)`

**request_server_time 대응 방안**:
1. **Option A: 로컬 시간 사용**
   - `datetime.now(timezone.utc)` 반환
   - 단점: 클라이언트-서버 시간 차이 발생 가능

2. **Option B: API 응답 헤더에서 시간 추출**
   - HTTP Response의 `Date` 헤더 파싱
   - 장점: 서버 시간 근사치 확보
   - 추천: **이 방식 사용**

3. **Option C: 더미 API 호출**
   - `get_market_all()` 호출 후 응답 시간 사용
   - 장점: 간단함
   - 단점: rate limit 소모

**결론**: HTTP 응답 헤더의 `Date` 필드를 파싱하여 서버 시간 반환 권장

---

## 3. 필수 메서드 구현 현황 요약

### ✅ 완전 구현 (10/13)

| 카테고리 | Gateway 메서드 | Upbit API | 상태 |
|---------|---------------|-----------|------|
| **주문** | request_limit_buy_order | create_order | ✅ |
| **주문** | request_limit_sell_order | create_order | ✅ |
| **주문** | request_market_buy_order | create_order | ✅ |
| **주문** | request_market_sell_order | create_order | ✅ |
| **주문** | request_cancel_order | cancel_order | ✅ |
| **주문** | request_order_status | get_order | ✅ |
| **계정** | request_current_balance | get_accounts | ✅ |
| **시장** | request_ticker | get_ticker | ✅ |
| **시장** | request_orderbook | get_orderbook | ✅ |
| **시장** | request_available_markets | get_market_all | ✅ |

### ⚠️ 부분 구현 / 대응 필요 (2/13)

| Gateway 메서드 | 상태 | 대응 방안 |
|---------------|------|----------|
| `request_trade_history` | ⚠️ | `get_orders_closed()` 사용 (구현됨) |
| `request_candles` | ⚠️ | 4개 캔들 API 중 적절히 선택 (모두 구현됨) |

### ❌ 미구현 (1/13)

| Gateway 메서드 | 상태 | 대응 방안 |
|---------------|------|----------|
| `request_server_time` | ❌ | HTTP 응답 헤더 `Date` 파싱 또는 로컬 시간 사용 |

---

## 4. throttled-api에서 Gateway 구현에 필요한 메서드만 추출

### 🔴 필수 (11개)

#### 주문 관리 (4개)
1. ✅ `create_order(market, side, ord_type, volume?, price?, identifier?)`
   - 4가지 주문 유형 모두 지원
   - ⚠️ `time_in_force`, `smp_type` 추가 권장

2. ✅ `cancel_order(uuid?, identifier?)`
   - 주문 취소

3. ✅ `get_order(uuid?, identifier?)`
   - 개별 주문 상태 조회

4. ✅ `get_orders_closed(market?, state?, start_time?, end_time?, page=1, limit=100, order_by="desc")`
   - **체결 내역 조회용**

#### 계정 정보 (1개)
5. ✅ `get_accounts()`
   - 잔고 조회

#### 시장 데이터 (6개)
6. ✅ `get_ticker(markets: List[str])`
   - 현재가 조회

7. ✅ `get_orderbook(markets: List[str])`
   - 호가 조회

8. ✅ `get_candles_minutes(unit, market, to?, count=1)`
   - 분봉 캔들

9. ✅ `get_candles_days(market, to?, count=1, converting_price_unit?)`
   - 일봉 캔들

10. ✅ `get_candles_weeks(market, to?, count=1)`
    - 주봉 캔들

11. ✅ `get_candles_months(market, to?, count=1)`
    - 월봉 캔들

12. ✅ `get_market_all(is_details=False)`
    - 마켓 목록

---

### 🟡 선택적 - Gateway 고급 기능용 (6개)

| 메서드 | 용도 | 우선순위 |
|-------|------|---------|
| `get_orders(market?, state?, ...)` | 주문 목록 조회 (필터링) | 중 |
| `get_orders_chance(market)` | 주문 가능 정보 (수수료, 제한) | 중 |
| `get_orders_open(market?, ...)` | 미체결 주문 조회 | 중 |
| `get_candles_*` (나머지) | 추가 타임프레임 | 낮음 |
| `get_trades_ticks(market, ...)` | 최근 체결 내역 (실시간 분석용) | 낮음 |
| `get_api_keys()` | API 키 관리 | 낮음 |

---

### 🟢 불필요 - Gateway 구현에 사용 안 함 (11개)

입출금 관련 API는 Gateway에서 사용하지 않음 (별도 자산 관리 시스템에서 처리):

- ❌ `get_deposits()`, `get_deposit()` - 입금 조회
- ❌ `get_coin_addresses()`, `get_coin_address()` - 입금 주소 조회
- ❌ `generate_coin_address()` - 입금 주소 생성
- ❌ `create_krw_deposit()` - 원화 입금
- ❌ `get_withdraws()`, `get_withdraw()` - 출금 조회
- ❌ `get_withdraws_chance()` - 출금 가능 정보
- ❌ `withdraw_coin()` - 코인 출금
- ❌ `withdraw_krw()` - 원화 출금

---

## 5. 시그니처 이슈 및 개선 사항

### ⚠️ 우선순위 1: create_order 파라미터 추가

**현재**:
```python
create_order(
    market: str,
    side: str,
    ord_type: str,
    volume: Optional[str] = None,
    price: Optional[str] = None,
    identifier: Optional[str] = None
) -> dict
```

**권장**:
```python
create_order(
    market: str,
    side: str,
    ord_type: str,
    volume: Optional[str] = None,
    price: Optional[str] = None,
    identifier: Optional[str] = None,
    time_in_force: Optional[str] = None,  # 추가: IOC, FOK, post_only
    smp_type: Optional[str] = None,       # 추가: 자전거래 방지
) -> dict
```

**영향도**:
- IOC/FOK 주문 불가 (현재)
- 자전거래 방지 기능 사용 불가
- Gateway에서 고급 주문 전략 구현 제한

**조치**: 하위 호환성 유지하며 선택적 파라미터로 추가

---

### ⚠️ 우선순위 2: 서버 시간 조회 구현

**미구현**: `request_server_time()`

**대응 방안**:
1. APICallExecutor에 HTTP 응답 헤더 접근 추가
2. `Date` 헤더 파싱 유틸리티 구현
3. 모든 API 호출 시 서버 시간 기록

**구현 예시**:
```python
# throttled_api/providers/upbit/UpbitSpotThrottler.py

async def get_server_time(self) -> datetime:
    """
    서버 시간 조회 (HTTP 응답 헤더 Date 파싱)

    더미 API 호출 후 응답 헤더에서 시간 추출
    """
    # get_market_all() 호출하여 응답 헤더 확보
    response = await self.client.get_market_all_raw()  # 헤더 포함 반환
    date_header = response.headers.get("Date")
    return parse_http_date(date_header)
```

---

## 6. 최종 결론

### ✅ UpbitSpotGateway 구현 가능 여부

**결론**: **충분히 구현 가능** (95% 완성도)

### 필수 메서드 구현률

- **주문 관리**: 4/4 (100%) ✅
  - create_order, cancel_order, get_order, get_orders_closed

- **계정 정보**: 1/1 (100%) ✅
  - get_accounts

- **시장 데이터**: 6/7 (85%) ⚠️
  - get_ticker, get_orderbook, get_candles_*, get_market_all
  - ❌ 서버 시간 조회만 미구현 (대응 가능)

### 추가 작업 필요 사항

1. **필수 (Gateway 구현 전)**:
   - ❌ `get_server_time()` 구현 (HTTP 헤더 파싱)
   - 작업량: 소 (1~2시간)

2. **권장 (Gateway 구현 후)**:
   - ⚠️ `create_order()`에 `time_in_force`, `smp_type` 추가
   - 작업량: 소 (1시간)

3. **선택적**:
   - 🟡 `get_orders_chance()` 활용 (주문 전 검증)
   - 🟡 `get_orders_open()` 활용 (미체결 관리)

### Gateway 계층 구조에서 추가 구현 필요 컴포넌트

#### Upbit Spot Gateway 모듈 (upbit_spot/)

**Controller Layer**:
- ✅ UpbitSpotGateway.py (SpotMarketGatewayBase 구현)

**Service Layer**:
- ✅ OrderRequestService (create/cancel)
- ✅ OrderQueryService (get_order, get_orders_closed)
- ✅ BalanceService (get_accounts)
- ✅ MarketDataService (ticker, orderbook, candles, market_all)

**Core Layer**:
- ✅ RequestConverter (Request → Upbit API params)
- ✅ ResponseParser (Upbit API response → Response)
- ✅ APICallExecutor (UpbitSpotThrottler 래핑)

**Particles Layer**:
- ✅ upbit_endpoints.py (이미 throttled-api에 있음)
- ✅ upbit_config.py (타임아웃, 재시도 설정)

---

## 7. 다음 단계 작업 계획

### Phase 1: 기반 작업 (throttled-api)
1. ✅ UpbitSpotThrottler에 `get_server_time()` 추가
2. ⚠️ `create_order()`에 `time_in_force`, `smp_type` 파라미터 추가 (선택)

### Phase 2: Gateway 구조 생성 (financial-gateway)
1. upbit_spot/ 디렉토리 생성 (CPSCP 구조)
2. Particles 계층 구현 (upbit_endpoints, upbit_config, api_params)
3. Core 계층 구현 (RequestConverter, ResponseParser, APICallExecutor)
4. Service 계층 구현 (4개 서비스)
5. Controller 구현 (UpbitSpotGateway)

### Phase 3: 테스트 및 검증
1. 단위 테스트 (각 계층별)
2. 통합 테스트 (실제 API 호출)
3. BinanceSpotGateway와 인터페이스 일관성 검증

---

## 부록: Upbit vs Binance 메서드 매핑 비교

| Gateway 메서드 | Binance API | Upbit API | 차이점 |
|---------------|-------------|-----------|--------|
| request_limit_buy | new_order(type=LIMIT) | create_order(ord_type=limit) | 파라미터 구조 다름 |
| request_market_buy | new_order(type=MARKET) | create_order(ord_type=price) | Upbit은 총액 지정 |
| request_cancel | cancel_order | cancel_order | 유사 |
| request_order_status | get_order | get_order | 유사 |
| request_balance | account | get_accounts | 응답 구조 다름 |
| request_ticker | ticker_price | get_ticker | markets 리스트 vs symbol |
| request_orderbook | depth | get_orderbook | markets 리스트 vs symbol |
| request_candles | klines | get_candles_* | 4개 메서드로 분리됨 |
| request_markets | exchange_info | get_market_all | 응답 구조 다름 |
| request_server_time | time | ❌ 없음 | 대응 필요 |

**주요 차이점**:
1. Binance: symbol 단일 지정 / Upbit: markets 리스트 지정
2. Binance: 통합 new_order / Upbit: 분리된 ord_type
3. Binance: server time API 제공 / Upbit: 미제공 (헤더 파싱 필요)
