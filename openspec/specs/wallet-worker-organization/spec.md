# wallet-worker-organization Specification

## Purpose
TBD - created by archiving change refactor-wallet-workers. Update Purpose after archive.
## Requirements
### Requirement: Worker Module Structure
The wallet workers MUST be organized in a `workers/` subdirectory with one class per file.

#### Scenario: Worker files organization
```python
# Directory structure should be:
# financial_assets/wallet/
#   workers/
#     __init__.py
#     wallet_worker.py        # WalletWorker abstract base class
#     total_value_worker.py   # TotalValueWorker
#     realized_pnl_worker.py  # RealizedPnLWorker
#     unrealized_pnl_worker.py # UnrealizedPnLWorker
#     position_summary_worker.py # PositionSummaryWorker
#     currency_summary_worker.py # CurrencySummaryWorker

# Import from workers module
from financial_assets.wallet.workers import (
    WalletWorker,
    TotalValueWorker,
    RealizedPnLWorker,
    UnrealizedPnLWorker,
    PositionSummaryWorker,
    CurrencySummaryWorker
)

# All imports work as expected
assert WalletWorker is not None
assert TotalValueWorker is not None
```

#### Scenario: Backward compatibility preserved
```python
# Old import path still works (re-exported from wallet/__init__.py)
from financial_assets.wallet import WalletWorker

# Worker can be imported
assert WalletWorker is not None
```

### Requirement: Worker Base Class Location
The `WalletWorker` abstract base class MUST be in `workers/wallet_worker.py`.

#### Scenario: Base class import
```python
from financial_assets.wallet.workers.wallet_worker import WalletWorker
from abc import ABC

# WalletWorker is abstract
assert issubclass(WalletWorker, ABC)
assert hasattr(WalletWorker, 'analyze')
```

### Requirement: Individual Worker Files
Each concrete worker implementation MUST be in its own file named after the class in snake_case.

#### Scenario: TotalValueWorker in separate file
```python
# workers/total_value_worker.py contains only TotalValueWorker
from financial_assets.wallet.workers.total_value_worker import TotalValueWorker
from financial_assets.wallet.workers.wallet_worker import WalletWorker

assert issubclass(TotalValueWorker, WalletWorker)
```

#### Scenario: RealizedPnLWorker in separate file
```python
from financial_assets.wallet.workers.realized_pnl_worker import RealizedPnLWorker
from financial_assets.wallet.workers.wallet_worker import WalletWorker

assert issubclass(RealizedPnLWorker, WalletWorker)
```

#### Scenario: UnrealizedPnLWorker in separate file
```python
from financial_assets.wallet.workers.unrealized_pnl_worker import UnrealizedPnLWorker
from financial_assets.wallet.workers.wallet_worker import WalletWorker

assert issubclass(UnrealizedPnLWorker, WalletWorker)
```

#### Scenario: PositionSummaryWorker in separate file
```python
from financial_assets.wallet.workers.position_summary_worker import PositionSummaryWorker
from financial_assets.wallet.workers.wallet_worker import WalletWorker

assert issubclass(PositionSummaryWorker, WalletWorker)
```

#### Scenario: CurrencySummaryWorker in separate file
```python
from financial_assets.wallet.workers.currency_summary_worker import CurrencySummaryWorker
from financial_assets.wallet.workers.wallet_worker import WalletWorker

assert issubclass(CurrencySummaryWorker, WalletWorker)
```

### Requirement: Workers Package Exports
The `workers/__init__.py` MUST export all worker classes for convenient importing.

#### Scenario: Import all workers from package
```python
from financial_assets.wallet.workers import (
    WalletWorker,
    TotalValueWorker,
    RealizedPnLWorker,
    UnrealizedPnLWorker,
    PositionSummaryWorker,
    CurrencySummaryWorker
)

# All workers are available
workers = [
    WalletWorker,
    TotalValueWorker,
    RealizedPnLWorker,
    UnrealizedPnLWorker,
    PositionSummaryWorker,
    CurrencySummaryWorker
]
assert all(w is not None for w in workers)
```

