# Tasks: add-min-trade-amount

## Implementation Tasks

### 1. Update SpotOrder class
- [x] Add `min_trade_amount: Optional[float] = None` field to `__init__`
- [x] Update `_clone` method to include `min_trade_amount`
- [x] Update `__repr__` to include `min_trade_amount`
- **Validation**: SpotOrder can be created with min_trade_amount parameter

### 2. Add validation logic
- [x] Update `_validate_fill` method to check against min_trade_amount
- [x] Allow fills that result in complete order fulfillment (even if below min)
- [x] Raise ValueError if partial fill is below min_trade_amount
- **Validation**: Validation logic correctly enforces minimum trade amount

### 3. Add helper methods
- [x] Add `is_remaining_below_min() -> bool` method
- [x] Add `round_to_min_amount(amount: float) -> float` method for rounding to min_trade_amount multiples
- **Validation**: Helper methods work correctly

### 4. Update tests
- [x] Add test for min_trade_amount in order creation
- [x] Add test for validation with min_trade_amount
- [x] Add test for edge case: final fill below min (should allow)
- [x] Add test for partial fill below min (should reject)
- [x] Add test for round_to_min_amount
- **Validation**: All tests pass (40/40 tests passing)

### 5. Update documentation
- [x] Update docstrings for SpotOrder class
- [x] Add usage examples in comments
- **Validation**: Documentation is clear and accurate
