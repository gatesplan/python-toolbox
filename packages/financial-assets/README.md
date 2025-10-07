# financial-assets

금융 시계열 데이터를 효율적으로 처리하는 빌딩블록 모듈.

## 설치

```bash
pip install git+https://github.com/gatesplan/python-toolbox.git#subdirectory=packages/financial-assets
```

## 서브모듈

### Candle
캔들스틱 데이터의 저장/로드를 담당합니다.

**책임:**
- 다양한 저장소 전략 지원 (Parquet, MySQL)
- 범위 기반 조회 (start_ts, end_ts)
- 온메모리 데이터 병합 및 업데이트
- Timestamp↔Tick 변환을 통한 저장 최적화

**세부사항:** `financial_assets/candle/Architecture.md` 참조

### StockAddress
금융 자산의 주소 정보를 표현합니다.

**책임:**
- 자산 식별 정보 관리 (archetype, exchange, tradetype, base, quote, timeframe)
- 파일명/테이블명 변환
- 주소 파싱 및 생성

**구성:**
```python
StockAddress(
    archetype="stock",      # stock, crypto, futures 등
    exchange="nyse",        # 거래소
    tradetype="spot",       # spot, futures 등
    base="tsla",            # 기초자산
    quote="usd",            # 결제통화
    timeframe="1d"          # 타임프레임
)
```

### Price
개별 캔들의 가격 데이터와 관련 유틸리티를 제공합니다.

**책임:**
- HLOCV(High, Low, Open, Close, Volume) 데이터 표현
- 캔들 범위 조회 (body, head, tail)
- 범위 내 랜덤 샘플링

**주요 메서드:**
- 확정 값: `bodytop()`, `bodybottom()`
- 범위: `body()`, `head()`, `tail()`, `headbody()`, `bodytail()`
- 샘플링: `body_sample()`, `head_sample()`, `tail_sample()` 등

## 간단한 사용 예시

```python
from financial_assets import Candle, StockAddress
import pandas as pd

# 주소 생성
address = StockAddress(
    archetype="stock",
    exchange="nyse",
    tradetype="spot",
    base="tsla",
    quote="usd",
    timeframe="1d"
)

# 캔들 데이터 생성 및 저장
df = pd.DataFrame({
    'timestamp': [1609459200, 1609545600],  # Unix timestamp (초 단위)
    'high': [100.5, 101.2],
    'low': [99.1, 100.0],
    'open': [100.0, 100.5],
    'close': [100.3, 101.0],
    'volume': [1000000.0, 1100000.0]
})

candle = Candle(address=address, candle_df=df)
candle.save()

# 로드
loaded = Candle.load(address)
```

## 라이선스

MIT
