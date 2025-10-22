# Proposal: remove-round-to-min-amount

## Why
`SpotOrder.round_to_min_amount()` 메서드는 데이터 클래스인 Order의 책임 범위를 벗어납니다. 이 메서드는 외부에서 전달받은 값을 조작하는 유틸리티 함수로, Order 자신의 상태와 무관한 동작을 수행합니다.

**Order의 적절한 책임:**
- 자신의 상태 조회: `remaining_asset()`, `is_remaining_below_min()`
- 자신의 상태 변경: `fill_by_asset_amount()`, `to_canceled_state()`

**부적절한 책임:**
- 외부 값 조작: `round_to_min_amount(external_amount)` ❌

Order 객체를 생성하기 전에 값은 이미 정합되어야 하며, 이러한 값 조정 로직은 Order 외부(예: 시뮬레이션 워커, 팩토리 함수)에서 수행하는 것이 올바른 설계입니다.

## What Changes
- `SpotOrder.round_to_min_amount()` 메서드 제거
- 관련 테스트 2개 제거
- OpenSpec에서 해당 시나리오 제거

## Impact
- **Breaking Changes**: 있음 - `round_to_min_amount()` 메서드가 제거됨
- **Affected specs**: `order-data-structure`
- **Affected code**:
  - `packages/financial-assets/financial_assets/order/spot_order.py`
  - `packages/financial-assets/tests/test_order.py`
- **Migration Required**: 이 메서드를 사용하는 코드는 직접 값을 조정해야 함

## Migration Guide
```python
# Before (잘못된 설계)
order = SpotOrder(amount=1.0, min_trade_amount=0.01)
valid_amount = order.round_to_min_amount(0.437)

# After (올바른 설계)
import math

min_trade_amount = 0.01
amount = 0.437
if min_trade_amount:
    valid_amount = math.floor(amount / min_trade_amount) * min_trade_amount
else:
    valid_amount = amount

order = SpotOrder(amount=valid_amount, min_trade_amount=min_trade_amount)
```

## Benefits
- 데이터 클래스의 책임을 명확히 분리
- Order가 자신의 상태만 관리하도록 단순화
- 값 정합 로직이 Order 생성 전에 명시적으로 수행됨
