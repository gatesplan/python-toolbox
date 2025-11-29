# see_candles Request/Response 설계

## 개요

캔들스틱(OHLCV) 데이터 조회 요청. 특정 마켓의 과거 가격 데이터를 시계열로 조회한다.

## see_candles Request 파라미터

### 공통 필드 (Request Base)
- `request_id`: 요청 추적 식별자
- `gateway_name`: 대상 Gateway ("binance", "upbit", "simulation")

### 조회 대상

**마켓:**
- `address: StockAddress` - 조회할 마켓 주소 (financial-assets)

**시간 간격:**
- `interval: str` - 캔들 간격 (Binance 형식 사용)
  - 분: "1m", "3m", "5m", "15m", "30m"
  - 시: "1h", "2h", "4h", "6h", "12h"
  - 일: "1d", "3d"
  - 주/월: "1w", "1M"

### 조회 옵션

**시간 범위:**
- `start_time: Optional[int]` - 조회 시작 시각 (UTC 초 단위, None이면 최근 데이터)
  - **예외: Binance는 밀리초 단위 사용**
- `end_time: Optional[int]` - 조회 종료 시각 (UTC 초 단위, None이면 현재)
  - **예외: Binance는 밀리초 단위 사용**

**개수 제한:**
- `limit: Optional[int]` - 조회 개수 (None이면 거래소 기본값)
  - 거래소별 기본값/최대값:
    - Binance: 기본 500, 최대 1000
    - Upbit: 기본 200, 최대 200
    - Bybit: 최대 1000
    - Coinbase: 최대 300

**동작:**
- `start_time`, `end_time` 둘 다 None: 최근 limit개 캔들
- `start_time`만 지정: start_time부터 limit개
- `end_time`만 지정: end_time까지 limit개 (역순)
- 둘 다 지정: start_time ~ end_time 범위

## see_candles Response 구조

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

**candles: pd.DataFrame**

DataFrame 컬럼:
- `timestamp: int` - 캔들 시작 시각 (초 단위, Candle 클래스와 동일)
- `open: float` - 시가
- `high: float` - 고가
- `low: float` - 저가
- `close: float` - 종가
- `volume: float` - 거래량 (base asset 기준)

**정렬:**
- timestamp 오름차순 (과거 → 최신)

**참고:**
- 캔들이 없으면 빈 DataFrame 또는 None 반환
- Candle 클래스와 동일한 DataFrame 형식 (바로 사용 가능)
- timestamp는 초 단위 (Candle 클래스 규칙)

### 실패 시 에러 코드

**데이터 에러:**
- `INVALID_SYMBOL` - 존재하지 않는 심볼
- `MARKET_NOT_FOUND` - 존재하지 않는 마켓
- `INVALID_INTERVAL` - 지원하지 않는 interval

**시간 범위 에러:**
- `INVALID_TIME_RANGE` - 잘못된 시간 범위 (start_time > end_time)
- `TIME_RANGE_TOO_LARGE` - 시간 범위가 너무 큼 (거래소 제한 초과)
- `TOO_MANY_CANDLES` - 요청 캔들 개수 초과 (Coinbase 300개 제한 등)

**시스템 에러:**
- `API_ERROR` - 거래소 API 오류
- `NETWORK_ERROR` - 네트워크 연결 오류
- `RATE_LIMIT_EXCEEDED` - API 호출 한도 초과

## 설계 원칙

### DataFrame 직접 반환

financial-assets의 Candle 클래스와 동일한 DataFrame 형식:
- 별도 변환 없이 바로 Candle 객체 생성 가능
- pandas 의존성은 financial-assets에 이미 존재
- 중복 데이터 없음 (List[Price]는 exchange, market이 모든 항목에 중복)
- 효율적이고 직관적

### Binance 형식 interval 사용

거래소별로 다른 형식을 Binance 형식으로 통일:
- **Binance**: "1m", "5m", "1h", "1d" → 그대로 사용
- **Upbit**: 분 단위만 지원 → "1m", "3m", "5m" 등으로 매핑
- **Bybit**: "1", "5", "60", "D" → Binance 형식으로 변환
- **Coinbase**: 60, 300, 3600, 86400 (초) → "1m", "5m", "1h", "1d"로 변환

