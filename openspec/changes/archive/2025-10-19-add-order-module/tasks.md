# Tasks: add-order-module

## Implementation Tasks

- [x] **Setup order module structure**
  - Create `packages/financial-assets/financial_assets/order/` directory
  - Create `__init__.py` with public API exports

- [x] **Implement Order class**
  - Define Order class with all required fields
  - Implement `fill_by_asset_amount()` method (returns Trade)
  - Implement `fill_by_value_amount()` method (returns Trade)
  - Implement `remaining_asset()` property/method
  - Implement `remaining_value()` property/method
  - Implement `remaining_rate()` property/method
  - Implement `is_filled()` method
  - Implement `cancel()` method
  - Add `__str__()` and `__repr__()` methods

- [x] **Implement status management**
  - Define order status constants or enum
  - Add status transition logic in fill methods
  - Validate status changes (e.g., cannot fill canceled order)

- [x] **Write comprehensive tests**
  - Test order creation (market, limit, stop orders)
  - Test `fill_by_asset_amount()` - partial fill
  - Test `fill_by_asset_amount()` - full fill
  - Test `fill_by_value_amount()` - partial fill
  - Test `fill_by_value_amount()` - full fill
  - Test remaining amount calculations
  - Test remaining rate calculation
  - Test status transitions (pending → partial → filled)
  - Test cancel operation
  - Test Trade object creation from fill
  - Test edge cases (fill amount exceeds remaining, zero amounts, etc.)

- [x] **Update package exports**
  - Add Order to `packages/financial-assets/financial_assets/__init__.py`
  - Verify imports work correctly

- [x] **Documentation**
  - Add docstrings to all public methods
  - Add usage examples in docstrings
  - Ensure consistency with existing modules (Trade, Pair, Token)

## Validation Tasks

- [x] Run all tests and verify they pass
- [x] Verify Trade objects created by fill methods are valid
- [x] Check that Pair split behavior is consistent
- [x] Validate status transitions are correct
- [x] Ensure no circular dependencies

## Dependencies
- Requires: Token, Pair, StockAddress, Trade modules (already exist)
- Blocks: OrderBook implementation (future work)
