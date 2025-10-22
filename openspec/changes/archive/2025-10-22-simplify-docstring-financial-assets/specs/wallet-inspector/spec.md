# Spec Delta: wallet-inspector

## MODIFIED Requirements

### Requirement: WalletInspector docstrings MUST be minimal Korean

WalletInspector class and all method docstrings SHALL use simplified Korean style:
- Class docstring MUST be 2 Korean lines describing inspector responsibilities
- Method docstrings MUST be single Korean line
- Args/Returns sections MUST NOT be present
- Type hints SHALL remain unchanged

#### Scenario: WalletInspector class docstring is concise Korean
**Given** the `WalletInspector` class definition
**When** an agent reads the class docstring
**Then** the docstring is 2 Korean lines: "지갑 상태 분석 도구. 총 자산 가치, 실현/미실현 손익, 포지션 요약을 제공합니다."
**And** no method list is present

#### Scenario: WalletInspector method docstrings are single-line Korean
**Given** `get_total_value` method in `WalletInspector`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "총 자산 가치 계산."
**And** no Args/Returns sections are present

**Given** `get_realized_pnl` method in `WalletInspector`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "실현 손익 계산."

**Given** `get_unrealized_pnl` method in `WalletInspector`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "미실현 손익 계산."

#### Scenario: All tests pass after docstring changes
**Given** simplified Korean docstrings in WalletInspector
**When** running `pytest tests/test_wallet_inspector.py`
**Then** all tests pass
**And** no functional behavior has changed

## Related Changes
- `wallet-data-structure`: Similar docstring simplification
- `simplify-docstring-style`: Financial-simulation pattern reference
