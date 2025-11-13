# StockAddress
거래소와 거래쌍 정보를 표현하는 주소 체계. 시장 정보를 표준화된 형식으로 캡슐화.
@dataclass로 구현되어 자동으로 __init__, __repr__, __eq__ 제공.

archetype: str    # 자산 유형 (stock, crypto, futures 등)
exchange: str     # 거래소
tradetype: str    # 거래 타입 (spot, futures, margin 등)
base: str         # 기준 자산
quote: str        # 견적 통화
timeframe: str    # 최소 tick 해상도 (1m, 5m, 1h, 1d 등)

__init__(archetype: str, exchange: str, tradetype: str, base: str, quote: str, timeframe: str)
    StockAddress 초기화 (dataclass 자동 생성)

to_filename() -> str
    하이픈으로 구분된 파일명 형식으로 변환. 예: "crypto-binance-spot-btc-usdt-1h"

to_tablename() -> str
    언더스코어로 구분된 테이블명 형식으로 변환. 예: "crypto_binance_spot_btc_usdt_1h"

to_symbol() -> Symbol
    거래쌍 심볼 객체 생성. base/quote를 Symbol 객체로 반환.
    예: StockAddress(base="btc", quote="usdt").to_symbol() -> Symbol("BTC/USDT")

from_filename(filename: str) -> StockAddress
    raise ValueError
    파일명 문자열 파싱하여 StockAddress 생성. .parquet 확장자 자동 제거.

---

**주소 형식:**
- 파일명: archetype-exchange-tradetype-base-quote-timeframe
- 테이블명: archetype_exchange_tradetype_base_quote_timeframe

**Symbol 연계:**
- to_symbol()로 Symbol 객체 생성 가능
- Symbol은 다양한 형식으로 출력 (slash, dash, compact)
- base, quote는 소문자로 저장되나 Symbol 생성시 자동 대문자 변환

**dataclass 자동 제공 기능:**
- __init__: 모든 필드를 파라미터로 받는 초기화
- __repr__: 개발자용 문자열 표현
- __eq__: 모든 필드 값 비교를 통한 동등성 검사
- 필드는 불변(frozen=False)이므로 수정 가능

**사용 예시:**
```python
address = StockAddress.from_filename("crypto-binance-spot-btc-usdt-1h")
symbol = address.to_symbol()  # Symbol("BTC/USDT")
symbol.to_slash()   # "BTC/USDT"
symbol.to_dash()    # "BTC-USDT"
symbol.to_compact() # "BTCUSDT"
```
