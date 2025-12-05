# SpotExchange API 타입 일관성 개선 계획

## 1. 현재 구조 분석

### StockAddress vs Symbol 용도
- **StockAddress**: 전체 거래 정보 (exchange, market_type, base, quote, timeframe)
  - 주문 생성 시 필수: `SpotOrder.stock_address`
  - `to_symbol()` → Symbol 변환

- **Symbol**: 거래쌍만 (base, quote)
  - 조회 시 사용: 가격, 주문 내역, 포지션
  - `to_slash()` → "BTC/USDT" (MarketData, OrderBook 인덱싱용)
  - `to_dash()` → "BTC-USDT" (Portfolio ticker용)

### 현재 SpotExchange 메서드 (symbol 관련만)

| 메서드 | 현재 타입 | 용도 | 올바른 타입 |
|--------|----------|------|------------|
| `place_order` | `SpotOrder` | 주문 생성 | ✅ OK (StockAddress 포함) |
| `get_open_orders` | `str \| None` | 미체결 주문 조회 | `str \| Symbol \| None` |
| `get_trade_history` | `str \| None` | 거래 내역 조회 | `str \| Symbol \| None` |
| `get_current_price` | `str` | 현재가 조회 | `str \| Symbol` |
| `get_orderbook` | `str` | 호가창 조회 | `str \| Symbol` |
| `get_candles` | `str` | 캔들 조회 | `str \| Symbol` |
| `get_position_value` | `str` (ticker) | 포지션 가치 | `str \| Symbol` |

### 누락된 메서드 (Portfolio 기능 미노출)

| 메서드 | 타입 | 용도 |
|--------|------|------|
| `get_position` | `str \| Symbol` | 단일 포지션 수량 조회 |
| `get_available_position` | `str \| Symbol` | 사용 가능 포지션 조회 |
| `get_locked_position` | `str \| Symbol` | 잠긴 포지션 조회 |
| `get_locked_balance` | `str` | 잠긴 잔고 조회 |
| `get_currencies` | - | 보유 화폐 목록 |

---

## 2. 개선 계획

### Phase 1: 기존 메서드 타입 개선

#### A. 시장 데이터 조회 메서드 (`str | Symbol` 지원)
**내부 변환**: `symbol.to_slash() if isinstance(symbol, Symbol) else symbol`

```python
def get_current_price(self, symbol: str | Symbol) -> float | None:
    """현재 시장 가격 조회.

    Args:
        symbol: "BTC/USDT" 문자열 또는 Symbol 객체
    """
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    price_data = self._market_data.get_current(symbol_str)
    ...

def get_orderbook(self, symbol: str | Symbol, depth: int = 20):
    """호가창 조회"""
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    return self._market_data_service.generate_orderbook(symbol_str, depth)

def get_candles(self, symbol: str | Symbol, start_time=None, end_time=None, limit=None):
    """캔들 조회"""
    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    return self._market_data.get_candles(symbol=symbol_str, ...)
```

#### B. 주문 조회 메서드 (`str | Symbol | None` 지원)

```python
def get_open_orders(self, symbol: str | Symbol | None = None) -> list[SpotOrder]:
    """미체결 주문 조회"""
    if symbol is None:
        return self._orderbook.get_all_orders()

    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    return self._orderbook.get_orders_by_symbol(symbol_str)

def get_trade_history(self, symbol: str | Symbol | None = None) -> list[SpotTrade]:
    """거래 내역 조회"""
    if symbol is None:
        return self._trade_history

    symbol_str = symbol.to_slash() if isinstance(symbol, Symbol) else symbol
    return [
        trade for trade in self._trade_history
        if trade.order.stock_address.to_symbol().to_slash() == symbol_str
    ]
```

#### C. 포지션 조회 메서드 (`str | Symbol` 지원)
**내부 변환**: `symbol.to_dash() if isinstance(symbol, Symbol) else Symbol(symbol).to_dash()`

```python
def get_position_value(self, symbol: str | Symbol) -> dict[str, float]:
    """포지션 가치 정보"""
    ticker = self._to_ticker(symbol)  # Helper 메서드
    return {
        "book_value": self._position_manager.get_position_book_value(ticker),
        "market_value": self._position_manager.get_position_market_value(ticker),
        "pnl": self._position_manager.get_position_pnl(ticker),
        "pnl_ratio": self._position_manager.get_position_pnl_ratio(ticker)
    }

def _to_ticker(self, symbol: str | Symbol) -> str:
    """Symbol → ticker(dash) 변환 헬퍼"""
    if isinstance(symbol, Symbol):
        return symbol.to_dash()
    else:
        # str이면 Symbol로 변환 후 dash 형식으로
        return Symbol(symbol).to_dash()
```

---

### Phase 2: 누락된 메서드 추가

#### A. 포지션 조회 메서드

