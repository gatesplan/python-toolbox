# Tasks: remove-round-to-min-amount

## Implementation Tasks

### 1. Remove round_to_min_amount method
- [x] Remove `round_to_min_amount()` method from `SpotOrder` class
- [x] Verify no internal usage of the method within SpotOrder
- [x] Remove unused `import math` statement
- **Validation**: Method no longer exists in SpotOrder class

### 2. Remove related tests
- [x] Remove `test_round_to_min_amount` test
- [x] Remove `test_round_to_min_amount_when_none` test
- **Validation**: Tests removed from test_order.py

### 3. Verify all tests pass
- [x] Run pytest for order module
- [x] Ensure no other tests depend on round_to_min_amount
- **Validation**: All 38 tests pass (down from 40)

### 4. Update documentation
- [x] Class docstring unchanged (no references to round_to_min_amount)
- [x] Verified no references to round_to_min_amount in comments
- **Validation**: Documentation is accurate
