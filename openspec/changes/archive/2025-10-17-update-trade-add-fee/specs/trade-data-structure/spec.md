# trade-data-structure Specification Delta

## MODIFIED Requirements

### Requirement: Trade 데이터 클래스
Trade MUST be an immutable object that contains all essential information about a completed trade, including optional fee information.

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

#### Scenario: Fee 정보 포함
```python
# 거래 수수료를 Token으로 표현
fee = Token("USD", 0.5)

trade = Trade(
    stock_address=stock_address,
    trade_id="trade-with-fee",
    fill_id="fill-with-fee",
    side=TradeSide.BUY,
    pair=Pair(Token("BTC", 1.0), Token("USD", 50000.0)),
    timestamp=1234567890,
    fee=fee
)

assert trade.fee is not None
assert trade.fee.symbol == "USD"
assert trade.fee.amount == 0.5
```

#### Scenario: Fee 없이 거래 생성 (하위 호환성)
```python
# fee를 명시하지 않으면 None
trade = Trade(
    stock_address=stock_address,
    trade_id="trade-no-fee",
    fill_id="fill-no-fee",
    side=TradeSide.SELL,
    pair=Pair(Token("BTC", 0.5), Token("USD", 25000.0)),
    timestamp=1234567890
    # fee 파라미터 생략
)

assert trade.fee is None
```

#### Scenario: 다양한 통화의 Fee
```python
# Fee는 거래 통화와 다를 수 있음
trade_krw = Trade(
    stock_address=StockAddress(
        archetype="crypto",
        exchange="upbit",
        tradetype="spot",
        base="btc",
        quote="krw",
        timeframe="1d"
    ),
    trade_id="trade-krw-fee",
    fill_id="fill-krw-fee",
    side=TradeSide.BUY,
    pair=Pair(Token("BTC", 0.1), Token("KRW", 7000000.0)),
    timestamp=1234567890,
    fee=Token("KRW", 7000.0)  # KRW로 표시된 수수료
)

assert trade_krw.fee.symbol == "KRW"
assert trade_krw.fee.amount == 7000.0
```