```python
def get_position(self, symbol: str | Symbol) -> float:
    """단일 포지션 수량 조회.

    Args:
        symbol: "BTC/USDT" 문자열 또는 Symbol 객체

    Returns:
        float: 보유 수량 (없으면 0.0)
    """
    ticker = self._to_ticker(symbol)
    return self._portfolio.get_positions().get(ticker, 0.0)

def get_available_position(self, symbol: str | Symbol) -> float:
    """사용 가능 포지션 조회 (미잠김).

    Args:
        symbol: "BTC/USDT" 문자열 또는 Symbol 객체

    Returns:
        float: 사용 가능 수량
    """
    ticker = self._to_ticker(symbol)
    return self._portfolio.get_available_position(ticker)

def get_locked_position(self, symbol: str | Symbol) -> float:
    """잠긴 포지션 조회 (미체결 매도 주문용).

    Args:
        symbol: "BTC/USDT" 문자열 또는 Symbol 객체

    Returns:
        float: 잠긴 수량
    """
    ticker = self._to_ticker(symbol)
    return self._portfolio.get_locked_position(ticker)
```

#### B. Currency 조회 메서드

```python
def get_locked_balance(self, currency: str) -> float:
    """잠긴 잔고 조회 (미체결 매수 주문용).

    Args:
        currency: 화폐 심볼 (예: "USDT")

    Returns:
        float: 잠긴 수량
    """
    return self._portfolio.get_locked_balance(currency)

def get_currencies(self) -> list[str]:
    """보유 화폐 목록 조회.

    Returns:
        list[str]: 화폐 심볼 리스트 (예: ["USDT", "BTC"])
    """
    return self._portfolio.get_currencies()
```

---

### Phase 3: 문서화 개선

#### A. get_balance Docstring 명확화

```python
def get_balance(self, currency: str | None = None) -> float | dict[str, float]:
    """Currency 잔고 조회 (사용 가능 잔고).

    NOTE: 이 메서드는 Quote Currency(USDT, USD 등) 전용입니다.
          Base Asset(BTC, ETH 등)는 get_position() 사용하세요.

    Args:
        currency: 화폐 심볼 (None이면 전체 dict 반환)

    Returns:
        - currency 지정: float (사용 가능 잔고)
        - currency=None: dict[str, float] (전체 잔고)

    Examples:
        >>> exchange.get_balance("USDT")  # USDT 잔고
        100000.0
        >>> exchange.get_balance("BTC")   # ❌ 0.0 반환 (BTC는 Position)
        0.0
        >>> exchange.get_position("BTC/USDT")  # ✅ BTC 수량 조회
        0.5
    """
```

---

## 3. 구현 우선순위

### High Priority (Phase 1 + 핵심 Phase 2)
1. ✅ 헬퍼 메서드 추가: `_to_ticker(symbol: str | Symbol) -> str`
2. ✅ `get_position(symbol)` - 가장 많이 사용될 메서드
3. ✅ `get_available_position(symbol)` - 매도 가능 수량 확인 필수
4. ✅ 기존 메서드 타입 변경: `get_current_price`, `get_orderbook`, `get_candles`
5. ✅ 기존 메서드 타입 변경: `get_open_orders`, `get_trade_history`
6. ✅ `get_position_value` 타입 변경

### Medium Priority
7. ⏳ `get_locked_balance(currency)` - 디버깅용
8. ⏳ `get_locked_position(symbol)` - 디버깅용
9. ⏳ `get_currencies()` - 정보 조회용

### Low Priority
10. ⏳ Docstring 개선 (get_balance 등)

---

## 4. 테스트 영향도 분석

### 수정 필요 테스트
- `test_spot_exchange.py` - str 대신 Symbol 객체 사용 테스트 추가
- `test_create_order_worker.py` - Symbol 객체 사용 검증
- `test_cancel_order_worker.py` - Symbol 객체 사용 검증
- `test_place_order_result_consistency.py` - Symbol/str 혼용 테스트

### 새 테스트 추가
- `test_spot_exchange_symbol_api.py` - Symbol vs str 호환성 테스트
- `test_position_api.py` - get_position, get_available_position 테스트

---

## 5. 구현 순서

1. **헬퍼 메서드 추가** (`_to_ticker`)
2. **Phase 1 구현** (기존 메서드 타입 개선)
3. **Phase 2-A 구현** (포지션 메서드 추가)
4. **테스트 작성 및 실행**
5. **Phase 2-B 구현** (Currency 메서드 추가)
6. **Phase 3 문서화**
7. **전체 테스트 통과 확인**

---

## 6. 호환성 고려사항

### Backward Compatibility
- 모든 변경은 `str | Symbol` 형태로 str을 계속 지원
- 기존 코드 영향 없음 (str만 사용하는 코드도 동작)

### 타입 힌트 개선
```python
from __future__ import annotations
from financial_assets.symbol import Symbol
```

### Import 문 추가
```python
# SpotExchange.py 상단
from financial_assets.symbol import Symbol
```
