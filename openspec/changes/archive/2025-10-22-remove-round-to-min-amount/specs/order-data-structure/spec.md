# order-data-structure Delta

## MODIFIED Requirements

### Requirement: 최소 단위 헬퍼 메서드
SpotOrder MUST provide helper methods to check remaining amount against min_trade_amount.

**Note**: `round_to_min_amount()` 메서드가 제거되었습니다. 외부 값 조작은 Order의 책임 범위를 벗어나므로, Order 생성 전에 외부에서 수행해야 합니다.

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
