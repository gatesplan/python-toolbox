# order-data-structure Specification

## Purpose
TBD - created by archiving change add-order-module. Update Purpose after archive.
## Requirements
### Requirement: 부분 체결 처리 - Asset 기준
SpotOrder MUST support partial fills based on asset amount and generate SpotTrade objects.

#### Scenario: fill_by_asset_amount로 부분 체결
```python
order = SpotOrder(
    order_id="order-partial",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 0.3 BTC 체결 (가격 50100.0에)
trade = order.fill_by_asset_amount(
    amount=0.3,
    price=50100.0,
    timestamp=1234567900
)

# SpotTrade 객체 검증
assert trade.trade_id == "order-partial"
assert trade.side == SpotSide.BUY
assert trade.pair.get_asset() == 0.3
assert trade.pair.get_value() == 0.3 * 50100.0
assert trade.timestamp == 1234567900

# SpotOrder 상태 업데이트 확인
assert order.filled_amount == 0.3
assert order.status == "partial"
assert order.remaining_asset() == 0.7
```

#### Scenario: fill_by_asset_amount로 전체 체결
```python
order = SpotOrder(
    order_id="order-full",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 전체 수량 체결
trade = order.fill_by_asset_amount(
    amount=1.0,
    price=50050.0,
    timestamp=1234567900
)

assert trade.pair.get_asset() == 1.0
assert order.filled_amount == 1.0
assert order.status == "filled"
assert order.remaining_asset() == 0.0
assert order.is_filled() == True
```

#### Scenario: 여러 번 부분 체결
```python
order = SpotOrder(
    order_id="order-multi",
    stock_address=stock_address,
    side=SpotSide.SELL,
    order_type="limit",
    price=51000.0,
    amount=2.0,
    timestamp=1234567890
)

# 첫 번째 체결: 0.5 BTC
trade1 = order.fill_by_asset_amount(0.5, 51000.0, 1234567900)
assert order.filled_amount == 0.5
assert order.status == "partial"

# 두 번째 체결: 0.8 BTC
trade2 = order.fill_by_asset_amount(0.8, 51000.0, 1234567910)
assert order.filled_amount == 1.3
assert order.status == "partial"

# 세 번째 체결: 0.7 BTC (전체 체결)
trade3 = order.fill_by_asset_amount(0.7, 51000.0, 1234567920)
assert order.filled_amount == 2.0
assert order.status == "filled"
assert order.is_filled() == True
```

### Requirement: 부분 체결 처리 - Value 기준
SpotOrder MUST support partial fills based on value amount (quote currency).

#### Scenario: fill_by_value_amount로 부분 체결
```python
order = SpotOrder(
    order_id="order-value",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,  # 1 BTC = 50000 USDT
    timestamp=1234567890
)

# 15000 USDT 어치 체결 (가격 50000.0에)
trade = order.fill_by_value_amount(
    amount=15000.0,
    price=50000.0,
    timestamp=1234567900
)

# 15000 USDT = 0.3 BTC
assert trade.pair.get_asset() == 0.3
assert trade.pair.get_value() == 15000.0
assert order.filled_amount == 0.3
assert order.status == "partial"
```

#### Scenario: fill_by_value_amount로 전체 체결
```python
order = SpotOrder(
    order_id="order-value-full",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 전체 금액 체결
trade = order.fill_by_value_amount(
    amount=50000.0,
    price=50000.0,
    timestamp=1234567900
)

assert trade.pair.get_asset() == 1.0
assert order.is_filled() == True
```

### Requirement: 미체결 수량 조회
SpotOrder MUST provide methods to query remaining unfilled amounts.

#### Scenario: remaining_asset() 계산
```python
order = SpotOrder(
    order_id="order-remain",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=2.0,
    timestamp=1234567890
)

assert order.remaining_asset() == 2.0

order.fill_by_asset_amount(0.7, 50000.0, 1234567900)
assert order.remaining_asset() == 1.3

order.fill_by_asset_amount(1.3, 50000.0, 1234567910)
assert order.remaining_asset() == 0.0
```

#### Scenario: remaining_value() 계산
```python
order = SpotOrder(
    order_id="order-remain-value",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 초기 remaining_value = 1.0 * 50000.0 = 50000.0
assert order.remaining_value() == 50000.0

# 0.3 BTC 체결 후
order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
# remaining = 0.7 * 50000.0 = 35000.0
assert order.remaining_value() == 35000.0
```

#### Scenario: remaining_rate() 계산
```python
order = SpotOrder(
    order_id="order-rate",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 초기 상태: 100% 미체결
assert order.remaining_rate() == 1.0

# 30% 체결
order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
assert order.remaining_rate() == 0.7

# 완전 체결
order.fill_by_asset_amount(0.7, 50000.0, 1234567910)
assert order.remaining_rate() == 0.0
```

### Requirement: 주문 상태 관리
SpotOrder MUST track and update its status based on fill operations.

#### Scenario: 상태 전이 - pending → partial → filled
```python
order = SpotOrder(
    order_id="order-status",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 초기 상태
assert order.status == "pending"
assert order.is_filled() == False

# 부분 체결
order.fill_by_asset_amount(0.4, 50000.0, 1234567900)
assert order.status == "partial"
assert order.is_filled() == False

# 완전 체결
order.fill_by_asset_amount(0.6, 50000.0, 1234567910)
assert order.status == "filled"
assert order.is_filled() == True
```

