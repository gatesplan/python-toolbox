# Implementation Tasks

## 1. Create Module Structure
- [x] 1.1 Create `financial_assets/ledger/` directory
- [x] 1.2 Create `financial_assets/ledger/__init__.py` with exports
- [x] 1.3 Update package structure documentation if needed

## 2. Implement SpotLedgerEntry
- [x] 2.1 Create `financial_assets/ledger/spot_ledger_entry.py`
- [x] 2.2 Define immutable `SpotLedgerEntry` dataclass with fields:
  - timestamp (int) - 거래 시각
  - trade (SpotTrade reference)
  - asset_change (float)
  - value_change (float)
  - cumulative_asset (float)
  - cumulative_value (float)
  - average_price (float)
  - realized_pnl (Optional[float])
- [x] 2.3 Add docstrings and examples
- [x] 2.4 Implement `__str__` and `__repr__` methods

## 3. Implement SpotLedger
- [x] 3.1 Create `financial_assets/ledger/spot_ledger.py`
- [x] 3.2 Define `SpotLedger` class with internal state:
  - _ticker (str)
  - _entries (list[SpotLedgerEntry])
  - _cumulative_asset (float)
  - _cumulative_value (float)
  - _average_price (Optional[float])
- [x] 3.3 Implement `__init__(ticker: str)` method
- [x] 3.4 Implement `add_trade(trade: SpotTrade) -> SpotLedgerEntry` method:
  - BUY: 평균가 가중 계산
  - SELL: 실현 손익 계산
  - 포지션 청산 시 평균가 리셋
- [x] 3.5 Implement `to_dataframe() -> pd.DataFrame` method
- [x] 3.6 Add docstrings and examples
- [x] 3.7 Implement `__str__` and `__repr__` methods

## 4. Write Tests
- [x] 4.1 Create `tests/test_spot_ledger.py`
- [x] 4.2 Test `SpotLedgerEntry` creation and immutability
- [x] 4.3 Test `SpotLedgerEntry` timestamp field
- [x] 4.4 Test `SpotLedger` initialization
- [x] 4.5 Test adding BUY trades (position building)
- [x] 4.6 Test adding SELL trades (position reduction + PnL)
- [x] 4.7 Test average price calculation across multiple buys
- [x] 4.8 Test realized PnL calculation
- [x] 4.9 Test `to_dataframe()` with empty ledger
- [x] 4.10 Test `to_dataframe()` with multiple entries
- [x] 4.11 Test DataFrame column names and data types
- [x] 4.12 Test edge cases (position closure, zero positions)
- [x] 4.13 Test string representations

## 5. Validation
- [x] 5.1 Run test suite: `pytest packages/financial-assets/tests/test_spot_ledger.py -v`
- [x] 5.2 Check test coverage for ledger module
- [x] 5.3 Verify integration with SpotTrade objects
- [x] 5.4 Update package exports if needed
