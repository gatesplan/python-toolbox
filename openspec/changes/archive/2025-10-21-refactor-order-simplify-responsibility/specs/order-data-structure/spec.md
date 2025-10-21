# order-data-structure Spec Delta

## REMOVED Requirements

### Requirement: SpotTrade 팩토리 기능
**Reason**: SpotOrder가 SpotTrade 생성을 담당하는 것은 책임 범위를 벗어납니다.
**Migration**: 외부 거래 처리 시스템에서 fill 결과를 활용하여 SpotTrade를 생성하세요.

## ADDED Requirements

### Requirement: 상태 변경 - 불변 복제
SpotOrder MUST provide state transition methods that return new instances with updated status, preserving immutability.

#### Scenario: to_pending_state()로 pending 상태 복제
```python
order = SpotOrder(
    order_id="order-1",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)
order.status = "partial"  # 임시로 상태 변경

# pending 상태로 복제
pending_order = order.to_pending_state()

assert pending_order.status == "pending"
assert pending_order.order_id == order.order_id
assert pending_order.amount == order.amount
# 원본은 변경되지 않음
assert order.status == "partial"
```

#### Scenario: to_partial_state()로 partial 상태 복제
```python
order = SpotOrder(
    order_id="order-2",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

partial_order = order.to_partial_state()

assert partial_order.status == "partial"
assert order.status == "pending"  # 원본 불변
```

#### Scenario: to_filled_state()로 filled 상태 복제
```python
order = SpotOrder(
    order_id="order-3",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

filled_order = order.to_filled_state()

assert filled_order.status == "filled"
assert order.status == "pending"  # 원본 불변
```

#### Scenario: to_canceled_state()로 canceled 상태 복제
```python
order = SpotOrder(
    order_id="order-4",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

canceled_order = order.to_canceled_state()

assert canceled_order.status == "canceled"
assert order.status == "pending"  # 원본 불변
```

## MODIFIED Requirements

### Requirement: 부분 체결 처리 - Asset 기준
SpotOrder MUST support updating filled_amount based on asset amount and return a new SpotOrder instance with updated state, without creating SpotTrade objects.

**Note**: 기존에는 SpotTrade 객체를 반환했으나, 이제는 업데이트된 SpotOrder만 반환합니다. SpotTrade 생성은 외부에서 처리하세요.

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

# 0.3 BTC 체결
updated_order = order.fill_by_asset_amount(0.3)

# 업데이트된 Order 검증
assert updated_order.order_id == "order-partial"
assert updated_order.filled_amount == 0.3
assert updated_order.status == "partial"
assert updated_order.remaining_asset() == 0.7

# 원본은 변경되지 않음
assert order.filled_amount == 0.0
assert order.status == "pending"
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
updated_order = order.fill_by_asset_amount(1.0)

assert updated_order.filled_amount == 1.0
assert updated_order.status == "filled"
assert updated_order.remaining_asset() == 0.0
assert updated_order.is_filled() == True

# 원본 불변
assert order.filled_amount == 0.0
```

#### Scenario: 여러 번 부분 체결 (체이닝)
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
order1 = order.fill_by_asset_amount(0.5)
assert order1.filled_amount == 0.5
assert order1.status == "partial"

# 두 번째 체결: 0.8 BTC (누적)
order2 = order1.fill_by_asset_amount(0.8)
assert order2.filled_amount == 1.3
assert order2.status == "partial"

# 세 번째 체결: 0.7 BTC (전체 체결)
order3 = order2.fill_by_asset_amount(0.7)
assert order3.filled_amount == 2.0
assert order3.status == "filled"
assert order3.is_filled() == True

# 원본은 여전히 불변
assert order.filled_amount == 0.0
```

### Requirement: 부분 체결 처리 - Value 기준
SpotOrder MUST support updating filled_amount based on value amount (quote currency) and return a new SpotOrder instance.

**Note**: 기존에는 SpotTrade 객체를 반환했으나, 이제는 업데이트된 SpotOrder만 반환합니다.

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

# 15000 USDT 어치 체결 (0.3 BTC에 해당)
updated_order = order.fill_by_value_amount(15000.0)

# 15000 USDT = 0.3 BTC
assert updated_order.filled_amount == 0.3
assert updated_order.status == "partial"

# 원본 불변
assert order.filled_amount == 0.0
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
updated_order = order.fill_by_value_amount(50000.0)

assert updated_order.filled_amount == 1.0
assert updated_order.is_filled() == True
```

### Requirement: 주문 상태 관리
SpotOrder MUST automatically determine status based on filled_amount when using fill methods.

**Note**: 기존 cancel() 메서드는 제거되고 to_canceled_state()로 대체됩니다.

#### Scenario: 상태 자동 판단 - pending → partial → filled
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

# 부분 체결 → 자동으로 partial 상태
order1 = order.fill_by_asset_amount(0.4)
assert order1.status == "partial"
assert order1.is_filled() == False

# 완전 체결 → 자동으로 filled 상태
order2 = order1.fill_by_asset_amount(0.6)
assert order2.status == "filled"
assert order2.is_filled() == True
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
order1 = order.fill_by_asset_amount(0.3)
assert order1.status == "partial"

canceled_order = order1.to_canceled_state()
assert canceled_order.status == "canceled"

# 원본들은 불변
assert order.status == "pending"
assert order1.status == "partial"
```

### Requirement: 미체결 수량 조회
SpotOrder MUST provide read-only methods to query amounts without any side effects.

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

order1 = order.fill_by_asset_amount(0.7)
assert order1.remaining_asset() == 1.3

order2 = order1.fill_by_asset_amount(1.3)
assert order2.remaining_asset() == 0.0
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

assert order.remaining_value() == 50000.0

order1 = order.fill_by_asset_amount(0.3)
assert order1.remaining_value() == 35000.0
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

assert order.remaining_rate() == 1.0

order1 = order.fill_by_asset_amount(0.3)
assert order1.remaining_rate() == 0.7

order2 = order1.fill_by_asset_amount(0.7)
assert order2.remaining_rate() == 0.0
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

try:
    order.fill_by_asset_amount(1.5)
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "exceed" in str(e).lower()
```

#### Scenario: 초과 체결 시도 - value 기준
```python
order = SpotOrder(
    order_id="order-exceed-value",
    stock_address=stock_address,
    side=SpotSide.BUY,
    order_type="limit",
    price=50000.0,
    amount=1.0,
    timestamp=1234567890
)

try:
    order.fill_by_value_amount(60000.0)
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "exceed" in str(e).lower()
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
    order.fill_by_asset_amount(-0.1)
    assert False, "Should raise ValueError"
except ValueError as e:
    assert "negative" in str(e).lower()
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
SpotOrder MUST be a data structure representing a pending spot trade order, providing immutable update methods for state management and containing all information necessary for stateless trade processing.

**Note**: 이전에는 "가변 객체"였지만, 이제는 불변 복제 패턴을 통해 업데이트를 제공합니다. 원본 인스턴스는 항상 보존되며, 변경이 필요한 경우 새 인스턴스를 반환합니다. `fee_rate` 필드가 추가되어 거래 처리에 필요한 모든 정보를 Order가 포함하게 됩니다.

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
    fee_rate=0.001  # 0.1% 수수료
)

assert order.order_id == "order-123"
assert order.side == SpotSide.BUY
assert order.order_type == "limit"
assert order.price == 50000.0
assert order.amount == 1.0
assert order.filled_amount == 0.0
assert order.status == "pending"
assert order.fee_rate == 0.001
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

