# order-data-structure Delta

## MODIFIED Requirements

### Requirement: SpotOrder 데이터 클래스
SpotOrder MUST be a data structure representing a pending spot trade order, providing immutable update methods for state management and containing all information necessary for stateless trade processing, including minimum trade amount constraints.

**Note**: `min_trade_amount` 필드가 추가되어 실제 거래소의 최소 거래 단위 제약을 시뮬레이션에 반영할 수 있습니다.

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

order = SpotOrder(
    order_id="order-123",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    fee_rate=0.001
)

assert order.order_id == "order-123"
assert order.side == SpotSide.BUY
assert order.order_type == "limit"
assert order.price == 50000.0
assert order.amount == 1.0
assert order.filled_amount == 0.0
assert order.status == "pending"
assert order.fee_rate == 0.001
assert order.min_trade_amount is None  # 기본값
```

#### Scenario: min_trade_amount 포함 주문 생성
```python
order = SpotOrder(
    order_id="order-with-min",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    min_trade_amount=0.001  # 최소 0.001 BTC
)

assert order.min_trade_amount == 0.001
```

#### Scenario: Market order 생성 (price=None)
```python
order = SpotOrder(
    order_id="market-order-1",
    stock_address=stock_address,
    side=SpotSide.SELL,
    order_type="market",
    price=None,
    amount=0.5,
    timestamp=1234567900
)

assert order.price is None
assert order.order_type == "market"
```

#### Scenario: Stop order 생성 (stop_price 포함)
```python
order = SpotOrder(
    order_id="stop-order-1",
    stock_address=stock_address,
    side=SpotSide.SELL,
    order_type="stop",
    price=45000.0,
    amount=0.3,
    timestamp=1234567910,
    stop_price=48000.0
)

assert order.stop_price == 48000.0
assert order.order_type == "stop"
```

#### Scenario: fee_rate 포함 주문 생성
```python
# 0.1% 수수료 적용 주문
order = SpotOrder(
    order_id="order-with-fee",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    fee_rate=0.001  # 0.1%
)

assert order.fee_rate == 0.001

# fee_rate 기본값 (수수료 없음)
order_no_fee = SpotOrder(
    order_id="order-no-fee",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

assert order_no_fee.fee_rate == 0.0

# 외부에서 fee_rate를 사용해 SpotTrade의 fee 계산
from financial_assets.token import Token

fill_amount = 0.3
fill_price = 50100.0
fee_amount = fill_amount * fill_price * order.fee_rate  # 15.03 USDT

trade_fee = Token(
    symbol=order.stock_address.quote,  # BUY는 quote 통화로 수수료 납부
    amount=fee_amount
)

assert trade_fee.amount == 15.03
```

## ADDED Requirements

### Requirement: 최소 거래 단위 제약
SpotOrder MUST enforce minimum trade amount constraints when min_trade_amount is set, preventing unrealistic fractional fills in simulations.

#### Scenario: 최소 단위 이상 부분 체결 허용
```python
order = SpotOrder(
    order_id="order-min-1",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    min_trade_amount=0.001  # 최소 0.001 BTC
)

# 0.5 BTC 체결 (최소 단위 이상)
updated_order = order.fill_by_asset_amount(0.5)
assert updated_order.filled_amount == 0.5
assert updated_order.status == "partial"
```

#### Scenario: 최소 단위 미만 부분 체결 거부
```python
order = SpotOrder(
    order_id="order-min-2",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    min_trade_amount=0.001
)

# 0.0005 BTC 체결 시도 (최소 단위 미만)
try:
    order.fill_by_asset_amount(0.0005)
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "minimum trade amount" in str(e).lower()
```

#### Scenario: 최종 체결은 최소 단위 미만 허용
```python
order = SpotOrder(
    order_id="order-min-3",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    min_trade_amount=0.001
)

# 0.9995 BTC 체결 후 잔여 0.0005 BTC
order1 = order.fill_by_asset_amount(0.9995)
assert order1.filled_amount == 0.9995
assert order1.remaining_asset() == 0.0005

# 마지막 0.0005 BTC 체결 (최소 단위 미만이지만 전체 체결이므로 허용)
order2 = order1.fill_by_asset_amount(0.0005)
assert order2.filled_amount == 1.0
assert order2.status == "filled"
```

#### Scenario: min_trade_amount가 None일 때는 검증 안 함
```python
order = SpotOrder(
    order_id="order-no-min",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
    # min_trade_amount 미지정 (None)
)

# 아주 작은 수량도 체결 가능
updated_order = order.fill_by_asset_amount(0.00001)
assert updated_order.filled_amount == 0.00001
```

### Requirement: 최소 단위 헬퍼 메서드
SpotOrder MUST provide helper methods to check and round amounts based on min_trade_amount.

#### Scenario: is_remaining_below_min() 확인
```python
order = SpotOrder(
    order_id="order-check",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    min_trade_amount=0.01
)

# 초기에는 충분한 잔여 수량
assert order.is_remaining_below_min() == False

# 0.995 체결 후 잔여 0.005 (최소 단위 0.01 미만)
order1 = order.fill_by_asset_amount(0.995)
assert order1.is_remaining_below_min() == True

# min_trade_amount가 None이면 항상 False
order_no_min = SpotOrder(
    order_id="order-no-min",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=0.0001,
    timestamp=1234567890
)
assert order_no_min.is_remaining_below_min() == False
```

#### Scenario: round_to_min_amount() 반올림
```python
order = SpotOrder(
    order_id="order-round",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890,
    min_trade_amount=0.01
)

# 0.01 단위로 내림
assert order.round_to_min_amount(0.0567) == 0.05
assert order.round_to_min_amount(0.0123) == 0.01
assert order.round_to_min_amount(0.0099) == 0.0

# min_trade_amount가 None이면 원본 반환
order_no_min = SpotOrder(
    order_id="order-no-min",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)
assert order_no_min.round_to_min_amount(0.0567) == 0.0567
```
