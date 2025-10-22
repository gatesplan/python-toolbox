# Spec Delta: wallet-data-structure

## MODIFIED Requirements

### Requirement: SpotWallet docstrings MUST be minimal Korean

SpotWallet class and all method docstrings SHALL use simplified Korean style:
- Class docstring MUST be 2-3 Korean lines describing wallet responsibilities
- Method docstrings MUST be single Korean line describing purpose only
- Attributes/Args/Returns/Examples/Raises sections MUST NOT be present
- Type hints SHALL remain unchanged

#### Scenario: SpotWallet class docstring is concise Korean
**Given** the `SpotWallet` class definition
**When** an agent reads the class docstring
**Then** the docstring is 2-3 Korean lines: "현물 거래 지갑. 화폐 계정, 자산 포지션, 거래 내역을 관리하고 BUY/SELL 거래를 처리합니다."
**And** no Attributes section is present
**And** no Examples section is present

#### Scenario: SpotWallet method docstrings are single-line Korean
**Given** `deposit_currency` method in `SpotWallet`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "화폐 입금."
**And** no Args/Examples sections are present

**Given** `withdraw_currency` method in `SpotWallet`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "화폐 출금."

**Given** `process_trade` method in `SpotWallet`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "거래 처리 및 장부 기록."

**Given** `get_currency_balance` method in `SpotWallet`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "화폐 잔액 조회."

#### Scenario: All tests pass after docstring changes
**Given** simplified Korean docstrings in SpotWallet
**When** running `pytest tests/test_spot_wallet.py`
**Then** all tests pass
**And** no functional behavior has changed

## Related Changes
- `spot-ledger-data-structure`: Similar docstring simplification
- `wallet-inspector`: Similar docstring simplification
- `simplify-docstring-style`: Financial-simulation pattern reference