#### Scenario: 주문 취소
```python
order = SpotOrder(
    order_id="order-cancel",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 부분 체결 후 취소
order.fill_by_asset_amount(0.3, 50000.0, 1234567900)
assert order.status == "partial"

order.cancel()
assert order.status == "canceled"

# 취소된 주문은 더 이상 체결 불가
try:
    order.fill_by_asset_amount(0.1, 50000.0, 1234567920)
    assert False, "Should raise error"
except ValueError:
    pass  # 예상된 동작
```

### Requirement: 에러 처리
SpotOrder MUST validate fill amounts and raise appropriate errors for invalid operations.

#### Scenario: 초과 체결 시도 - asset 기준
```python
order = SpotOrder(
    order_id="order-exceed",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

# 주문 수량을 초과하는 체결 시도
try:
    order.fill_by_asset_amount(1.5, 50000.0, 1234567900)
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "exceed" in str(e).lower() or "remaining" in str(e).lower()
```

#### Scenario: 초과 체결 시도 - value 기준
```python
order = SpotOrder(
    order_id="order-exceed-value",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,  # 총 50000 USDT
    timestamp=1234567890
)

# 주문 금액을 초과하는 체결 시도
try:
    order.fill_by_value_amount(60000.0, 50000.0, 1234567900)
    assert False, "Should raise ValueError"
except ValueError:
    pass
```

#### Scenario: 음수 체결 시도
```python
order = SpotOrder(
    order_id="order-negative",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

try:
    order.fill_by_asset_amount(-0.1, 50000.0, 1234567900)
    assert False, "Should raise ValueError"
except ValueError:
    pass
```

### Requirement: 문자열 표현
SpotOrder MUST provide readable string representations.

#### Scenario: 읽기 쉬운 문자열 출력
```python
order = SpotOrder(
    order_id="order-str",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

order_str = str(order)
assert "order-str" in order_str
assert "BUY" in order_str or "buy" in order_str.lower()
assert "50000" in order_str or "50000.0" in order_str

order_repr = repr(order)
assert "SpotOrder" in order_repr
```

### Requirement: SpotOrder 데이터 클래스
SpotOrder MUST be a mutable object that tracks the state of a pending spot trade order and supports partial/full fills.

**Note**: This requirement was previously named "Order 데이터 클래스" and now explicitly scopes to spot trading only. Futures orders will use a separate `FuturesOrder` class with leverage and position management.

#### Scenario: 기본 SpotOrder 객체 생성
```python
from financial_assets.order import SpotOrder
from financial_assets.trade import SpotSide
from financial_assets.stock_address import StockAddress

stock_address = StockAddress(
    archetype="crypto",
    exchange="binance",
    tradetype="spot",
    base="btc",
    quote="usdt",
    timeframe="1d"
)

# Limit order 생성
order = SpotOrder(
    order_id="order-123",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

assert order.order_id == "order-123"
assert order.side == SpotSide.BUY
assert order.order_type == "limit"
assert order.price == 50000.0
assert order.amount == 1.0
assert order.filled_amount == 0.0
assert order.status == "pending"
```

#### Scenario: Market order 생성 (price=None)
```python
# 시장가 주문은 price가 None
order = SpotOrder(
    order_id="market-order-1",
    stock_address=stock_address,
    side=SpotSide.SELL,
    order_type="market",
    price=None,  # 시장가는 가격 지정 없음
    amount=0.5,
    timestamp=1234567900
)

assert order.price is None
assert order.order_type == "market"
```

#### Scenario: Stop order 생성 (stop_price 포함)
```python
# Stop order는 stop_price 지정
order = SpotOrder(
    order_id="stop-order-1",
    stock_address=stock_address,
    side=SpotSide.SELL,
    order_type="stop",
    price=45000.0,  # 손절 실행 시 지정가
    amount=0.3,
    timestamp=1234567910,
    stop_price=48000.0  # 이 가격 도달 시 주문 활성화
)

assert order.stop_price == 48000.0
assert order.order_type == "stop"
```

### Requirement: SpotTrade 팩토리 기능
SpotOrder MUST generate valid SpotTrade objects when filled, utilizing existing Token, Pair, and StockAddress modules.

#### Scenario: fill 메서드가 생성한 SpotTrade 객체 검증
```python
from financial_assets.token import Token
from financial_assets.pair import Pair

order = SpotOrder(
    order_id="order-factory",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

trade = order.fill_by_asset_amount(0.5, 50100.0, 1234567900)

# SpotTrade가 올바르게 생성되었는지 검증
assert isinstance(trade, SpotTrade)
assert trade.stock_address == stock_address
assert trade.trade_id == "order-factory"
assert trade.side == SpotSide.BUY
assert trade.timestamp == 1234567900

# Pair 검증
assert isinstance(trade.pair, Pair)
assert trade.pair.get_asset() == 0.5
assert trade.pair.get_value() == 0.5 * 50100.0
assert trade.pair.get_asset_token().symbol == stock_address.base
assert trade.pair.get_value_token().symbol == stock_address.quote
```

#### Scenario: SELL order의 SpotTrade 생성
```python
order = SpotOrder(
    order_id="sell-order",
    stock_address=stock_address,
    side=SpotSide.SELL,
    order_type="limit",
    price=51000.0,
    amount=2.0,
    timestamp=1234567890
)

trade = order.fill_by_asset_amount(1.0, 51000.0, 1234567900)

assert trade.side == SpotSide.SELL
assert trade.pair.get_asset() == 1.0
assert trade.pair.get_value() == 51000.0
```

