# Spec Delta: calculation-tool

## MODIFIED Requirements

### Requirement: CalculationTool docstrings MUST be minimal and in Korean

CalculationTool class and method docstrings SHALL use simplified Korean style:
- Class docstring MUST be 1-2 lines in Korean describing responsibility
- Method docstrings MUST be single Korean line describing intent
- Args/Returns/Example sections MUST NOT be present
- Type hints SHALL remain unchanged

#### Scenario: CalculationTool class docstring is concise Korean
**Given** the `CalculationTool` class definition
**When** an agent reads the class docstring
**Then** the docstring is 1 Korean line: "시뮬레이션 수치 계산 도구 (stateless 순수 함수)."
**And** no additional explanation or method list is present

#### Scenario: Method docstrings are single-line Korean
**Given** `round_to_min_amount` method in `CalculationTool`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "금액을 최소 거래 단위의 배수로 내림."
**And** no Args, Returns, or Example sections are present

**Given** `get_price_sample` method in `CalculationTool`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "정규분포 기반 가격 샘플링 (범위 클리핑 적용)."

**Given** `get_separated_amount_sequence` method in `CalculationTool`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "금액을 랜덤하게 여러 조각으로 분할."

**Given** `get_price_range` method in `CalculationTool`
**When** an agent reads the method docstring
**Then** the docstring is 1 Korean line: "target_price가 캔들의 어느 범위에 위치하는지 판단."

#### Scenario: Type hints remain unchanged
**Given** all methods in `CalculationTool`
**When** reviewing method signatures
**Then** all type hints are preserved (e.g., `amount: float`, `-> float`)

## Related Changes
- `tradesim-integration`: Similar docstring simplification
