# Spec: Trade Data Structure

## Overview
Trade는 체결 완료된 거래를 표현하는 불변 데이터 구조입니다. 거래 시뮬레이션이나 실제 거래소 API 응답을 표준화된 형식으로 캡슐화합니다.

## ADDED Requirements

### Requirement: Trade 데이터 클래스
Trade MUST be an immutable object that contains all essential information about a completed trade.

#### Scenario: 기본 Trade 객체 생성
```python
from financial_assets.trade import Trade, TradeSide
from financial_assets.token import Token
from financial_assets.pair import Pair
from financial_assets.stock_address import StockAddress

stock_address = StockAddress(
    archetype="crypto",
    exchange="binance",
    tradetype="spot",
    base="btc",
    quote="usd",
    timeframe="1d"
)

pair = Pair(
    asset=Token("BTC", 1.5),
    value=Token("USD", 75000.0)
)

trade = Trade(
    stock_address=stock_address,
    trade_id="trade-123",
    fill_id="fill-456",
    side=TradeSide.BUY,
    pair=pair,
    timestamp=1234567890
)

assert trade.trade_id == "trade-123"
assert trade.fill_id == "fill-456"
assert trade.side == TradeSide.BUY
assert trade.pair.get_asset() == 1.5
assert trade.timestamp == 1234567890
```

#### Scenario: Trade 불변성 보장
```python
# Trade 객체는 생성 후 수정 불가
trade = Trade(
    stock_address=stock_address,
    trade_id="trade-789",
    fill_id="fill-012",
    side=TradeSide.SELL,
    pair=pair,
    timestamp=1234567900
)

# 다음 시도는 에러 발생해야 함
try:
    trade.trade_id = "modified"
    assert False, "Should raise error"
except:
    pass  # 예상된 동작
```

### Requirement: TradeSide Enum
The system MUST provide an enum to clearly distinguish trade directions.

#### Scenario: TradeSide 모든 값 사용 가능
```python
from financial_assets.trade import TradeSide

# 모든 거래 방향 지원
assert TradeSide.BUY
assert TradeSide.SELL
assert TradeSide.LONG
assert TradeSide.SHORT

# enum으로 동등성 비교 가능
side = TradeSide.BUY
assert side == TradeSide.BUY
assert side != TradeSide.SELL
```

### Requirement: 기존 모듈 통합
Trade MUST utilize existing financial-assets modules such as Token, Pair, and StockAddress.

#### Scenario: Pair를 통한 거래 정보 접근
```python
# Pair 객체를 통해 거래 수량, 가격, 평균 접근
trade = Trade(
    stock_address=stock_address,
    trade_id="trade-abc",
    fill_id="fill-def",
    side=TradeSide.BUY,
    pair=Pair(Token("BTC", 2.0), Token("USD", 100000.0)),
    timestamp=1234567890
)

# Pair의 기능 활용
assert trade.pair.get_asset() == 2.0
assert trade.pair.get_value() == 100000.0
assert trade.pair.mean_value() == 50000.0  # 평균 단가
```

#### Scenario: StockAddress를 통한 거래 특정
```python
# StockAddress로 거래 컨텍스트 식별
trade = Trade(
    stock_address=StockAddress(
        archetype="crypto",
        exchange="upbit",
        tradetype="spot",
        base="eth",
        quote="krw",
        timeframe="1h"
    ),
    trade_id="trade-eth",
    fill_id="fill-eth",
    side=TradeSide.LONG,
    pair=Pair(Token("ETH", 10.0), Token("KRW", 30000000.0)),
    timestamp=1234567890
)

assert trade.stock_address.exchange == "upbit"
assert trade.stock_address.base == "eth"
assert trade.stock_address.quote == "krw"
```

### Requirement: 문자열 표현
Trade MUST provide a readable string representation.

#### Scenario: 읽기 쉬운 문자열 출력
```python
trade = Trade(
    stock_address=stock_address,
    trade_id="trade-str",
    fill_id="fill-str",
    side=TradeSide.SELL,
    pair=Pair(Token("BTC", 0.5), Token("USD", 25000.0)),
    timestamp=1234567890
)

# __str__ 또는 __repr__로 주요 정보 확인 가능
trade_str = str(trade)
assert "trade-str" in trade_str
assert "SELL" in trade_str or "sell" in trade_str.lower()

# repr은 재생성 가능한 형식 (선택적)
trade_repr = repr(trade)
assert "Trade" in trade_repr
```

## MODIFIED Requirements
None

## REMOVED Requirements
None

## Cross-References
- Related to: Token module (financial_assets/token)
- Related to: Pair module (financial_assets/pair)
- Related to: StockAddress module (financial_assets/stock_address)
