# Implementation Tasks

## 1. Rename TradeSide to SpotSide
- [x] 1.1 Rename `financial_assets/trade/trade_side.py` → `spot_side.py`
- [x] 1.2 Rename `TradeSide` class to `SpotSide`
- [x] 1.3 Remove LONG and SHORT enum values (keep only BUY and SELL)
- [x] 1.4 Update docstrings to indicate spot trading only
- [x] 1.5 Update `__init__.py` exports

## 2. Rename Trade to SpotTrade
- [x] 2.1 Rename `financial_assets/trade/trade.py` → `spot_trade.py`
- [x] 2.2 Rename `Trade` dataclass to `SpotTrade`
- [x] 2.3 Update type hints to use `SpotSide` instead of `TradeSide`
- [x] 2.4 Update docstrings to emphasize spot trading semantics
- [x] 2.5 Update `__init__.py` exports

## 3. Rename Order to SpotOrder
- [x] 3.1 Rename `financial_assets/order/order.py` → `spot_order.py`
- [x] 3.2 Rename `Order` class to `SpotOrder`
- [x] 3.3 Update type hints to use `SpotSide` and `SpotTrade`
- [x] 3.4 Update docstrings to emphasize spot trading semantics
- [x] 3.5 Update `__init__.py` exports

## 4. Update Tests
- [x] 4.1 Update `tests/test_trade.py`: rename imports and class references
- [x] 4.2 Update `tests/test_order.py`: rename imports and class references
- [x] 4.3 Remove tests for LONG and SHORT sides (only test BUY and SELL)
- [x] 4.4 Verify all tests pass with new names

## 5. Validation
- [x] 5.1 Run full test suite: `pytest packages/financial-assets/tests/`
- [x] 5.2 Verify no references to old names remain: `rg "TradeSide|(?<!Spot)Trade(?!r)|(?<!Spot)Order(?!Book)" packages/financial-assets`
- [x] 5.3 Check documentation consistency
