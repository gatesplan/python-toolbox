# Spec Delta: order-data-structure

## MODIFIED Requirements

### Requirement: SpotOrder docstrings MUST be minimal Korean

SpotOrder class and method docstrings SHALL use simplified Korean style:
- Class docstring MUST be 2-3 Korean lines describing responsibility
- Method docstrings MUST be single Korean line describing purpose only
- Attributes/Args/Returns/Examples/Raises sections MUST NOT be present
- Type hints SHALL remain unchanged

#### Scenario: SpotOrder class docstring is concise Korean
**Given** the `SpotOrder` class definition
**When** an agent reads the class docstring
**Then** the docstring is 2-3 Korean lines: "현물 거래 주문 (불변 복제 패턴). 주문 정보, 체결 상태, 수수료, 최소 거래 제약을 캡슐화합니다."
**And** no Attributes section is present

#### Scenario: SpotOrder method docstrings are single-line Korean
**Given** `fill_by_asset_amount` method in `SpotOrder`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "자산 수량만큼 주문 체결."
**And** no Args/Returns/Raises sections are present

**Given** `remaining_asset` method in `SpotOrder`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "미체결 자산 수량 반환."

**Given** `is_filled` method in `SpotOrder`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "주문 완전 체결 여부."

#### Scenario: All tests pass after docstring changes
**Given** simplified Korean docstrings in SpotOrder
**When** running `pytest tests/test_order.py`
**Then** all tests pass
**And** no functional behavior has changed

## Related Changes
- `trade-data-structure`: Similar docstring simplification
- `simplify-docstring-style`: Financial-simulation pattern reference
