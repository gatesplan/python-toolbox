# Symbol 객체 지원 현황 분석

## 현재 상태

### Symbol을 이미 사용하는 곳
```python
# Portfolio.py (Core Layer) ✅
def get_available_position(self, ticker: Union[str, Symbol]) -> float
def get_locked_position(self, ticker: Union[str, Symbol]) -> float
def lock_position(self, promise_id: str, ticker: Union[str, Symbol], amount: float)

# MarketDataService.py (Service Layer) ✅
from financial_assets.symbol import Symbol  # import 있음

def get_available_markets(self) -> list[dict]:
    # Symbol 객체 반환
    return [{"symbol": Symbol(symbol_str), "status": MarketStatus.TRADING}, ...]
```

### Symbol을 사용하지 않는 곳
```python
# MarketData.py (Core Layer) ❌
def get_current(self, symbol: str) -> Price  # str만 받음
# Symbol import 없음

# OrderBook.py (Core Layer) ❌
def get_orders_by_symbol(self, symbol: str) -> list[SpotOrder]  # str만 받음
# Symbol import 없음
# 하지만 내부적으로는 Symbol 사용:
def _get_symbol(self, order: SpotOrder) -> str:
    return order.stock_address.to_symbol().to_slash()  # StockAddress → Symbol 변환

# MarketDataService.py (Service Layer) ❌
def generate_orderbook(self, symbol: str, depth: int = 20)  # str만 받음

# SpotExchange.py (API Layer) ❌
def get_current_price(self, symbol: str) -> float | None  # str만 받음
def get_orderbook(self, symbol: str, depth: int = 20)  # str만 받음
# Symbol import 없음
```

## 문제점

### 1. 아키텍처 일관성 부족
- **Portfolio**: Symbol 지원 ✅
- **MarketData, OrderBook**: Symbol 미지원 ❌
- **SpotExchange**: Symbol 미지원 ❌

→ 같은 Core Layer인데 Portfolio만 Symbol을 지원

### 2. 내부 모순
```python
# OrderBook은 내부적으로 Symbol을 사용
order.stock_address.to_symbol().to_slash()

# 하지만 외부 API는 str만 받음
get_orders_by_symbol(symbol: str)
```

### 3. Service Layer 불일치
```python
# MarketDataService
get_available_markets() -> list[dict]  # Symbol 객체 반환 ✅
generate_orderbook(symbol: str)        # str만 받음 ❌
```

## 근본 원인

### financial-assets의 제약
```python
# MultiCandle.get_snapshot() 반환 타입
dict[str, Price]  # str 키 사용 (Symbol 아님)
```

**하지만 이것은 내부 구현 문제일 뿐, API 설계와는 별개입니다.**

## 올바른 설계

### 계층별 역할

#### API Layer (SpotExchange)
```python
# 사용자 인터페이스 - 도메인 객체 사용
def get_current_price(self, symbol: str | Symbol) -> float | None
def get_position(self, symbol: str | Symbol) -> float
```

#### Core Layer (MarketData, OrderBook, Portfolio)
```python
# 비즈니스 로직 - 도메인 객체 지원
def get_current(self, symbol: str | Symbol) -> Price
def get_orders_by_symbol(self, symbol: str | Symbol) -> list[SpotOrder]
def get_available_position(self, ticker: str | Symbol) -> float  # ✅ 이미 구현됨
```

#### 내부 저장소 (dict, index)
```python
# 성능을 위한 str 키 사용 (내부적으로 변환)
self._symbol_index: dict[str, set[str]]  # str 키
self._multicandle.get_snapshot(ts) -> dict[str, Price]  # str 키
```

### 변환 로직
```python
# Core Layer에서 변환 처리
def get_current(self, symbol: str | Symbol) -> Price:
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    # 내부 dict[str, ...] 접근
    return self._snapshot[symbol_str]
```

## 결론

**현재 구현이 잘못되었습니다:**

1. ❌ Symbol import 누락 (MarketData, OrderBook, SpotExchange)
2. ❌ 타입 힌트에 Symbol 미지원
3. ❌ Portfolio만 Symbol 지원 (일관성 부족)
4. ❌ OrderBook은 내부적으로 Symbol 사용하지만 API는 str만 받음

**올바른 방향:**

1. ✅ 모든 Layer에서 `str | Symbol` 지원
2. ✅ 내부적으로 str로 변환 (성능)
3. ✅ API는 도메인 객체(Symbol) 우선
4. ✅ Portfolio 패턴을 MarketData, OrderBook에도 적용

## 수정 계획

### Phase 1: Core Layer Symbol 지원 추가

#### MarketData.py
```python
from financial_assets.symbol import Symbol
from financial_assets.price import Price
from typing import Union

def get_current(self, symbol: Union[str, Symbol]) -> Price:
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    current_timestamp = int(self._timestamps[self._cursor_idx])
    snapshot = self._multicandle.get_snapshot(current_timestamp, as_price=True)

    if symbol_str not in snapshot:
        raise KeyError(f"Symbol {symbol_str} not found")

    return snapshot[symbol_str]
```

#### OrderBook.py
```python
from financial_assets.symbol import Symbol
from typing import Union

def get_orders_by_symbol(self, symbol: Union[str, Symbol]) -> list[SpotOrder]:
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    order_ids = self._symbol_index.get(symbol_str, set())
    return [self._orders[oid] for oid in order_ids]
```

### Phase 2: Service Layer Symbol 지원 추가

#### MarketDataService.py
```python
def generate_orderbook(self, symbol: Union[str, Symbol], depth: int = 20) -> Orderbook:
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    price_data = self._market_data.get_current(symbol_str)
    ...
```

### Phase 3: API Layer Symbol 지원 추가

#### SpotExchange.py
```python
from financial_assets.symbol import Symbol
from typing import Union

def get_current_price(self, symbol: Union[str, Symbol]) -> float | None:
    price_data = self._market_data.get_current(symbol)  # MarketData가 이미 변환 처리
    if price_data is None:
        return None
    return price_data.c

def get_open_orders(self, symbol: Union[str, Symbol, None] = None) -> list[SpotOrder]:
    if symbol is None:
        return self._orderbook.get_all_orders()
    return self._orderbook.get_orders_by_symbol(symbol)  # OrderBook이 이미 변환 처리
```

## 우선순위

1. **HIGH**: Core Layer (MarketData, OrderBook) Symbol 지원
   - 이것이 근본 원인
   - Portfolio는 이미 구현됨

2. **HIGH**: Service Layer Symbol 지원
   - MarketDataService.generate_orderbook

3. **MEDIUM**: API Layer Symbol 지원
   - SpotExchange 모든 메서드
   - Core가 지원하면 자동으로 가능

4. **MEDIUM**: 누락된 메서드 추가
   - get_position, get_available_position 등

5. **LOW**: 문서화
   - Docstring에 str | Symbol 명시
