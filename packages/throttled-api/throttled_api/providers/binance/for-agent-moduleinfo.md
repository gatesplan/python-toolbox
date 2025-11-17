# throttled_api.providers.binance

Binance Spot API Provider - Wrapper 패턴으로 Binance 클라이언트에 throttle 적용

## 개요

Binance Spot API의 rate limit을 관리하는 throttler. 기존 Binance 클라이언트(python-binance, binance-connector-python 등)를 감싸서 rate limit 체크만 수행하는 wrapper 패턴.

## Rate Limit 정책 (Binance Spot API)

- **REQUEST_WEIGHT**: 분당 6000 weight (IP 기반, FixedWindow)
- **ORDERS**: 10초당 50개 (FixedWindow)
- **ORDERS**: 일당 160000개 (FixedWindow)
- **RAW_REQUESTS**: 5분당 61000개 (선택적, 보수적 제한)

## endpoints.py

엔드포인트별 REQUEST_WEIGHT 정의 모듈

```
SPOT_ENDPOINT_WEIGHTS: Dict[Tuple[str, str], int]
    (method, endpoint) -> weight 매핑

get_depth_weight(limit: int) -> int
    /api/v3/depth 엔드포인트의 limit에 따른 weight 계산
    limit <= 100: 5
    limit <= 500: 10
    limit <= 1000: 20
    limit <= 5000: 50

get_ticker_24hr_weight(symbols: int = 1) -> int
    /api/v3/ticker/24hr 엔드포인트의 symbol 개수에 따른 weight
    1개: 2
    20개 이하: 40
    100개 이하: 40
    100개 초과 (전체): 80

get_ticker_price_weight(symbols: int = 1) -> int
    /api/v3/ticker/price 엔드포인트의 weight
    1개: 2
    전체: 4

get_ticker_book_ticker_weight(symbols: int = 1) -> int
    /api/v3/ticker/bookTicker 엔드포인트의 weight
    1개: 2
    전체: 4

get_open_orders_weight(has_symbol: bool) -> int
    /api/v3/openOrders 엔드포인트의 weight
    symbol 있음: 6
    symbol 없음 (전체): 80

get_exchange_info_weight(has_symbol: bool) -> int
    /api/v3/exchangeInfo 엔드포인트의 weight
    symbol 있음: 2
    symbol 없음 (전체): 20
```

**주요 엔드포인트 weight**:
- /api/v3/ping: 1
- /api/v3/time: 1
- /api/v3/order (POST): 1
- /api/v3/account: 20
- /api/v3/allOrders: 20
- /api/v3/myTrades: 20

## BinanceSpotThrottler

BaseThrottler를 상속한 Binance Spot API 전용 throttler

```
client: Any                     # 주입받은 Binance 클라이언트
warning_threshold: float        # weight drift 경고 임계값 (0.0 ~ 1.0)
weight_pipeline: Pipeline       # REQUEST_WEIGHT_1M Pipeline
order_pipeline_10s: Pipeline    # ORDERS_10S Pipeline

__init__(client, warning_threshold=0.2, enable_raw_requests_limit=False)
    client: 기존 Binance 클라이언트 객체
    warning_threshold: 서버/로컬 weight 차이 경고 임계값
    enable_raw_requests_limit: RAW_REQUESTS 제한 활성화 여부

get_weight(method: str, endpoint: str, params: Optional[Dict] = None) -> int
    엔드포인트와 파라미터로 REQUEST_WEIGHT 계산
    특수 케이스 (depth, ticker 등) 처리

is_order_endpoint(method: str, endpoint: str) -> bool
    주문 관련 엔드포인트 판단
    POST 메서드 + 주문 엔드포인트 패턴 매칭

async request(method: str, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Any
    Throttle 적용된 API 요청 wrapper
    1. weight 계산
    2. _check_and_wait() 호출 (자동 대기)
    3. client.request() 호출
    4. 응답 헤더에서 weight drift 체크

async _call_client(method: str, endpoint: str, params: Optional[Dict], **kwargs) -> Any
    클라이언트 호출 추상화
    client.request() 또는 client.get(), client.post() 등 지원
```

### Weight Drift 체크

```
_check_weight_drift(headers: Dict) -> None
    응답 헤더 X-MBX-USED-WEIGHT-1M 파싱
    서버 사용량과 로컬 사용량 비교
    diff_rate = |server_used - local_used| / weight_limit
    diff_rate > warning_threshold 시 logger.warning 발행
```

**경고 예시**:
```
[Weight Drift] server=100, local=50, diff=0.83% (threshold=20.0%)
```

## 사용 예시

### 기본 사용

```python
from throttled_api.providers.binance import BinanceSpotThrottler
from binance.client import AsyncClient  # 예시

# Binance 클라이언트 생성
binance_client = AsyncClient(api_key="...", api_secret="...")

# Throttler로 감싸기
throttler = BinanceSpotThrottler(client=binance_client)

# throttler를 통해 요청
response = await throttler.request("GET", "/api/v3/ticker/price", {"symbol": "BTCUSDT"})
```

### Weight 계산

```python
# 수동 weight 확인
weight = throttler.get_weight("GET", "/api/v3/depth", {"limit": 1000})
print(f"Weight: {weight}")  # Weight: 20

# 자동 대기
await throttler.request("GET", "/api/v3/depth", {"symbol": "BTCUSDT", "limit": 1000})
# weight=20 소비, 자동으로 throttle 체크 후 요청
```

### Weight Drift 모니터링

```python
import logging

logging.basicConfig(level=logging.WARNING)

# 임계값 10%로 설정 (더 민감하게)
throttler = BinanceSpotThrottler(
    client=binance_client,
    warning_threshold=0.1
)

# 요청 시 자동으로 drift 체크
await throttler.request("GET", "/api/v3/account")

# 로그 출력:
# WARNING:throttled_api.providers.binance.BinanceSpotThrottler:[Weight Drift] ...
```

### 이벤트 리스너 등록

```python
def on_threshold_event(event):
    print(f"[ALERT] {event.timeframe}: {event.remaining_rate:.1%} remaining")

throttler.add_event_listener(on_threshold_event)

# weight 80% 사용 시 이벤트 발행
# 출력: [ALERT] REQUEST_WEIGHT_1M: 19.5% remaining
```

## 테스트 커버리지

- endpoints.py: 23 tests
- BinanceSpotThrottler.py: 23 tests
- 총 46 tests 통과

**테스트 항목**:
- 엔드포인트 weight 계산 (기본, 특수 케이스)
- weight 소비 및 누적
- 주문 엔드포인트 감지
- weight drift 체크
- 동시성 제어
- 클라이언트 wrapper 호출

## 주의사항

1. **Wrapper 패턴**: 직접 HTTP 요청하지 않음, client 주입 필요
2. **Weight 정확성**: endpoints.py의 weight 값은 공식 문서 기준, 정기적 업데이트 필요
3. **클라이언트 호환성**: client.request() 또는 client.get()/post() 메서드 필요
4. **IP 기반 제한**: Binance rate limit은 API key가 아닌 IP 기반
5. **헤더 의존성**: weight drift 체크는 X-MBX-USED-WEIGHT-1M 헤더 필요

## 향후 개선

- [ ] exchangeInfo에서 실시간 weight 정보 파싱
- [ ] 서버 weight와 자동 동기화 옵션
- [ ] Binance Futures, Margin API 지원
- [ ] 더 많은 클라이언트 패턴 지원
