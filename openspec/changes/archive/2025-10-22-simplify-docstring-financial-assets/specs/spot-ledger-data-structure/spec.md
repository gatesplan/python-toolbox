# Spec Delta: spot-ledger-data-structure

## MODIFIED Requirements

### Requirement: SpotLedger and SpotLedgerEntry docstrings MUST be minimal Korean

SpotLedger class and SpotLedgerEntry dataclass docstrings SHALL use simplified Korean style:
- Class docstrings MUST be 2-3 Korean lines describing ledger responsibilities
- Method docstrings MUST be single Korean line
- Attributes/Args/Returns/Examples sections MUST NOT be present
- Type hints and dataclass fields SHALL remain unchanged

#### Scenario: SpotLedger class docstring is concise Korean
**Given** the `SpotLedger` class definition
**When** an agent reads the class docstring
**Then** the docstring is 2-3 Korean lines: "단일 거래쌍의 현물 거래 내역 장부. 거래를 시간순으로 기록하고 누적 자산, 평균 진입가, 실현 손익을 계산합니다."
**And** no Attributes section is present
**And** no Examples section is present

#### Scenario: SpotLedgerEntry dataclass docstring is concise Korean
**Given** the `SpotLedgerEntry` dataclass definition
**When** an agent reads the class docstring
**Then** the docstring is 1-2 Korean lines describing entry data
**And** no Attributes section is present

#### Scenario: SpotLedger method docstrings are single-line Korean
**Given** `add_trade` method in `SpotLedger`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "거래 추가 및 장부 업데이트."
**And** no Args/Returns sections are present

**Given** `to_dataframe` method in `SpotLedger`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "장부를 DataFrame으로 변환."

**Given** `get_last_entry` method in `SpotLedger`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "마지막 거래 엔트리 반환."

#### Scenario: All tests pass after docstring changes
**Given** simplified Korean docstrings in SpotLedger and SpotLedgerEntry
**When** running `pytest tests/test_spot_ledger.py`
**Then** all tests pass
**And** no functional behavior has changed

## Related Changes
- `wallet-data-structure`: Similar docstring simplification
- `simplify-docstring-style`: Financial-simulation pattern reference
