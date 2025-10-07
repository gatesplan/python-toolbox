# StockAddress

금융 자산의 고유 주소를 표현하는 식별자 시스템입니다.

## 설계 의도

동일한 ticker라도 거래소, 거래 타입에 따라 서로 다른 마켓으로 취급됩니다:
- **거래소 구분**: TSLA는 NYSE와 다른 거래소에서 다르게 거래될 수 있음
- **거래 타입 구분**: spot, futures, margin 등은 별도 마켓
- **시간 해상도**: 해당 자산 데이터의 최소 tick 해상도 (예: 1d는 일봉 캔들스틱 저장)

`stock-nasdaq-spot-tsla-usd-1d`는 "NASDAQ 거래소의 TSLA/USD spot 거래를 1일 간격 캔들스틱으로 저장"을 의미합니다.

## 사용법

### 초기화

```python
from financial_assets import StockAddress

# 기본 생성
address = StockAddress(
    archetype="stock",      # 자산 유형 (stock, crypto, futures 등)
    exchange="nasdaq",      # 거래소
    tradetype="spot",       # 거래 타입 (spot, futures, margin 등)
    base="tsla",            # 기준 자산
    quote="usd",            # 견적 통화
    timeframe="1d"          # 최소 tick 해상도 (1m, 5m, 1h, 1d 등)
)

# 암호화폐 예시
crypto_address = StockAddress(
    archetype="crypto",
    exchange="binance",
    tradetype="spot",
    base="btc",
    quote="usdt",
    timeframe="1h"
)

# 암호화폐 선물 예시
futures_address = StockAddress(
    archetype="crypto",
    exchange="binance",
    tradetype="futures",
    base="btc",
    quote="usd",
    timeframe="15m"
)
```

### to_filename()

주소를 파일명 형식으로 변환합니다.

```python
address = StockAddress(
    archetype="stock",
    exchange="nasdaq",
    tradetype="spot",
    base="tsla",
    quote="usd",
    timeframe="1d"
)

filename = address.to_filename()
print(filename)
# 출력: stock-nasdaq-spot-tsla-usd-1d
```

### from_filename()

파일명에서 StockAddress 객체를 생성합니다.

```python
# .parquet 확장자 포함/미포함 모두 가능
address1 = StockAddress.from_filename("stock-nasdaq-spot-tsla-usd-1d")
address2 = StockAddress.from_filename("stock-nasdaq-spot-tsla-usd-1d.parquet")

print(address1.exchange)   # nasdaq
print(address1.base)       # tsla
print(address1.timeframe)  # 1d
```

## 주소 형식

```
archetype-exchange-tradetype-base-quote-timeframe
```

**예시:**
- `stock-nyse-spot-aapl-usd-1d` → NYSE의 AAPL 주식, spot 거래, 일봉
- `crypto-binance-spot-btc-usdt-1h` → Binance의 BTC/USDT, spot 거래, 시간봉
- `crypto-binance-futures-btc-usd-1m` → Binance의 BTC 선물, 1분봉
- `stock-nasdaq-margin-tsla-usd-5m` → NASDAQ의 TSLA 마진 거래, 5분봉
