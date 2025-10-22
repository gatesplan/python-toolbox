# Spec Delta: trade-data-structure

## MODIFIED Requirements

### Requirement: SpotTrade and SpotSide docstrings MUST be minimal Korean

SpotTrade dataclass and SpotSide enum docstrings SHALL use simplified Korean style:
- SpotTrade class docstring MUST be 2 Korean lines describing immutable trade data
- SpotSide enum docstring MUST be 1 Korean line
- Method docstrings MUST be single Korean line
- Attributes/Args/Returns/Examples sections MUST NOT be present
- Type hints and dataclass fields SHALL remain unchanged

#### Scenario: SpotTrade dataclass docstring is concise Korean
**Given** the `SpotTrade` dataclass definition
**When** an agent reads the class docstring
**Then** the docstring is 2 Korean lines: "체결 완료된 현물 거래 (불변 데이터 구조). 거래 시뮬레이션이나 실제 거래소 API의 체결 정보를 표준화합니다."
**And** no Attributes section is present

#### Scenario: SpotSide enum docstring is single-line Korean
**Given** the `SpotSide` enum definition
**When** an agent reads the enum docstring
**Then** the docstring is 1 Korean line: "현물 거래 방향 (BUY, SELL)."

#### Scenario: SpotTrade __str__ and __repr__ docstrings are single-line Korean
**Given** `__str__` method in `SpotTrade`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "거래 정보의 읽기 쉬운 문자열 표현."

**Given** `__repr__` method in `SpotTrade`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "재생성 가능한 상세 문자열 표현."

#### Scenario: All tests pass after docstring changes
**Given** simplified Korean docstrings in SpotTrade and SpotSide
**When** running `pytest tests/test_trade.py`
**Then** all tests pass
**And** no functional behavior has changed

## Related Changes
- `order-data-structure`: Similar docstring simplification
- `simplify-docstring-style`: Financial-simulation pattern reference
