# Clarify Spot Trading Scope

## Why

The current `Trade` and `Order` modules claim to support both spot and futures trading through the `TradeSide` enum (BUY, SELL, LONG, SHORT), but the implementation only handles spot trading semantics. This creates confusion and false expectations:

- All tests use `tradetype="spot"` in `StockAddress`
- LONG/SHORT sides exist but have no futures-specific logic (leverage, margin, position management)
- The fill logic assumes immediate asset exchange (spot) rather than position contracts (futures)

This ambiguity will cause issues when futures trading is eventually implemented, as there's no clear separation between the two fundamentally different trading paradigms.

## What Changes

**BREAKING**: Rename core types to explicitly indicate spot-only scope:

- Rename `TradeSide` enum → `SpotSide` with only BUY and SELL values
- Rename `Trade` dataclass → `SpotTrade`
- Rename `Order` class → `SpotOrder`
- Update all imports, tests, and documentation to reflect spot-only semantics
- Remove LONG and SHORT from the spot trading domain (reserve for future `FuturesSide`)

This change establishes a clear foundation for later introducing `FuturesTrade`, `FuturesOrder`, and `FuturesSide` without conflicting with spot trading infrastructure.

## Impact

- **Affected specs**: `trade-data-structure`, `order-data-structure`
- **Affected code**:
  - `financial_assets/trade/trade.py` → `spot_trade.py`
  - `financial_assets/trade/trade_side.py` → `spot_side.py`
  - `financial_assets/order/order.py` → `spot_order.py`
  - All test files (`test_trade.py`, `test_order.py`)
  - Public API exports in `__init__.py` files

- **Migration**: Users must update imports from `Trade`/`TradeSide`/`Order` to `SpotTrade`/`SpotSide`/`SpotOrder`
