# financial-assets

금융 시계열 데이터(캔들스틱)를 효율적으로 저장하고 로드하는 빌딩블록 모듈. Parquet 형식과 timestamp-tick 변환으로 속도와 저장공간을 최적화합니다.

## 설치

```bash
pip install git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/financial-assets
```

## 기본 사용법

### 1. 캔들 데이터 저장

```python
from financial_assets import Candle, StockAddress
import pandas as pd

# 주소 정보 생성
address = StockAddress(
    archetype="stock",
    exchange="nyse",
    tradetype="spot",
    base="tsla",
    quote="usd",
    timeframe="1d"
)

# 캔들 데이터 생성
df = pd.DataFrame({
    't': [1609459200000, 1609545600000, 1609632000000],  # timestamp (ms)
    'h': [100.5, 101.2, 102.8],  # high
    'l': [99.1, 100.0, 101.5],   # low
    'o': [100.0, 100.5, 101.0],  # open
    'c': [100.3, 101.0, 102.5],  # close
    'v': [1000000.0, 1100000.0, 1200000.0]  # volume
})

candle = Candle(address=address, candle_df=df)
candle.save()
# 파일명: stock-nyse-spot-tsla-usd-1d.parquet
```

### 2. 캔들 데이터 로드

```python
from financial_assets import Candle, StockAddress

address = StockAddress(
    archetype="stock",
    exchange="nyse",
    tradetype="spot",
    base="tsla",
    quote="usd",
    timeframe="1d"
)

# 로드
candle = Candle.load(address)

# 마지막 타임스탬프 조회
last_ts = candle.last_timestamp()

# DataFrame 접근
df = candle.candle_df
```

### 3. Price 객체 조회

```python
# 인덱스로 조회
price = candle.get_price_by_iloc(0)
print(price.o, price.h, price.l, price.c, price.v)

# 타임스탬프로 조회
price = candle.get_price_by_timestamp(1609459200000)
```

### 4. Price 범위 메서드

```python
price = candle.get_price_by_iloc(0)

# 확정적 값
body_top = price.bodytop()      # max(o, c)
body_bottom = price.bodybottom()  # min(o, c)

# 범위 반환 (min, max)
body_range = price.body()        # 몸통
head_range = price.head()        # 위 꼬리
tail_range = price.tail()        # 아래 꼬리
headbody_range = price.headbody()  # 위 꼬리 + 몸통
bodytail_range = price.bodytail()  # 몸통 + 아래 꼬리

# 범위 내 랜덤 샘플링
random_body = price.body_sample()
random_head = price.head_sample()
random_tail = price.tail_sample()
```

### 5. 커스텀 저장 경로

```python
# 기본 경로: './data/financial-assets/candles/'
candle = Candle(address=address, basepath='./custom/path/')
candle.save()

# 로드 시에도 동일한 경로 지정
loaded = Candle.load(address, basepath='./custom/path/')
```

## 파일 네이밍 규칙

파일명 형식: `archetype-exchange-tradetype-base-quote-timeframe.parquet`

**예시:**
- `stock-nyse-spot-tsla-usd-1d.parquet`
- `crypto-binance-spot-btc-usdt-1h.parquet`
- `futures-cme-futures-es-usd-15m.parquet`

## 최적화 전략

### 데이터 최적화
- **HLOCV 값**: 소수점 4자리로 round 처리
- **Timestamp**: Tick 변환으로 저장용량 절감
- **저장 형식**: Parquet (압축 + 칼럼형 저장)

### 성능 우선순위
**속도 > 저장용량**

Tick 변환은 최대공약수(GCD) 알고리즘으로 벡터 연산을 활용해 빠르게 처리하며, 동시에 저장공간도 절감합니다.

## 구성 요소

### Candle
캔들스틱 데이터 저장/로드 인터페이스
- `save()`: 파일로 저장
- `load()`: 파일에서 로드 (static)
- `last_timestamp()`: 마지막 타임스탬프
- `get_price_by_iloc()`: 인덱스로 Price 조회
- `get_price_by_timestamp()`: 타임스탬프로 Price 조회

### StockAddress
금융 자산 주소 정보
- `to_filename()`: 파일명으로 변환
- `from_filename()`: 파일명에서 생성 (classmethod)

### Price
개별 가격 데이터 (frozen dataclass)
- 확정 값: `bodytop()`, `bodybottom()`
- 범위: `body()`, `head()`, `tail()`, `headbody()`, `bodytail()`
- 샘플링: `body_sample()`, `head_sample()`, `tail_sample()` 등

## 특징

- **효율적 저장**: Timestamp-Tick 변환 + Parquet 압축
- **간단한 인터페이스**: StockAddress로 파일 관리 자동화
- **Price 유틸리티**: 캔들 범위 조회 및 랜덤 샘플링 기능
- **타입 안전**: dataclass 기반 구조체