**Worker에서 변환:**
```python
# Binance: 그대로
interval_map = {"1m": "1m", "5m": "5m", ...}

# Upbit: 분 단위만
interval_map = {"1m": 1, "5m": 5, "1h": 60, ...}

# Bybit: 문자열
interval_map = {"1m": "1", "5m": "5", "1h": "60", "1d": "D", ...}

# Coinbase: 초 단위
interval_map = {"1m": 60, "5m": 300, "1h": 3600, "1d": 86400, ...}
```

### 시간순 정렬 보장

모든 거래소에서 일관된 정렬:
- timestamp 오름차순 (과거 → 최신)
- 거래소 API가 다른 순서를 제공하면 Gateway에서 재정렬

### limit 처리

- `limit=None`: 거래소 기본값 사용
- `limit=N`: N개 조회
- 거래소 최대값 초과 시: 로깅 경고 후 최대값으로 조정

### 지원 interval 목록

**공통 (모든 거래소):**
- "1m", "5m", "15m", "30m"
- "1h", "4h"
- "1d"

**Binance 추가:**
- "3m", "2h", "6h", "8h", "12h"
- "3d", "1w", "1M"

**Upbit 제한:**
- 분 단위만: "1m", "3m", "5m", "10m", "15m", "30m", "1h" (60분), "4h" (240분)
- 일/주/월: "1d", "1w", "1M" (별도 엔드포인트)

**지원하지 않는 interval:**
- Worker에서 `INVALID_INTERVAL` 에러 반환
- 또는 가장 가까운 interval로 변환 후 로깅 경고

### 거래소별 특이사항

**Binance:**
- 최대 1000개
- startTime/endTime 없으면 최신 캔들
- **타임스탬프: 밀리초 단위 사용**
  - Request: start_time/end_time을 밀리초로 전달
  - Response: API가 반환하는 timestamp를 밀리초 → 초로 변환

**Upbit:**
- 최대 200개
- 분 캔들은 /v1/candles/minutes/{unit}
- 일/주/월은 별도 엔드포인트
- **타임스탬프: 초 단위 사용**
  - Request: start_time/end_time을 초로 전달 (start_time 미지원)
  - Response: API가 반환하는 timestamp가 밀리초이면 초로 변환

**Bybit:**
- 최대 1000개
- category="spot" 필수

**Coinbase:**
- 최대 300개
- start/end 범위와 granularity 조합 시 300개 초과하면 에러
- 큰 범위는 여러 요청으로 분할 필요

### 사용 시나리오

**1. 최근 100개 캔들:**
```python
response = gateway.execute(SeeCandlesRequest(
    request_id="req-001",
    gateway_name="binance",
    address=btc_usdt_address,
    interval="1h",
    limit=100
))

if response.is_success:
    df = response.candles
    print(df)
    # 또는 iterrows 사용
    for idx, row in df.iterrows():
        print(f"{row['timestamp']}: O={row['open']} H={row['high']} L={row['low']} C={row['close']}")
```

**2. 특정 기간 캔들:**
```python
# 일반 거래소 (초 단위)
start = int(datetime(2024, 1, 1).timestamp())
end = int(datetime(2024, 1, 31).timestamp())

response = gateway.execute(SeeCandlesRequest(
    request_id="req-001",
    gateway_name="upbit",
    address=btc_krw_address,
    interval="1d",
    start_time=start,
    end_time=end
))

# Binance (밀리초 단위)
start_ms = int(datetime(2024, 1, 1).timestamp() * 1000)
end_ms = int(datetime(2024, 1, 31).timestamp() * 1000)

response = gateway.execute(SeeCandlesRequest(
    request_id="req-002",
    gateway_name="binance",
    address=btc_usdt_address,
    interval="1d",
    start_time=start_ms,
    end_time=end_ms
))
```

**3. Candle 객체로 변환:**
```python
from financial_assets.candle import Candle
import pandas as pd

response = gateway.execute(SeeCandlesRequest(...))

if response.is_success:
    # DataFrame을 바로 Candle 객체로 전달
    candle = Candle(address=btc_usdt_address, candle_df=response.candles)
    candle.save()
```
