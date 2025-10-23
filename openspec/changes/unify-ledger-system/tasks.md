# Implementation Tasks

## 1. Core Data Structures
- [ ] 1.1 Create `EventType` enum with DEPOSIT, WITHDRAW, BUY, SELL, FEE
- [ ] 1.2 Create `LedgerEntry` dataclass with timestamp, account, event, asset_change, value_change, asset, value
- [ ] 1.3 Add unit tests for `LedgerEntry` immutability

## 2. Ledger Class
- [ ] 2.1 Implement `Ledger` class with account-based initialization
- [ ] 2.2 Implement `add_currency_deposit(timestamp, amount)` method
- [ ] 2.3 Implement `add_currency_withdraw(timestamp, amount)` method
- [ ] 2.4 Implement `add_asset_deposit(timestamp, amount)` method
- [ ] 2.5 Implement `add_asset_withdraw(timestamp, amount)` method
- [ ] 2.6 Implement `add_trade(trade: SpotTrade)` method (BUY/SELL event)
- [ ] 2.7 Implement `add_fee(timestamp, amount)` method
- [ ] 2.8 Implement `to_dataframe()` for analysis
- [ ] 2.9 Add cumulative tracking logic (_cumulative_asset, _cumulative_value)
- [ ] 2.10 Add unit tests for all ledger operations

## 3. SpotWallet Integration
- [ ] 3.1 Add `_ledgers: dict[str, Ledger]` to SpotWallet (account-based)
- [ ] 3.2 Integrate ledger recording in `deposit_currency()`
- [ ] 3.3 Integrate ledger recording in `withdraw_currency()`
- [ ] 3.4 Integrate ledger recording in `process_trade()` for BUY/SELL
- [ ] 3.5 Integrate fee recording in `process_trade()` when trade.fee exists
- [ ] 3.6 Update `get_ledger()` to return new Ledger type
- [ ] 3.7 Add integration tests for wallet + ledger operations

## 4. Migration and Cleanup
- [ ] 4.1 Deprecate or refactor old SpotLedger (keep for backward compatibility if needed)
- [ ] 4.2 Update wallet tests to use new ledger API
- [ ] 4.3 Update documentation and docstrings
- [ ] 4.4 Run full test suite and verify all tests pass

## 5. Validation
- [ ] 5.1 Verify ledger records all wallet operations (deposit, withdraw, trade, fee)
- [ ] 5.2 Verify cumulative tracking accuracy
- [ ] 5.3 Verify DataFrame conversion works correctly
- [ ] 5.4 Performance test with large transaction volumes
