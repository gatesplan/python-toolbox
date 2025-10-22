# Tasks: refactor-wallet-workers

## Implementation Tasks

### 1. Create workers directory structure
- [x] Create `packages/financial-assets/financial_assets/wallet/workers/` directory
- [x] Create empty `workers/__init__.py`
- **Validation**: Directory and init file exist ✓

### 2. Extract WalletWorker base class
- [x] Create `workers/wallet_worker.py`
- [x] Move `WalletWorker` abstract class from `worker.py` to `workers/wallet_worker.py`
- [x] Preserve all docstrings and type hints
- **Validation**: File exists and contains WalletWorker class with `analyze` abstract method ✓

### 3. Extract TotalValueWorker
- [x] Create `workers/total_value_worker.py`
- [x] Move `TotalValueWorker` class from `worker.py` to new file
- [x] Import `WalletWorker` from `workers.wallet_worker`
- [x] Import required dependencies (`SpotWallet`, `Price`, etc.)
- **Validation**: File exists, class works independently ✓

### 4. Extract RealizedPnLWorker
- [x] Create `workers/realized_pnl_worker.py`
- [x] Move `RealizedPnLWorker` class from `worker.py` to new file
- [x] Import `WalletWorker` from `workers.wallet_worker`
- [x] Import required dependencies
- **Validation**: File exists, class works independently ✓

### 5. Extract UnrealizedPnLWorker
- [x] Create `workers/unrealized_pnl_worker.py`
- [x] Move `UnrealizedPnLWorker` class from `worker.py` to new file
- [x] Import `WalletWorker` from `workers.wallet_worker`
- [x] Import required dependencies
- **Validation**: File exists, class works independently ✓

### 6. Extract PositionSummaryWorker
- [x] Create `workers/position_summary_worker.py`
- [x] Move `PositionSummaryWorker` class from `worker.py` to new file
- [x] Import `WalletWorker` from `workers.wallet_worker`
- [x] Import required dependencies (including `pandas`)
- **Validation**: File exists, class works independently ✓

### 7. Extract CurrencySummaryWorker
- [x] Create `workers/currency_summary_worker.py`
- [x] Move `CurrencySummaryWorker` class from `worker.py` to new file
- [x] Import `WalletWorker` from `workers.wallet_worker`
- [x] Import required dependencies (including `pandas`)
- **Validation**: File exists, class works independently ✓

### 8. Configure workers package exports
- [x] Update `workers/__init__.py` to import and export all worker classes:
  - `WalletWorker`
  - `TotalValueWorker`
  - `RealizedPnLWorker`
  - `UnrealizedPnLWorker`
  - `PositionSummaryWorker`
  - `CurrencySummaryWorker`
- [x] Define `__all__` list with all exported names
- **Validation**: Can import all workers from `financial_assets.wallet.workers` ✓

### 9. Update wallet package imports
- [x] Update `packages/financial-assets/financial_assets/wallet/__init__.py`
- [x] Change import from `from .worker import WalletWorker` to `from .workers import WalletWorker`
- [x] Ensure backward compatibility - `WalletWorker` still accessible from `financial_assets.wallet`
- **Validation**: Import `from financial_assets.wallet import WalletWorker` still works ✓

### 10. Update WalletInspector imports
- [x] Update `wallet_inspector.py` to import workers from new location
- [x] Change imports from `from .worker import ...` to `from .workers import ...`
- **Validation**: WalletInspector instantiates and uses workers correctly ✓

### 11. Remove old worker.py file
- [x] Delete `packages/financial-assets/financial_assets/wallet/worker.py`
- **Validation**: File no longer exists ✓

### 12. Run existing tests
- [x] Run all wallet-related tests to ensure nothing broke
- [x] Fix any import issues if discovered
- **Validation**: All tests pass ✓ (32 passed)

### 13. Clean up __pycache__
- [x] Remove `__pycache__/worker.cpython-*.pyc` files
- **Validation**: Old cache files removed ✓

## Parallelizable Work
- Tasks 3-7 (extracting individual workers) can be done in parallel after task 2 is complete
- Task 9 and 10 (updating imports) can be done in parallel after task 8 is complete

## Dependencies
- Tasks 3-7 depend on task 2 (base class must exist first)
- Task 8 depends on tasks 2-7 (all files must exist before package export)
- Tasks 9-10 depend on task 8 (package exports must be configured)
- Task 11 depends on tasks 9-10 (ensure new imports work before removing old file)
- Task 12 depends on task 11 (all code changes complete)
